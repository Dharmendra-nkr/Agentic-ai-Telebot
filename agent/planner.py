"""
Agent Planner - Analyzes user messages and creates execution plans.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dateparser import parse as dateparse

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from config import settings
from utils.logger import get_logger
from utils.nlp import extract_intent, extract_event_info
from agent.prompts import (
    get_intent_classification_prompt,
    get_entity_extraction_prompt,
    get_planning_prompt
)

logger = get_logger(__name__)


class Plan:
    """Represents an execution plan."""
    
    def __init__(self, steps: List[Dict[str, Any]], requires_clarification: bool = False, 
                 clarifying_questions: Optional[List[str]] = None):
        self.steps = steps
        self.requires_clarification = requires_clarification
        self.clarifying_questions = clarifying_questions or []
    
    def __repr__(self):
        return f"<Plan(steps={len(self.steps)}, needs_clarification={self.requires_clarification})>"


class AgentPlanner:
    """
    Plans actions based on user intent and available information.
    Uses LLM for intent classification, entity extraction, and action planning.
    """
    
    def __init__(self):
        """Initialize the planner with LLM client."""
        if settings.llm_provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
        elif settings.llm_provider == "anthropic":
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
        elif settings.llm_provider == "groq":
            # Groq uses OpenAI-compatible API
            self.client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url
            )
            self.model = settings.groq_model
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        
        self.provider = settings.llm_provider
        logger.info("agent_planner_initialized", provider=self.provider, model=self.model)
    
    async def analyze_message(self, message: str, conversation_context: List[Dict] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze user message to extract intent and entities.
        
        Args:
            message: User message
            conversation_context: Recent conversation history
            
        Returns:
            Tuple of (intent, entities)
        """
        # First, try rule-based intent extraction
        intent = extract_intent(message)
        logger.info("extracted_intent", intent=intent, message=message[:100])
        
        # Extract basic entities using NLP
        nlp_entities = extract_event_info(message)
        
        # Handle relative time expressions more robustly
        # If we have a duration, check if we should use it for relative time calculation
        import re
        from datetime import datetime as dt_now
        
        if nlp_entities.get('duration'):
            # Check for explicit relative time patterns
            relative_patterns = [
                r'\bin\s+(\d+)\s+(minute|min|hour|hr|day)s?',  # "in 2 minutes"
                r'(\d+)\s+(minute|min|hour|hr|day)s?\s+from\s+now',  # "2 minutes from now"
                r'after\s+(\d+)\s+(minute|min|hour|hr|day)s?',  # "after 2 minutes"
            ]
            
            is_relative = False
            for pattern in relative_patterns:
                if re.search(pattern, message.lower()):
                    is_relative = True
                    break
            
            # Also treat as relative if datetime is missing or in the past
            current_datetime = nlp_entities.get('datetime')
            if current_datetime:
                # Check if the datetime is in the past or suspiciously wrong
                now = dt_now.now()
                if current_datetime < now:
                    is_relative = True
                    logger.info("datetime_in_past_using_relative", 
                               parsed_datetime=current_datetime.isoformat(),
                               current_time=now.isoformat())
            else:
                # No datetime extracted, but we have duration - use relative
                is_relative = True
            
            if is_relative:
                # Calculate the actual reminder time
                current_time = dt_now.now()
                reminder_time = current_time + nlp_entities['duration']
                nlp_entities['datetime'] = reminder_time
                logger.info("calculated_relative_reminder_time", 
                           current_time=current_time.isoformat(),
                           duration=str(nlp_entities['duration']),
                           reminder_time=reminder_time.isoformat(),
                           reason="duration_detected")
        
        # Use nlp_entities as the initial set of entities
        entities = nlp_entities
        logger.info("extracted_entities", entities=entities)
        
        # Enhance with LLM if needed
        if settings.enable_clarifying_questions:
            # Use LLM for more sophisticated entity extraction
            llm_entities = await self._llm_extract_entities(message, intent)
            # Merge entities (but preserve our calculated datetime for relative expressions)
            for k, v in llm_entities.items():
                # Don't override datetime if we calculated it from duration
                if k == 'datetime' and nlp_entities.get('duration'):
                    continue  # Keep our calculated datetime
                if v is not None:
                    entities[k] = v
        
        return intent, entities
    
    async def _llm_extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Use LLM to extract entities from message."""
        try:
            prompt = get_entity_extraction_prompt(message, intent)
            
            if self.provider in ["openai", "groq"]:  # Groq uses OpenAI-compatible API
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                content = response.choices[0].message.content
            else:  # anthropic
                response = await self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                content = response.content[0].text
            
            # Parse JSON response
            entities = json.loads(content)
            
            # Handle relative time expressions (e.g., "in 2 minutes", "in 1 hour")
            # Check if there's a duration but no valid datetime
            if "duration" in entities and entities["duration"]:
                # Check if the original text contains "in X minutes/hours"
                import re
                relative_time_pattern = r'\bin\s+(\d+)\s+(minute|min|hour|hr|day)s?'
                match = re.search(relative_time_pattern, message.lower())
                
                if match:
                    # This is a relative time expression
                    from datetime import datetime, timedelta
                    from dateparser import parse as dateparse_lib
                    
                    # Extract the duration
                    amount = int(match.group(1))
                    unit = match.group(2)
                    
                    # Convert to timedelta
                    if unit in ['minute', 'min']:
                        delta = timedelta(minutes=amount)
                    elif unit in ['hour', 'hr']:
                        delta = timedelta(hours=amount)
                    elif unit == 'day':
                        delta = timedelta(days=amount)
                    else:
                        delta = timedelta(minutes=amount)  # default
                    
                    # Calculate the actual reminder time
                    reminder_time = datetime.now() + delta
                    entities["datetime"] = reminder_time
                    logger.info("calculated_relative_time", original=message, reminder_time=reminder_time)
            
            # Parse datetime if present and not already set
            if "datetime" in entities and isinstance(entities["datetime"], str):
                datetime_str = entities["datetime"]
                # Use dateparser to convert string to datetime
                parsed_dt = dateparse(datetime_str, settings={'PREFER_DATES_FROM': 'future'})
                if parsed_dt:
                    entities["datetime"] = parsed_dt
                    logger.info("parsed_datetime", original=datetime_str, parsed=parsed_dt)
                else:
                    logger.warning("datetime_parse_failed", input=datetime_str)
                    # Remove invalid datetime
                    del entities["datetime"]
            
            logger.info("llm_entity_extraction", entities=entities)
            return entities
            
        except Exception as e:
            logger.error("llm_entity_extraction_failed", error=str(e))
            return {}
    
    async def create_plan(self, intent: str, entities: Dict[str, Any], 
                         conversation_context: List[Dict] = None) -> Plan:
        """
        Create an execution plan based on intent and entities.
        
        Args:
            intent: User intent
            entities: Extracted entities
            conversation_context: Recent conversation history
            
        Returns:
            Plan object with steps and clarification needs
        """
        conversation_context = conversation_context or []
        
        # Check for missing required information
        missing_info = self._check_missing_info(intent, entities)
        
        if missing_info and settings.enable_clarifying_questions:
            # Generate clarifying questions
            questions = self._generate_clarifying_questions(intent, missing_info)
            return Plan(
                steps=[],
                requires_clarification=True,
                clarifying_questions=questions
            )
        
        # Create execution steps
        steps = self._create_execution_steps(intent, entities)
        
        return Plan(steps=steps, requires_clarification=False)
    
    def _check_missing_info(self, intent: str, entities: Dict[str, Any]) -> List[str]:
        """Check what information is missing for the given intent."""
        missing = []
        
        if intent == "create_event":
            if not entities.get("title"):
                missing.append("title")
            if not entities.get("datetime"):
                missing.append("datetime")
        
        elif intent == "create_reminder":
            if not entities.get("title"):
                missing.append("title")
            if not entities.get("datetime"):
                missing.append("datetime")
        
        elif intent == "create_task":
            if not entities.get("title"):
                missing.append("title")
        
        elif intent == "create_note":
            if not entities.get("title") and not entities.get("description"):
                missing.append("content")
        
        return missing
    
    def _generate_clarifying_questions(self, intent: str, missing_info: List[str]) -> List[str]:
        """Generate clarifying questions for missing information."""
        questions = []
        
        question_map = {
            "title": "What would you like to call this?",
            "datetime": "When should this be?",
            "duration": "How long will it last?",
            "location": "Where will this take place?",
            "reminder_before": "How long before should I remind you?",
            "content": "What would you like to save?"
        }
        
        for info in missing_info:
            if info in question_map:
                questions.append(question_map[info])
        
        return questions
    
    def _create_execution_steps(self, intent: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create execution steps based on intent and entities."""
        steps = []
        
        if intent == "create_event":
            # Step 1: Create calendar event
            steps.append({
                "step": 1,
                "action": "create_event",
                "tool": "CalendarMCP",
                "parameters": {
                    "action": "create_event",
                    "title": entities.get("title"),
                    "start_time": entities.get("datetime"),
                    "description": entities.get("description"),
                    "location": entities.get("location")
                }
            })
            
            # Step 2: Create reminder if requested
            if entities.get("reminder_before"):
                reminder_time = entities.get("datetime")
                # Calculate reminder time (would need proper datetime handling)
                steps.append({
                    "step": 2,
                    "action": "create_reminder",
                    "tool": "ReminderMCP",
                    "parameters": {
                        "action": "create",
                        "title": f"Reminder: {entities.get('title')}",
                        "remind_at": reminder_time  # Should subtract reminder_before
                    }
                })
        
        elif intent == "create_reminder":
            steps.append({
                "step": 1,
                "action": "create_reminder",
                "tool": "ReminderMCP",
                "parameters": {
                    "action": "create",
                    "title": entities.get("title"),
                    "remind_at": entities.get("datetime"),
                    "description": entities.get("description")
                }
            })
        
        elif intent == "query_events":
            steps.append({
                "step": 1,
                "action": "list_events",
                "tool": "CalendarMCP",
                "parameters": {
                    "action": "list_events"
                }
            })
        
        elif intent == "file_upload":
            steps.append({
                "step": 1,
                "action": "upload",
                "tool": "FileStorageMCP",
                "parameters": {
                    "action": "upload",
                    "file_path": entities.get("file_path"),
                    "file_name": entities.get("file_name") or entities.get("title")
                }
            })
        
        elif intent == "file_list":
            steps.append({
                "step": 1,
                "action": "list",
                "tool": "FileStorageMCP",
                "parameters": {
                    "action": "list"
                }
            })
        
        elif intent == "file_link":
            # Extract file name from entities or parse from raw text
            file_name = entities.get("title") or entities.get("file_name")
            if not file_name:
                import re
                raw = entities.get("raw_text", "")
                match = re.search(r'(?:link\s+(?:for|of)\s+)(.+)', raw, re.IGNORECASE)
                if match:
                    file_name = match.group(1).strip()
            
            steps.append({
                "step": 1,
                "action": "get_link",
                "tool": "FileStorageMCP",
                "parameters": {
                    "action": "get_link",
                    "file_id": entities.get("file_id"),
                    "file_name": file_name
                }
            })
        
        elif intent == "file_share":
            steps.append({
                "step": 1,
                "action": "share",
                "tool": "FileStorageMCP",
                "parameters": {
                    "action": "share",
                    "file_id": entities.get("file_id"),
                    "share_with": entities.get("share_with"),
                    "access_level": entities.get("access_level", "viewer")
                }
            })
        
        elif intent == "query_reminders":
            steps.append({
                "step": 1,
                "action": "list_reminders",
                "tool": "ReminderMCP",
                "parameters": {
                    "action": "list"
                }
            })
        
        elif intent == "browser_navigation":
            # Extract URL from message
            import re
            raw_text = entities.get("raw_text", "")
            url = None
            
            # Try to find URLs in the text
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, raw_text)
            if url_match:
                url = url_match.group(0)
            else:
                # Try to extract domain names (e.g., "google.com", "example.org")
                domain_pattern = r'(?:https?://)?([a-z0-9]+(?:[.-][a-z0-9]+)*(?:\.[a-z]{2,}))'
                domain_match = re.search(domain_pattern, raw_text, re.IGNORECASE)
                if domain_match:
                    domain = domain_match.group(1)
                    # Add protocol if missing
                    if not domain.startswith('http'):
                        url = f"https://{domain}"
                    else:
                        url = domain
            
            # Step 1: Create browser session
            steps.append({
                "step": 1,
                "action": "create_session",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "create_session"
                }
            })
            
            # Step 2: Navigate if URL found
            step_num = 2
            if url:
                steps.append({
                    "step": step_num,
                    "action": "navigate",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "navigate",
                        "session_id": "${session_id}",  # Reference from previous step
                        "url": url
                    }
                })
                step_num += 1
            
            # Check if the message also contains screenshot keywords
            screenshot_keywords = ['screenshot', 'capture', 'snap', 'take a picture', 'snap a photo']
            if any(keyword in raw_text.lower() for keyword in screenshot_keywords):
                steps.append({
                    "step": step_num,
                    "action": "screenshot",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "screenshot",
                        "session_id": "${session_id}"
                    }
                })
                logger.info("added_screenshot_step", message=raw_text)
        
        elif intent == "browser_screenshot":
            steps.append({
                "step": 1,
                "action": "create_session",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "create_session"
                }
            })
            
            # Extract URL if present
            import re
            raw_text = entities.get("raw_text", "")
            url_match = re.search(r'https?://[^\s]+', raw_text)
            
            if url_match:
                url = url_match.group(0)
                steps.append({
                    "step": 2,
                    "action": "navigate",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "navigate",
                        "session_id": "${session_id}",
                        "url": url
                    }
                })
                
                steps.append({
                    "step": 3,
                    "action": "screenshot",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "screenshot",
                        "session_id": "${session_id}"
                    }
                })
            else:
                # Just take screenshot of current page
                steps.append({
                    "step": 2,
                    "action": "screenshot",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "screenshot",
                        "session_id": "${session_id}"
                    }
                })
        
        elif intent == "browser_extract":
            steps.append({
                "step": 1,
                "action": "create_session",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "create_session"
                }
            })
            
            # Extract URL if present
            import re
            raw_text = entities.get("raw_text", "")
            url = None
            
            # Try to find full URLs first
            url_match = re.search(r'https?://[^\s]+', raw_text)
            if url_match:
                url = url_match.group(0)
            else:
                # Try to extract domain names (e.g., "google.com", "example.org")
                domain_pattern = r'(?:https?://)?([a-z0-9]+(?:[.-][a-z0-9]+)*(?:\.[a-z]{2,}))'
                domain_match = re.search(domain_pattern, raw_text, re.IGNORECASE)
                if domain_match:
                    domain = domain_match.group(1)
                    # Add protocol if missing
                    if not domain.startswith('http'):
                        url = f"https://{domain}"
                    else:
                        url = domain
            
            if url:
                steps.append({
                    "step": 2,
                    "action": "navigate",
                    "tool": "BrowserbaseMCP",
                    "parameters": {
                        "action": "navigate",
                        "session_id": "${session_id}",
                        "url": url
                    }
                })
            
            steps.append({
                "step": 3 if url else 2,
                "action": "extract",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "extract",
                    "session_id": "${session_id}",
                    "instruction": raw_text,
                    "data_format": "json"
                }
            })
        
        elif intent == "browser_interaction":
            steps.append({
                "step": 1,
                "action": "create_session",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "create_session"
                }
            })
            
            # Extract action type and details from message
            raw_text = entities.get("raw_text", "").lower()
            action_type = "click"
            
            if "type" in raw_text or "enter" in raw_text:
                action_type = "type"
            elif "scroll" in raw_text:
                action_type = "scroll"
            elif "click" in raw_text or "submit" in raw_text:
                action_type = "click"
            
            steps.append({
                "step": 2,
                "action": "act",
                "tool": "BrowserbaseMCP",
                "parameters": {
                    "action": "act",
                    "session_id": "${session_id}",
                    "action_type": action_type,
                    "instruction": entities.get("raw_text", "")
                }
            })
        
        return steps
    
    async def refine_plan_with_llm(self, plan: Plan, conversation_context: List[Dict]) -> Plan:
        """
        Use LLM to refine and validate the plan.
        
        Args:
            plan: Initial plan
            conversation_context: Conversation history
            
        Returns:
            Refined plan
        """
        # This is an advanced feature for future enhancement
        # For now, return the plan as-is
        return plan

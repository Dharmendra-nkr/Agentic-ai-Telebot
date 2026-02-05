"""
Agent orchestrator - the main brain of the agentic AI system.
Coordinates planning, execution, and memory management.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from config import settings
from memory.short_term import get_user_memory
from memory.long_term import LongTermMemory
from memory.temporal import TemporalMemory
from agent.planner import AgentPlanner, Plan
from agent.executor import AgentExecutor, ExecutionResult
from agent.prompts import get_system_prompt
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """
    Main orchestrator for the agentic AI system.
    Coordinates between planning, execution, and memory systems.
    """
    
    def __init__(self, db: AsyncSession, scheduler=None):
        """
        Initialize the orchestrator.
        
        Args:
            db: Database session
            scheduler: Optional scheduler for reminder notifications
        """
        self.db = db
        self.planner = AgentPlanner()
        self.executor = AgentExecutor(db, scheduler=scheduler)
        self.long_term_memory = LongTermMemory(db)
        self.temporal_memory = TemporalMemory(db)
        
        # Initialize LLM client
        if settings.llm_provider == "openai":
            self.llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
        elif settings.llm_provider == "anthropic":
            self.llm_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.anthropic_model
        elif settings.llm_provider == "groq":
            # Groq uses OpenAI-compatible API
            self.llm_client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=settings.groq_base_url
            )
            self.model = settings.groq_model
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        
        self.provider = settings.llm_provider
        logger.info("agent_orchestrator_initialized", provider=self.provider)
    
    async def process_message(self, user_id: int, telegram_id: int, message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            user_id: Database user ID
            telegram_id: Telegram user ID
            message: User message
            
        Returns:
            Response message
        """
        logger.info("processing_message", user_id=user_id, message=message[:100])
        
        # Get or create user
        user = await self.long_term_memory.get_or_create_user(telegram_id)
        
        # Get short-term memory for context
        stm = get_user_memory(telegram_id)
        stm.add_message("user", message)
        
        # Save to long-term memory
        await self.long_term_memory.save_conversation(
            user_id=user.id,
            role="user",
            content=message
        )
        
        try:
            # Step 1: Analyze message (intent + entities)
            intent, entities = await self.planner.analyze_message(
                message,
                conversation_context=stm.get_context_for_llm()
            )
            
            # Step 2: Create execution plan
            plan = await self.planner.create_plan(
                intent,
                entities,
                conversation_context=stm.get_context_for_llm()
            )
            
            # Step 3: Handle clarification if needed
            if plan.requires_clarification:
                response = self._format_clarifying_questions(plan.clarifying_questions)
                stm.add_message("assistant", response)
                await self.long_term_memory.save_conversation(
                    user_id=user.id,
                    role="assistant",
                    content=response,
                    intent=intent
                )
                return response
            
            # Step 4: Execute plan
            result = await self.executor.execute_plan(plan, user.id)
            
            # Step 5: Generate natural language response
            response = await self._generate_response(
                message=message,
                intent=intent,
                entities=entities,
                execution_result=result,
                conversation_context=stm.get_context_for_llm()
            )
            
            # Step 6: Update memories
            stm.add_message("assistant", response)
            await self.long_term_memory.save_conversation(
                user_id=user.id,
                role="assistant",
                content=response,
                intent=intent,
                entities=entities
            )
            
            # Step 7: Learn preferences if applicable
            await self._learn_preferences(user.id, intent, entities)
            
            return response
            
        except Exception as e:
            logger.error("message_processing_error", error=str(e), user_id=user_id)
            error_response = "I apologize, but I encountered an error processing your request. Could you please try again?"
            stm.add_message("assistant", error_response)
            return error_response
    
    def _format_clarifying_questions(self, questions: list) -> str:
        """Format clarifying questions into a natural response."""
        if len(questions) == 1:
            return questions[0]
        
        response = "I need a bit more information:\n"
        for i, q in enumerate(questions, 1):
            response += f"{i}. {q}\n"
        return response.strip()
    
    async def _generate_response(self, message: str, intent: str, entities: Dict[str, Any],
                                execution_result: ExecutionResult, 
                                conversation_context: list) -> str:
        """
        Generate a natural language response using LLM.
        
        Args:
            message: Original user message
            intent: Detected intent
            entities: Extracted entities
            execution_result: Result of plan execution
            conversation_context: Recent conversation
            
        Returns:
            Natural language response
        """
        # If execution failed, return error message
        if not execution_result.success:
            return execution_result.message
        
        # Create prompt for response generation
        prompt = f"""Generate a friendly, conversational response to the user.

User message: "{message}"
Intent: {intent}
Actions taken: {execution_result.message}

Provide a natural, helpful response that:
1. Confirms what was done
2. Provides relevant details
3. Asks if there's anything else you can help with

Keep it concise and friendly. Use emojis appropriately."""
        
        try:
            if self.provider in ["openai", "groq"]:  # Groq uses OpenAI-compatible API
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": get_system_prompt()},
                        *conversation_context[-5:],  # Last 5 messages
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                return response.choices[0].message.content
            
            else:  # anthropic
                # Build message history
                messages = conversation_context[-5:] + [{"role": "user", "content": prompt}]
                
                response = await self.llm_client.messages.create(
                    model=self.model,
                    system=get_system_prompt(),
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error("response_generation_failed", error=str(e))
            # Fallback to execution result message
            return execution_result.message
    
    async def _learn_preferences(self, user_id: int, intent: str, entities: Dict[str, Any]) -> None:
        """
        Learn user preferences from interactions.
        
        Args:
            user_id: User ID
            intent: User intent
            entities: Extracted entities
        """
        # Example: Learn default reminder time
        if intent == "create_reminder" and entities.get("reminder_before"):
            await self.long_term_memory.save_preference(
                user_id=user_id,
                key="default_reminder_before",
                value=entities["reminder_before"],
                confidence=0.8
            )
            logger.info("learned_preference", user_id=user_id, key="default_reminder_before")

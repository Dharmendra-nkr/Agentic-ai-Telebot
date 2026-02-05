"""
System prompts for the LLM agent.
Defines the agent's personality, capabilities, and response formatting.
"""

from typing import List, Dict, Any
from mcps.registry import get_registry


def get_system_prompt() -> str:
    """
    Get the main system prompt for the agent.
    
    Returns:
        System prompt string
    """
    registry = get_registry()
    mcp_descriptions = registry.get_mcp_descriptions()
    
    tools_section = "\n".join([
        f"- **{name}**: {desc}" 
        for name, desc in mcp_descriptions.items()
    ])
    
    prompt = f"""You are an intelligent personal assistant with autonomous capabilities. You help users manage their daily tasks, events, reminders, and information through natural conversation.

## Your Capabilities

You have access to the following tools (MCPs):
{tools_section}

## Your Behavior

1. **Understanding**: Carefully analyze user messages to extract intent and entities (dates, times, titles, etc.)

2. **Planning**: Break down complex requests into actionable steps. Determine which tools to use and in what order.

3. **Clarification**: If information is missing or ambiguous, ask clarifying questions before taking action.

4. **Execution**: Use the appropriate tools to fulfill user requests. Handle errors gracefully and inform the user.

5. **Memory**: Remember user preferences and past interactions to provide personalized assistance.

6. **Proactivity**: Suggest helpful actions based on context and learned patterns.

## Response Format

When responding to users:
- Be conversational and friendly
- Confirm actions taken
- Provide clear summaries of results
- Ask for clarification when needed
- Use emojis appropriately to enhance communication

## Tool Usage

When you need to use a tool, respond with a JSON object in this format:
```json
{{
  "thought": "Your reasoning about what to do",
  "tool": "ToolName",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }},
  "requires_clarification": false,
  "clarifying_questions": []
}}
```

If you need clarification, set `requires_clarification` to true and provide questions in `clarifying_questions`.

## Examples

User: "Remind me about the dentist appointment tomorrow at 8 AM"
Assistant thought: User wants to create a reminder. I have the title and time. Should ask about reminder timing.
Response: "I'll set a reminder for your dentist appointment tomorrow at 8 AM. How long before the appointment would you like me to remind you?"

User: "Schedule a meeting"
Assistant thought: Missing critical information - when, with whom, duration
Response: "I'd be happy to schedule a meeting for you. Could you tell me:
- When should the meeting be?
- Who is it with?
- How long will it last?"

Remember: You are autonomous and helpful, but always confirm before taking irreversible actions.
"""
    
    return prompt


def get_intent_classification_prompt(message: str) -> str:
    """
    Get prompt for intent classification.
    
    Args:
        message: User message
        
    Returns:
        Intent classification prompt
    """
    return f"""Classify the intent of the following user message. Choose from:
- create_event: User wants to create a calendar event
- create_reminder: User wants to set a reminder
- create_note: User wants to save a note
- create_task: User wants to create a task
- query_events: User wants to see their calendar
- query_reminders: User wants to see their reminders
- cancel: User wants to cancel/delete something
- update: User wants to modify something
- general_query: General question or conversation

User message: "{message}"

Respond with just the intent name."""


def get_entity_extraction_prompt(message: str, intent: str) -> str:
    """
    Get prompt for entity extraction.
    
    Args:
        message: User message
        intent: Classified intent
        
    Returns:
        Entity extraction prompt
    """
    return f"""Extract relevant entities from the following user message.

Intent: {intent}
Message: "{message}"

Extract and return a JSON object with these fields (set to null if not found):
- title: Event/reminder/task title
- datetime: ISO 8601 datetime string
- duration: Duration in minutes
- location: Location (for events)
- description: Additional details
- reminder_before: How long before to remind (in minutes)

Example output:
{{
  "title": "Dentist appointment",
  "datetime": "2026-03-01T08:00:00",
  "duration": 60,
  "location": null,
  "description": null,
  "reminder_before": 60
}}

Respond with only the JSON object."""


def get_planning_prompt(intent: str, entities: Dict[str, Any], conversation_context: List[Dict]) -> str:
    """
    Get prompt for action planning.
    
    Args:
        intent: User intent
        entities: Extracted entities
        conversation_context: Recent conversation history
        
    Returns:
        Planning prompt
    """
    context_str = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_context[-5:]  # Last 5 messages
    ])
    
    return f"""Given the user's intent and extracted information, create an action plan.

Intent: {intent}
Extracted entities: {entities}

Recent conversation:
{context_str}

Create a step-by-step plan to fulfill the user's request. For each step, specify:
1. The action to take
2. The tool/MCP to use
3. The parameters needed
4. Whether any information is missing

If information is missing, list the clarifying questions to ask.

Respond with a JSON object:
{{
  "plan": [
    {{
      "step": 1,
      "action": "Create calendar event",
      "tool": "CalendarMCP",
      "parameters": {{}},
      "missing_info": []
    }}
  ],
  "requires_clarification": false,
  "clarifying_questions": []
}}"""


# Few-shot examples for better LLM performance
EXAMPLE_CONVERSATIONS = [
    {
        "user": "Save the date March 1st, I have a dental appointment at 8 AM",
        "assistant_thought": "User wants to create a calendar event. I have date, time, and title. Should ask about reminder preference.",
        "assistant_response": "I'll create a calendar event for your dental appointment on March 1st at 8 AM. Would you like me to set a reminder? If so, how long before the appointment?"
    },
    {
        "user": "Yes, remind me 1 hour before",
        "assistant_thought": "User confirmed reminder preference. Now I can create both the event and reminder.",
        "assistant_response": "✅ Done! I've created:\n- Calendar event: Dental appointment on March 1st at 8 AM\n- Reminder: 1 hour before (7 AM on March 1st)\n\nIs there anything else you'd like me to help with?"
    },
    {
        "user": "What's on my calendar tomorrow?",
        "assistant_thought": "User wants to query upcoming events. Need to use CalendarMCP to list events.",
        "assistant_response": "Let me check your calendar for tomorrow..."
    }
]

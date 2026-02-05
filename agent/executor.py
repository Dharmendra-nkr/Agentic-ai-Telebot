"""
Agent executor for running planned actions.
Executes MCP calls and aggregates results.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from mcps.registry import get_registry
from mcps.base import MCPOutput, MCPStatus
from mcps.calendar_mcp import CalendarMCP, CalendarInput
from mcps.reminder_mcp import ReminderMCP, ReminderInput
from agent.planner import Plan
from utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionResult:
    """Result of plan execution."""
    
    def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None, 
                 errors: Optional[List[str]] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.errors = errors or []
    
    def __repr__(self):
        return f"<ExecutionResult(success={self.success}, message={self.message})>"


class AgentExecutor:
    """
    Executes planned actions using MCPs.
    Handles tool calls, error recovery, and result aggregation.
    """
    
    def __init__(self, db: AsyncSession, scheduler=None):
        """
        Initialize the executor.
        
        Args:
            db: Database session
            scheduler: Optional scheduler for reminder notifications
        """
        self.db = db
        self.registry = get_registry()
        
        # Initialize MCPs
        self.calendar_mcp = CalendarMCP(db)
        self.reminder_mcp = ReminderMCP(db, scheduler=scheduler)
        
        # Register MCPs
        self.registry.register(self.calendar_mcp)
        self.registry.register(self.reminder_mcp)
        
        logger.info("agent_executor_initialized", registered_mcps=len(self.registry))
    
    async def execute_plan(self, plan: Plan, user_id: int) -> ExecutionResult:
        """
        Execute a plan by running all steps.
        
        Args:
            plan: Plan to execute
            user_id: User ID for context
            
        Returns:
            ExecutionResult with aggregated results
        """
        if plan.requires_clarification:
            return ExecutionResult(
                success=False,
                message="Need more information",
                data={"clarifying_questions": plan.clarifying_questions}
            )
        
        results = []
        errors = []
        
        for step in plan.steps:
            try:
                logger.info("executing_step", step=step["step"], action=step["action"])
                result = await self._execute_step(step, user_id)
                results.append(result)
                
                if result.status == MCPStatus.FAILURE:
                    errors.append(f"Step {step['step']} failed: {result.error}")
                    logger.warning("step_failed", step=step["step"], error=result.error)
                
            except Exception as e:
                error_msg = f"Step {step['step']} error: {str(e)}"
                errors.append(error_msg)
                logger.error("step_execution_error", step=step["step"], error=str(e))
        
        # Aggregate results
        success = len(errors) == 0
        message = self._create_summary_message(results, errors)
        
        return ExecutionResult(
            success=success,
            message=message,
            data={"results": [r.data for r in results]},
            errors=errors
        )
    
    async def _execute_step(self, step: Dict[str, Any], user_id: int) -> MCPOutput:
        """
        Execute a single step.
        
        Args:
            step: Step definition
            user_id: User ID
            
        Returns:
            MCPOutput from the MCP
        """
        tool_name = step["tool"]
        parameters = step["parameters"]
        
        # Get the MCP
        mcp = self.registry.get(tool_name)
        if not mcp:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Tool {tool_name} not found",
                error="Tool not registered"
            )
        
        # Create appropriate input based on tool
        if tool_name == "CalendarMCP":
            input_data = CalendarInput(**parameters)
        elif tool_name == "ReminderMCP":
            input_data = ReminderInput(**parameters)
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Unknown tool: {tool_name}",
                error="Unknown tool"
            )
        
        # Execute with retry
        result = await mcp.execute_with_retry(input_data, user_id=user_id, max_retries=2)
        
        return result
    
    def _create_summary_message(self, results: List[MCPOutput], errors: List[str]) -> str:
        """
        Create a human-readable summary of execution results.
        
        Args:
            results: List of MCP outputs
            errors: List of error messages
            
        Returns:
            Summary message
        """
        if errors:
            return f"❌ Completed with errors:\n" + "\n".join(f"- {e}" for e in errors)
        
        if not results:
            return "No actions were taken."
        
        # Create success message
        messages = []
        for result in results:
            if result.status == MCPStatus.SUCCESS:
                messages.append(f"✅ {result.message}")
            else:
                messages.append(f"⚠️ {result.message}")
        
        return "\n".join(messages)
    
    async def execute_single_action(self, tool_name: str, parameters: Dict[str, Any], 
                                   user_id: int) -> MCPOutput:
        """
        Execute a single MCP action directly.
        
        Args:
            tool_name: Name of the MCP
            parameters: Action parameters
            user_id: User ID
            
        Returns:
            MCPOutput
        """
        step = {
            "step": 1,
            "action": "direct_action",
            "tool": tool_name,
            "parameters": parameters
        }
        
        return await self._execute_step(step, user_id)

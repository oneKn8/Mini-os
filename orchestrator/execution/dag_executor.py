"""
DAG-Based Parallel Execution Engine

Executes tool calls in parallel while respecting dependencies.
This is the core performance optimization that replaces sequential ReAct loops.

Key Features:
- Parallel execution with asyncio.gather() for independent tools
- Dependency-aware execution graph
- Automatic retry with exponential backoff
- Real-time progress streaming
- Error isolation (one tool failure doesn't stop others)

Example:
    Query: "What's my day like?"
    Plan: [get_calendar, get_emails, get_weather]

    Traditional Sequential: 3 tools x 5s = 15s
    DAG Parallel: max(5s, 5s, 5s) = 5s (3x faster)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Execution status for a step."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """
    Represents a single tool execution in the DAG.

    Attributes:
        tool_name: Name of the tool to execute
        tool: The actual tool instance (BaseTool or callable)
        args: Arguments to pass to the tool
        dependencies: List of tool names that must complete first
        priority: Higher priority steps run first when multiple are ready (1-10)
        retry_count: Number of retry attempts (default: 2)
        timeout_ms: Timeout in milliseconds (default: 30000)
    """

    tool_name: str
    tool: Any
    args: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5
    retry_count: int = 2
    timeout_ms: int = 30000

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration_ms(self) -> Optional[int]:
        """Get execution duration in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

    def is_ready(self, completed_steps: Set[str]) -> bool:
        """Check if all dependencies are completed."""
        return all(dep in completed_steps for dep in self.dependencies)


@dataclass
class ExecutionResult:
    """
    Result of DAG execution.

    Attributes:
        success: Whether execution completed successfully
        results: Map of tool_name -> result for completed steps
        errors: Map of tool_name -> error for failed steps
        total_duration_ms: Total execution time
        step_details: Detailed info for each step
    """

    success: bool
    results: Dict[str, Any]
    errors: Dict[str, str]
    total_duration_ms: int
    step_details: Dict[str, Dict[str, Any]]


class DAGExecutor:
    """
    Parallel execution engine with dependency management.

    Replaces sequential ReAct loops with intelligent parallel execution.
    """

    def __init__(
        self,
        streaming_session: Optional[Any] = None,
        max_parallel: int = 10,
        retry_delay_ms: int = 1000,
    ):
        """
        Initialize DAG executor.

        Args:
            streaming_session: Optional streaming session for progress events
            max_parallel: Maximum number of tools to run in parallel
            retry_delay_ms: Base delay between retries (exponential backoff)
        """
        self.streaming_session = streaming_session
        self.max_parallel = max_parallel
        self.retry_delay_ms = retry_delay_ms
        self.visual_feedback = None  # Set by enhanced_agent if visual feedback enabled

    async def execute_plan(
        self,
        steps: List[ExecutionStep],
        emit_progress: bool = True,
    ) -> ExecutionResult:
        """
        Execute a plan with parallel execution and dependency management.

        Args:
            steps: List of execution steps
            emit_progress: Whether to emit progress events

        Returns:
            ExecutionResult with all completed steps and errors
        """
        start_time = time.time()

        # Build dependency graph
        step_map = {step.tool_name: step for step in steps}
        completed_steps: Set[str] = set()
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        if emit_progress and self.streaming_session:
            tool_names = [s.tool_name for s in steps]
            await self.streaming_session.emit_agent_status(
                "executing",
                message=f"Executing {len(steps)} tools",
                tools=tool_names,
            )

        total_steps = len(steps)
        current_step = 0

        # Main execution loop
        while len(completed_steps) < total_steps:
            # Find all ready steps
            ready_steps = self._get_ready_steps(step_map, completed_steps)

            if not ready_steps:
                # Check if we're stuck (all remaining steps have unmet dependencies)
                remaining = [s for s in step_map.values() if s.status == StepStatus.PENDING]
                if remaining:
                    # Dependency deadlock or all dependencies failed
                    for step in remaining:
                        step.status = StepStatus.SKIPPED
                        errors[step.tool_name] = "Unmet dependencies or dependency failure"
                    break
                else:
                    # All done
                    break

            # Limit parallelism
            ready_steps = ready_steps[: self.max_parallel]

            # Emit progress
            if emit_progress and self.streaming_session:
                action = f"Running {len(ready_steps)} tools in parallel: {', '.join(s.tool_name for s in ready_steps)}"
                await self.streaming_session.emit_progress(
                    current_step=current_step,
                    total_steps=total_steps,
                    current_action=action,
                )

            # Execute ready steps in parallel
            batch_results = await asyncio.gather(
                *[self._execute_step_with_retry(step, emit_progress) for step in ready_steps],
                return_exceptions=True,
            )

            # Process results
            for step, result in zip(ready_steps, batch_results):
                current_step += 1

                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    errors[step.tool_name] = str(result)
                    logger.error(f"Tool {step.tool_name} failed: {result}")
                elif step.status == StepStatus.COMPLETED:
                    completed_steps.add(step.tool_name)
                    results[step.tool_name] = step.result
                else:
                    # Failed after retries
                    errors[step.tool_name] = step.error or "Unknown error"

        # Build result
        total_duration_ms = int((time.time() - start_time) * 1000)

        step_details = {}
        for step in steps:
            step_details[step.tool_name] = {
                "status": step.status.value,
                "duration_ms": step.duration_ms,
                "attempts": step.attempts,
                "error": step.error,
            }

        success = len(errors) == 0

        if emit_progress and self.streaming_session:
            status = "completed" if success else "completed_with_errors"
            message = f"Executed {len(results)} tools successfully"
            if errors:
                message += f", {len(errors)} failed"
            await self.streaming_session.emit_agent_status(status, message=message)

        return ExecutionResult(
            success=success,
            results=results,
            errors=errors,
            total_duration_ms=total_duration_ms,
            step_details=step_details,
        )

    def _get_ready_steps(
        self,
        step_map: Dict[str, ExecutionStep],
        completed_steps: Set[str],
    ) -> List[ExecutionStep]:
        """
        Get all steps that are ready to execute.

        A step is ready if:
        1. Status is PENDING or READY (READY means it was ready before but not executed due to max_parallel limit)
        2. All dependencies are completed

        Returns steps sorted by priority (highest first).
        """
        ready = []

        for step in step_map.values():
            # Check both PENDING and READY to handle max_parallel limiting
            if step.status in (StepStatus.PENDING, StepStatus.READY) and step.is_ready(completed_steps):
                step.status = StepStatus.READY
                ready.append(step)

        # Sort by priority (higher first)
        ready.sort(key=lambda s: s.priority, reverse=True)

        return ready

    async def _execute_step_with_retry(
        self,
        step: ExecutionStep,
        emit_progress: bool,
    ) -> Any:
        """
        Execute a step with automatic retry on failure.

        Uses exponential backoff: delay * (2 ** attempt)
        """
        step.status = StepStatus.RUNNING
        step.start_time = time.time()

        # Emit start event
        if emit_progress and self.streaming_session:
            await self.streaming_session.emit_tool_start(
                tool_name=step.tool_name,
                args=step.args,
            )

        # Visual feedback: start
        if self.visual_feedback:
            await self.visual_feedback.start_tool_execution(step.tool_name, step.args)

        last_error = None

        for attempt in range(step.retry_count + 1):
            step.attempts = attempt + 1

            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute_tool(step.tool, step.args),
                    timeout=step.timeout_ms / 1000,
                )

                # Success
                step.status = StepStatus.COMPLETED
                step.result = result
                step.end_time = time.time()

                # Emit completion event
                if emit_progress and self.streaming_session:
                    await self.streaming_session.emit_tool_complete(
                        tool_name=step.tool_name,
                        result=result,
                        duration_ms=step.duration_ms or 0,
                    )

                # Visual feedback: complete
                if self.visual_feedback:
                    await self.visual_feedback.complete_tool_execution(step.tool_name, result, success=True)

                return result

            except asyncio.TimeoutError as e:
                last_error = f"Timeout after {step.timeout_ms}ms"
                logger.warning(f"Tool {step.tool_name} timeout (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Tool {step.tool_name} failed (attempt {attempt + 1}): {e}")

            # Retry delay with exponential backoff
            if attempt < step.retry_count:
                delay = (self.retry_delay_ms / 1000) * (2**attempt)
                await asyncio.sleep(delay)

        # All retries exhausted
        step.status = StepStatus.FAILED
        step.error = last_error
        step.end_time = time.time()

        # Emit error event
        if emit_progress and self.streaming_session:
            await self.streaming_session.emit_tool_error(
                tool_name=step.tool_name,
                error=last_error or "Unknown error",
            )

        # Visual feedback: error
        if self.visual_feedback:
            await self.visual_feedback.complete_tool_execution(step.tool_name, None, success=False)

        raise Exception(f"Tool {step.tool_name} failed after {step.retry_count + 1} attempts: {last_error}")

    async def _execute_tool(self, tool: Any, args: Dict[str, Any]) -> Any:
        """
        Execute a tool (supports multiple tool interfaces).

        Supports:
        - LangChain BaseTool with ainvoke/invoke
        - Async callables
        - Sync callables (wrapped in executor)
        - Dict-based tool definitions
        """
        # LangChain async tool
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(args)

        # LangChain sync tool
        if hasattr(tool, "invoke"):
            # Run sync tool in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, tool.invoke, args)

        # Async callable
        if callable(tool):
            result = tool(**args)
            if hasattr(result, "__await__"):
                return await result
            return result

        # Dict-based tool
        if isinstance(tool, dict):
            func = tool.get("function")
            if callable(func):
                result = func(**args)
                if hasattr(result, "__await__"):
                    return await result
                return result

        raise ValueError(f"Unknown tool type: {type(tool)}")

    @staticmethod
    def from_tool_plan(
        tool_plan,
        tool_map: Dict[str, BaseTool],
        tool_args: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[ExecutionStep]:
        """
        Convert a ToolPlan to ExecutionSteps.

        Args:
            tool_plan: ToolPlan with parallel_groups
            tool_map: Map of tool_name -> tool instance
            tool_args: Optional arguments for each tool

        Returns:
            List of ExecutionSteps with dependency relationships
        """
        steps = []
        tool_args = tool_args or {}

        # Process parallel groups to build dependencies
        # Tools in the same group have no dependencies on each other
        # Tools in later groups depend on all tools in earlier groups
        previous_group_tools: List[str] = []

        for group_idx, group in enumerate(tool_plan.parallel_groups):
            for tool_name in group:
                if tool_name not in tool_map:
                    logger.warning(f"Tool {tool_name} not found in tool_map, skipping")
                    continue

                step = ExecutionStep(
                    tool_name=tool_name,
                    tool=tool_map[tool_name],
                    args=tool_args.get(tool_name, {}),
                    dependencies=previous_group_tools.copy(),
                    priority=10 - group_idx,  # Earlier groups have higher priority
                )

                steps.append(step)

            # Update dependencies for next group
            previous_group_tools.extend(group)

        return steps

    @staticmethod
    def create_simple_parallel_plan(
        tool_names: List[str],
        tool_map: Dict[str, BaseTool],
        tool_args: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[ExecutionStep]:
        """
        Create a simple plan where all tools run in parallel (no dependencies).

        Args:
            tool_names: List of tool names to execute
            tool_map: Map of tool_name -> tool instance
            tool_args: Optional arguments for each tool

        Returns:
            List of ExecutionSteps with no dependencies
        """
        steps = []
        tool_args = tool_args or {}

        for tool_name in tool_names:
            if tool_name not in tool_map:
                logger.warning(f"Tool {tool_name} not found in tool_map, skipping")
                continue

            step = ExecutionStep(
                tool_name=tool_name,
                tool=tool_map[tool_name],
                args=tool_args.get(tool_name, {}),
                dependencies=[],  # No dependencies = run in parallel
                priority=5,
            )

            steps.append(step)

        return steps

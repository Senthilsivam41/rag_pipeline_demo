"""Telemetry and logging for agent tool usage.

Tracks which tools are invoked, with inputs/outputs, for auditing
and debugging agent behavior.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_telemetry")


@dataclass
class ToolCall:
    """Record of a single tool invocation."""
    timestamp: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AgentTelemetry:
    """Centralized telemetry collector for agent tool usage."""

    def __init__(self, max_history: int = 100):
        """Initialize telemetry collector.

        Args:
            max_history: Maximum number of tool calls to keep in memory
        """
        self.max_history = max_history
        self.tool_calls: List[ToolCall] = []
        self.session_start_time = datetime.now()

    def log_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        execution_time_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Record a tool call.

        Args:
            tool_name: Name of the tool invoked
            tool_input: Input arguments to the tool
            tool_output: Output/result from the tool
            execution_time_ms: Time taken to execute (in milliseconds)
            success: Whether the tool call succeeded
            error_message: Error message if tool call failed
        """
        tool_call = ToolCall(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message
        )
        self.tool_calls.append(tool_call)

        # Keep only max_history calls
        if len(self.tool_calls) > self.max_history:
            self.tool_calls.pop(0)

        # Log to standard logger
        log_msg = f"Tool: {tool_name} | Input: {tool_input} | Output: {tool_output} | Time: {execution_time_ms:.2f}ms"
        if success:
            logger.info(log_msg)
        else:
            logger.error(f"{log_msg} | Error: {error_message}")

    def get_latest_call(self) -> Optional[ToolCall]:
        """Get the most recent tool call."""
        return self.tool_calls[-1] if self.tool_calls else None

    def get_call_history(self, n: Optional[int] = None) -> List[ToolCall]:
        """Get recent tool call history.

        Args:
            n: Number of recent calls to retrieve. If None, returns all.

        Returns:
            List of ToolCall records (newest first)
        """
        if n is None:
            return list(reversed(self.tool_calls))
        return list(reversed(self.tool_calls[-n:]))

    def get_tool_call_counts(self) -> Dict[str, int]:
        """Count how many times each tool was called.

        Returns:
            Dictionary mapping tool names to call counts
        """
        counts: Dict[str, int] = {}
        for call in self.tool_calls:
            counts[call.tool_name] = counts.get(call.tool_name, 0) + 1
        return counts

    def get_tool_success_rate(self) -> Dict[str, float]:
        """Calculate success rate for each tool.

        Returns:
            Dictionary mapping tool names to success rates (0.0 to 1.0)
        """
        success_rates: Dict[str, float] = {}
        tool_stats: Dict[str, Dict[str, int]] = {}

        for call in self.tool_calls:
            if call.tool_name not in tool_stats:
                tool_stats[call.tool_name] = {"total": 0, "success": 0}
            tool_stats[call.tool_name]["total"] += 1
            if call.success:
                tool_stats[call.tool_name]["success"] += 1

        for tool_name, stats in tool_stats.items():
            success_rates[tool_name] = (
                stats["success"] / stats["total"] if stats["total"] > 0 else 0.0
            )

        return success_rates

    def get_average_execution_time(self) -> Dict[str, float]:
        """Calculate average execution time for each tool.

        Returns:
            Dictionary mapping tool names to average execution time (ms)
        """
        avg_times: Dict[str, List[float]] = {}

        for call in self.tool_calls:
            if call.tool_name not in avg_times:
                avg_times[call.tool_name] = []
            avg_times[call.tool_name].append(call.execution_time_ms)

        return {
            tool_name: sum(times) / len(times)
            for tool_name, times in avg_times.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive telemetry summary.

        Returns:
            Dictionary with aggregated telemetry data
        """
        return {
            "session_duration_seconds": (
                datetime.now() - self.session_start_time
            ).total_seconds(),
            "total_tool_calls": len(self.tool_calls),
            "tool_call_counts": self.get_tool_call_counts(),
            "tool_success_rates": self.get_tool_success_rate(),
            "average_execution_times_ms": self.get_average_execution_time(),
        }

    def clear(self) -> None:
        """Clear all recorded tool calls."""
        self.tool_calls.clear()


# Global telemetry instance
_telemetry_instance: Optional[AgentTelemetry] = None


def get_telemetry() -> AgentTelemetry:
    """Get the global telemetry instance (singleton)."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = AgentTelemetry()
    return _telemetry_instance


def reset_telemetry() -> None:
    """Reset telemetry instance."""
    global _telemetry_instance
    _telemetry_instance = AgentTelemetry()

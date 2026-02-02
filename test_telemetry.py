"""Tests for agent telemetry and logging."""

import pytest
import time
from agent_telemetry import (
    AgentTelemetry,
    ToolCall,
    get_telemetry,
    reset_telemetry
)


class TestToolCall:
    """Test ToolCall dataclass."""

    def test_tool_call_creation(self):
        """Test creating a ToolCall record."""
        call = ToolCall(
            timestamp="2025-02-02T10:00:00",
            tool_name="sum_column",
            tool_input={"column_name": "salary"},
            tool_output=150000.0,
            execution_time_ms=10.5,
            success=True
        )
        assert call.tool_name == "sum_column"
        assert call.execution_time_ms == 10.5
        assert call.success is True
        assert call.error_message is None

    def test_tool_call_with_error(self):
        """Test ToolCall with error."""
        call = ToolCall(
            timestamp="2025-02-02T10:00:00",
            tool_name="sum_column",
            tool_input={"column_name": "invalid"},
            tool_output=None,
            execution_time_ms=2.3,
            success=False,
            error_message="Column not found"
        )
        assert call.success is False
        assert call.error_message == "Column not found"

    def test_tool_call_to_dict(self):
        """Test converting ToolCall to dict."""
        call = ToolCall(
            timestamp="2025-02-02T10:00:00",
            tool_name="average_column",
            tool_input={"column_name": "salary"},
            tool_output=75000.0,
            execution_time_ms=8.2,
            success=True
        )
        d = call.to_dict()
        assert d["tool_name"] == "average_column"
        assert d["execution_time_ms"] == 8.2

    def test_tool_call_to_json(self):
        """Test converting ToolCall to JSON."""
        call = ToolCall(
            timestamp="2025-02-02T10:00:00",
            tool_name="count_column",
            tool_input={"column_name": "id"},
            tool_output=100,
            execution_time_ms=5.0,
            success=True
        )
        json_str = call.to_json()
        assert "count_column" in json_str
        assert "100" in json_str


class TestAgentTelemetry:
    """Test AgentTelemetry collector."""

    def test_telemetry_initialization(self):
        """Test creating a telemetry instance."""
        telemetry = AgentTelemetry(max_history=50)
        assert telemetry.max_history == 50
        assert len(telemetry.tool_calls) == 0

    def test_log_tool_call(self):
        """Test logging a single tool call."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call(
            tool_name="sum_column",
            tool_input={"column_name": "salary"},
            tool_output=100000.0,
            execution_time_ms=5.2,
            success=True
        )
        assert len(telemetry.tool_calls) == 1
        assert telemetry.tool_calls[0].tool_name == "sum_column"

    def test_log_multiple_calls(self):
        """Test logging multiple tool calls."""
        telemetry = AgentTelemetry()
        for i in range(5):
            telemetry.log_tool_call(
                tool_name=f"tool_{i}",
                tool_input={"param": i},
                tool_output=i * 10,
                execution_time_ms=float(i),
                success=True
            )
        assert len(telemetry.tool_calls) == 5

    def test_max_history_enforced(self):
        """Test that max_history limit is enforced."""
        telemetry = AgentTelemetry(max_history=3)
        for i in range(5):
            telemetry.log_tool_call(
                tool_name=f"tool_{i}",
                tool_input={"param": i},
                tool_output=i,
                execution_time_ms=1.0,
                success=True
            )
        assert len(telemetry.tool_calls) == 3
        # Oldest calls should be removed
        assert telemetry.tool_calls[0].tool_name == "tool_2"

    def test_get_latest_call(self):
        """Test getting the latest tool call."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("tool_1", {}, "result1", 1.0, True)
        telemetry.log_tool_call("tool_2", {}, "result2", 2.0, True)

        latest = telemetry.get_latest_call()
        assert latest is not None
        assert latest.tool_name == "tool_2"

    def test_get_call_history(self):
        """Test retrieving call history."""
        telemetry = AgentTelemetry()
        for i in range(3):
            telemetry.log_tool_call(f"tool_{i}", {}, f"result_{i}", float(i), True)

        history = telemetry.get_call_history()
        assert len(history) == 3
        # Should be in reverse order (newest first)
        assert history[0].tool_name == "tool_2"
        assert history[1].tool_name == "tool_1"
        assert history[2].tool_name == "tool_0"

    def test_get_call_history_with_limit(self):
        """Test getting limited call history."""
        telemetry = AgentTelemetry()
        for i in range(5):
            telemetry.log_tool_call(f"tool_{i}", {}, f"result_{i}", float(i), True)

        history = telemetry.get_call_history(n=2)
        assert len(history) == 2
        assert history[0].tool_name == "tool_4"

    def test_get_tool_call_counts(self):
        """Test counting tool calls by name."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("sum_column", {}, 100, 1.0, True)
        telemetry.log_tool_call("sum_column", {}, 200, 1.0, True)
        telemetry.log_tool_call("average_column", {}, 150, 1.0, True)

        counts = telemetry.get_tool_call_counts()
        assert counts["sum_column"] == 2
        assert counts["average_column"] == 1

    def test_get_tool_success_rate(self):
        """Test calculating tool success rates."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("sum_column", {}, 100, 1.0, success=True)
        telemetry.log_tool_call("sum_column", {}, None, 1.0, success=False)
        telemetry.log_tool_call("average_column", {}, 50, 1.0, success=True)

        rates = telemetry.get_tool_success_rate()
        assert rates["sum_column"] == 0.5  # 1 success out of 2
        assert rates["average_column"] == 1.0  # 1 success out of 1

    def test_get_average_execution_time(self):
        """Test calculating average execution times."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("sum_column", {}, 100, 10.0, True)
        telemetry.log_tool_call("sum_column", {}, 200, 20.0, True)
        telemetry.log_tool_call("average_column", {}, 50, 15.0, True)

        avg_times = telemetry.get_average_execution_time()
        assert avg_times["sum_column"] == 15.0
        assert avg_times["average_column"] == 15.0

    def test_get_summary(self):
        """Test getting comprehensive telemetry summary."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("sum_column", {}, 100, 5.0, True)
        telemetry.log_tool_call("average_column", {}, 50, 10.0, True)

        summary = telemetry.get_summary()
        assert summary["total_tool_calls"] == 2
        assert "tool_call_counts" in summary
        assert "tool_success_rates" in summary
        assert "average_execution_times_ms" in summary
        assert "session_duration_seconds" in summary

    def test_clear_telemetry(self):
        """Test clearing telemetry data."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call("tool_1", {}, "result", 1.0, True)
        assert len(telemetry.tool_calls) == 1

        telemetry.clear()
        assert len(telemetry.tool_calls) == 0

    def test_log_error_message(self):
        """Test logging tool call with error."""
        telemetry = AgentTelemetry()
        telemetry.log_tool_call(
            tool_name="invalid_tool",
            tool_input={"column": "invalid"},
            tool_output=None,
            execution_time_ms=2.5,
            success=False,
            error_message="Column 'invalid' not found"
        )
        call = telemetry.get_latest_call()
        assert call is not None
        assert call.success is False
        assert call.error_message is not None
        assert "Column" in call.error_message


class TestSingleton:
    """Test singleton pattern for telemetry."""

    def test_get_telemetry_singleton(self):
        """Test that get_telemetry returns same instance."""
        reset_telemetry()
        tel1 = get_telemetry()
        tel2 = get_telemetry()
        assert tel1 is tel2

    def test_reset_telemetry(self):
        """Test resetting telemetry instance."""
        tel1 = get_telemetry()
        tel1.log_tool_call("tool_1", {}, "result", 1.0, True)
        assert len(tel1.tool_calls) == 1

        reset_telemetry()
        tel2 = get_telemetry()
        assert len(tel2.tool_calls) == 0
        assert tel1 is not tel2

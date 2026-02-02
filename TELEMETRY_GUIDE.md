# Agent Telemetry & Logging

## Overview

The telemetry system tracks which tools the agent invokes, captures input/output, execution time, and success/failure status for each tool call. This provides:

- **Debugging**: Understand which tools the agent chooses for different queries
- **Auditing**: Complete history of tool usage and results
- **Performance Monitoring**: Track execution times and success rates
- **Transparency**: Users can see exactly what the agent did

## Components

### `agent_telemetry.py`

Core telemetry module with:

#### `ToolCall` (Dataclass)
Represents a single tool invocation:
```python
@dataclass
class ToolCall:
    timestamp: str              # ISO format timestamp
    tool_name: str             # Name of the tool
    tool_input: Dict           # Input arguments
    tool_output: Any           # Result/output from tool
    execution_time_ms: float   # Execution time in milliseconds
    success: bool              # Whether call succeeded
    error_message: Optional[str]  # Error if call failed
```

#### `AgentTelemetry` (Main Collector)
Centralized telemetry collector:

**Key Methods:**
- `log_tool_call(...)` — Record a tool invocation
- `get_latest_call()` — Get most recent tool call
- `get_call_history(n=None)` — Retrieve recent calls (newest first)
- `get_tool_call_counts()` — Count calls per tool
- `get_tool_success_rate()` — Calculate success rates (0.0-1.0)
- `get_average_execution_time()` — Average time per tool
- `get_summary()` — Comprehensive aggregated telemetry
- `clear()` — Reset telemetry data

**Singleton Pattern:**
```python
from agent_telemetry import get_telemetry

telemetry = get_telemetry()  # Global instance
telemetry.log_tool_call(...)
```

## Integration with `app_hybrid.py`

### 1. Initialize Telemetry in Session State
```python
if "telemetry" not in st.session_state:
    st.session_state.telemetry = get_telemetry()
```

### 2. Instrument Tools
Tools are wrapped to automatically capture telemetry:
```python
# In app_hybrid.py
telemetry = st.session_state.telemetry
instrumented_tools = [
    instrument_tool(tool, telemetry) for tool in agg_tools
]

# Pass instrumented tools to agent
agent = create_react_agent(llm, instrumented_tools, prompt=system_prompt)
```

### 3. Display Tool Usage After Each Query
After the agent responds, tool usage details are shown:
```
🔍 Tool Usage Details
┌─────────────────────────────────────────┐
│ Tool Used: groupby_count                │
│ Execution Time: 3.45ms                  │
│ Status: ✅ Success                      │
├─────────────────────────────────────────┤
│ Input: {"args": "('department',)"}      │
│ Output: {'IT': 12, 'Sales': 8, ...}     │
└─────────────────────────────────────────┘
```

### 4. Telemetry Dashboard in Sidebar
Expandable "📈 Tool Usage Telemetry" section shows:

**Statistics:**
- Total tool calls count
- Calls per tool (sorted by frequency)
- Success rates per tool
- Average execution time per tool

**Recent Calls:**
- Last 5 tool invocations with timestamp and execution time
- Status indicator (✅ or ❌)

**Actions:**
- "🗑️ Clear Telemetry" button to reset data

## Usage Examples

### Example 1: Log a Successful Tool Call
```python
from agent_telemetry import get_telemetry

telemetry = get_telemetry()
telemetry.log_tool_call(
    tool_name="groupby_count",
    tool_input={"group_column": "department"},
    tool_output={"IT": 12, "Sales": 8, "HR": 5},
    execution_time_ms=3.45,
    success=True
)
```

### Example 2: Log a Failed Tool Call
```python
telemetry.log_tool_call(
    tool_name="sum_column",
    tool_input={"column_name": "invalid_col"},
    tool_output=None,
    execution_time_ms=1.2,
    success=False,
    error_message="Column 'invalid_col' not found"
)
```

### Example 3: Get Telemetry Summary
```python
summary = telemetry.get_summary()
print(f"Total calls: {summary['total_tool_calls']}")
print(f"Success rates: {summary['tool_success_rates']}")
print(f"Avg times: {summary['average_execution_times_ms']}")
```

### Example 4: Review Recent Tool Calls
```python
recent = telemetry.get_call_history(n=5)
for call in recent:
    print(f"Tool: {call.tool_name} | Time: {call.execution_time_ms:.2f}ms | Success: {call.success}")
```

## Testing

19 comprehensive tests in `test_telemetry.py`:

**Test Coverage:**
- ToolCall creation and serialization (to_dict, to_json)
- Logging single and multiple calls
- Max history enforcement
- Call history retrieval (with and without limit)
- Tool call counting
- Success rate calculation
- Execution time averaging
- Summary generation
- Error logging
- Singleton pattern

**Run tests:**
```bash
pytest test_telemetry.py -v
```

## Architecture Design

### Tool Instrumentation Flow

```
User Query
    ↓
Agent receives query
    ↓
Agent invokes instrumented tool
    ↓
instrument_tool wrapper
  ├→ Records start time
  ├→ Executes original tool
  ├→ Records end time & result
  ├→ Calls telemetry.log_tool_call()
  └→ Returns result to agent
    ↓
Agent generates response
    ↓
UI displays response + tool details
```

### Telemetry Data Flow

```
Tool execution
    ↓
instrument_tool captures timing
    ↓
telemetry.log_tool_call() records data
    ↓
ToolCall appended to history (with max limit)
    ↓
Logged to Python logger (INFO/ERROR)
    ↓
UI retrieves via get_summary(), get_latest_call(), etc.
    ↓
Dashboard displays stats and recent calls
```

## Performance Considerations

- **Memory**: Max 100 ToolCall records kept in memory (configurable via `max_history`)
- **Overhead**: Minimal - only adds timing instrumentation (~microseconds per call)
- **Logging**: Uses Python's built-in logging (non-blocking)
- **UI**: Telemetry dashboard is lazy-loaded in an expander (no UI lag)

## Future Enhancements

1. **Persistent Storage**: Export telemetry to CSV/JSON for long-term analysis
2. **Advanced Analytics**: Generate agent behavior reports and recommendations
3. **Tool Recommendations**: Suggest better tools based on historical usage
4. **Threshold Alerts**: Warn if tool success rate drops or execution time spikes
5. **Multi-session Comparison**: Compare telemetry across multiple user sessions
6. **Tool Chains**: Track sequences of tool calls (e.g., get_column_sample → filter_count)

## Debugging Guide

### Scenario: Agent calling wrong tool for queries

**Debug Steps:**
1. Open "📈 Tool Usage Telemetry" in sidebar
2. Check "Calls per Tool" — tool overuse indicates miscalibration
3. Review "Recent Tool Calls" — see exact sequence of invocations
4. Check tool success rates — failures may indicate bad inputs from LLM

**Example Output:**
```
Calls per Tool:
  • groupby_count: 8
  • filter_count: 2
  • sum_column: 1

Recent Tool Calls:
1. ✅ groupby_count (2.34ms)
2. ✅ get_column_sample (1.56ms)
3. ✅ filter_count (1.89ms)
```

### Scenario: Tool taking too long

**Debug Steps:**
1. Check "Avg Execution Time" section
2. Identify slowest tool
3. Review dataset size or check for data processing bottlenecks

## Integration Checklist

- [x] Created `agent_telemetry.py` with core telemetry classes
- [x] Added `instrument_tool()` wrapper in `app_hybrid.py`
- [x] Initialize telemetry in session state
- [x] Instrument all tools before passing to agent
- [x] Display tool usage details after each query
- [x] Added telemetry dashboard in sidebar
- [x] Created comprehensive test suite (`test_telemetry.py`)
- [x] All tests passing (72 total, including 19 telemetry tests)

## Quick Start

1. **Enable Telemetry** (already done):
   - Import `from agent_telemetry import get_telemetry` in your app
   - Initialize: `telemetry = get_telemetry()`

2. **Use Dashboard**:
   - Open sidebar → click "📈 Tool Usage Telemetry"
   - View stats, recent calls, and click "Clear Telemetry" to reset

3. **Log Custom Tool Calls**:
   ```python
   telemetry.log_tool_call(
       tool_name="my_tool",
       tool_input={...},
       tool_output=result,
       execution_time_ms=elapsed_ms,
       success=True
   )
   ```

4. **Programmatic Access**:
   ```python
   summary = telemetry.get_summary()
   recent = telemetry.get_call_history(n=5)
   counts = telemetry.get_tool_call_counts()
   ```

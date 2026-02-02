# Telemetry Quick Reference

## 🚀 Quick Start

### View Telemetry in Streamlit App

1. **Upload a CSV file** in the sidebar
2. **Ask a question** (e.g., "Count employees by department")
3. **After agent responds**, look for:
   - **"🔍 Tool Usage Details"** expander (shows tool, execution time, status)
   - **"📈 Tool Usage Telemetry"** in sidebar (shows stats)

### Dashboard Features

```
📈 Tool Usage Telemetry
├─ Total Tool Calls: Shows total invocations
├─ Calls per Tool: Which tools are used most
├─ Success Rates: Reliability of each tool
├─ Avg Execution Time: Performance by tool
├─ Recent Tool Calls: Last 5 invocations with status
└─ 🗑️ Clear Telemetry: Reset stats
```

## 📊 Programmatic Access

### Get Summary Stats
```python
from agent_telemetry import get_telemetry

telemetry = get_telemetry()
summary = telemetry.get_summary()

print(f"Total calls: {summary['total_tool_calls']}")
print(f"Tools used: {summary['tool_call_counts']}")
print(f"Success rates: {summary['tool_success_rates']}")
```

### Get Recent Calls
```python
recent = telemetry.get_call_history(n=5)
for call in recent:
    print(f"{call.tool_name} - {call.execution_time_ms:.2f}ms")
```

### Log Custom Tool Call
```python
telemetry.log_tool_call(
    tool_name="my_tool",
    tool_input={"param": "value"},
    tool_output="result",
    execution_time_ms=1.5,
    success=True
)
```

## 🔍 What Each Metric Means

| Metric | Meaning | Good Value |
|--------|---------|-----------|
| Total Tool Calls | Number of tools invoked | Depends on queries |
| Calls per Tool | Frequency of each tool | Balanced distribution |
| Success Rate | % of successful calls | 90-100% |
| Avg Execution Time | Average speed per tool | < 10ms typical |
| Recent Calls | Last 5 invocations | Mix of tools, ✅ success |

## 🎯 Common Scenarios

### Scenario: Agent Using Wrong Tool

**What to look for:**
- Check "Calls per Tool" — if one tool dominates
- Review "Recent Tool Calls" — see which tool was used
- Check success rate for that tool

**Example:**
```
Calls per Tool:
  • sum_column: 15  ← Used too much!
  • groupby_count: 2
  • filter_count: 1
```
→ Agent may be treating all queries as summation

### Scenario: Tool Failures

**What to look for:**
- Check "Success Rates" section
- Tools with < 100% success rate
- Review "Recent Tool Calls" for ❌ marks

**Example:**
```
Success Rates:
  • filter_count: 60.0%  ← Problem!
  • sum_column: 100.0%
```
→ filter_count is failing 40% of the time

### Scenario: Slow Performance

**What to look for:**
- Check "Avg Execution Time" section
- Tools with high execution times
- Look for patterns (slowness on certain queries)

**Example:**
```
Avg Execution Time (ms):
  • groupby_count: 45.2ms  ← Slow!
  • filter_count: 2.3ms
```
→ groupby_count may be processing large groups slowly

## 🛠️ Debugging Tips

### Enable Logging
```python
import logging

# Show telemetry logs in console
logging.basicConfig(level=logging.INFO)
```

### Export Data for Analysis
```python
import json
from agent_telemetry import get_telemetry

telemetry = get_telemetry()
calls = telemetry.get_call_history()

# Convert to JSON
data = [call.to_dict() for call in calls]
with open("telemetry.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
```

### Check Specific Tool
```python
telemetry = get_telemetry()
counts = telemetry.get_tool_call_counts()
rates = telemetry.get_tool_success_rate()

tool_name = "groupby_count"
print(f"Calls: {counts.get(tool_name, 0)}")
print(f"Success Rate: {rates.get(tool_name, 0):.1%}")
```

## 📁 Files

| File | Purpose |
|------|---------|
| `agent_telemetry.py` | Core telemetry module (ToolCall, AgentTelemetry) |
| `app_hybrid.py` | Streamlit app (updated with telemetry UI) |
| `test_telemetry.py` | 19 unit tests for telemetry system |
| `TELEMETRY_GUIDE.md` | Comprehensive documentation |
| `TELEMETRY_IMPLEMENTATION.md` | Implementation details & summary |

## ✅ Verification

### Test Results
```bash
pytest test_telemetry.py -v
# Output: 19 passed
```

### All Tests
```bash
pytest test_aggregator.py test_dataset_validation.py test_telemetry.py -q
# Output: 72 passed, 61 warnings
```

## 💡 Tips

1. **Clear telemetry between sessions** → Use "🗑️ Clear Telemetry" button
2. **Export before clearing** → Save telemetry data programmatically
3. **Monitor success rates** → Tools with < 100% may need prompt adjustment
4. **Check execution times** → Slow tools may need optimization
5. **Review recent calls** → Understand agent's decision-making

## 🔗 Related

- **TELEMETRY_GUIDE.md** — Full documentation with examples
- **TELEMETRY_IMPLEMENTATION.md** — Technical implementation details
- **test_telemetry.py** — Test code showing usage patterns
- **agent_telemetry.py** — Source code with docstrings

## ❓ FAQ

**Q: Does telemetry slow down the agent?**
A: No, overhead is minimal (~microseconds per call).

**Q: Where is telemetry stored?**
A: In Streamlit session state (memory), max 100 records.

**Q: Can I export telemetry data?**
A: Yes, convert to JSON via `call.to_json()` or `to_dict()`.

**Q: How do I reset telemetry?**
A: Click "🗑️ Clear Telemetry" in sidebar, or call `telemetry.clear()`.

**Q: What if a tool never completes?**
A: It will be logged as a timeout error in recent calls.

---

**Last Updated:** February 2, 2025  
**Status:** ✅ Production Ready  
**Tests:** 19/19 Passing  
**Coverage:** Tool invocation, timing, success/error tracking

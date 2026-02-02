# 🎯 Features & Capabilities

## Overview

This project provides a **local, privacy-preserving RAG (Retrieval-Augmented Generation) pipeline** with support for PDFs, CSV, and Parquet files. It includes semantic search capabilities and **intelligent data aggregation** using AI agents.

---

## 📊 Data Aggregation (NEW)

The **`app_hybrid.py`** version includes intelligent data aggregation alongside semantic search using **LangChain's AI Agent framework**.

### Aggregation Functions

#### Basic Aggregations
- **sum** — Total sum of a numeric column
- **average** — Mean value of a numeric column  
- **min** — Minimum value in a column
- **max** — Maximum value in a column
- **median** — Median value in a column
- **count** — Number of rows
- **unique** — Count of unique values in a column

#### GroupBy Aggregations
- **groupby_sum** — Sum grouped by category
- **groupby_average** — Average grouped by category
- **groupby_count** — Count grouped by category

#### Advanced Operations
- **filter_and_aggregate** — Combine filtering conditions with aggregation
- **get_statistics** — Get min, max, average, median in one call
- **get_available_aggregations** — List all available functions

### AI Agent Routing

The system automatically routes queries to the appropriate tool:

**Semantic Search Queries:**
```
"Show me employees in the Engineering department"
→ Uses vector search + RAG retrieval
→ Returns: Matching rows with context
```

**Aggregation Queries:**
```
"What is the average salary?"
→ Uses aggregation tools
→ Returns: Single numeric value
```

**GroupBy Queries:**
```
"Average salary by department?"
→ Uses groupby_average tool
→ Returns: Dict with {department: average}
```

**Complex Queries:**
```
"Show me high earners and calculate average salary in IT"
→ Agent combines search + aggregation
→ Returns: Both results
```

---

## 🔍 Semantic Search Features

### Supported File Types
- **PDF** — Text extraction with page-level source tracking
- **CSV** — Comma-separated values with configurable encoding
- **Parquet** — Apache Parquet binary format

### Search Capabilities
- Full-text semantic search across documents
- Source attribution (page numbers for PDFs, row numbers for tables)
- Multi-encoding CSV support (UTF-8, Latin-1, ISO-8859-1, CP1252)
- Table-aware chunking for structured data

### Query Examples
```
"What are the key findings in this document?"
"Show me all employees earning more than 100k"
"Which products have the highest revenue?"
"Summarize the main topics covered"
```

---

## 📁 Application Versions

### 1️⃣ **app.py** — Original (PDF only)
- **Purpose:** Simple PDF-only RAG
- **Framework:** LangChain
- **Storage:** In-memory
- **Use Case:** Quick prototyping
- **Command:** `uv run streamlit run app.py`

### 2️⃣ **app_tabular.py** — Enhanced (LangChain)
- **Purpose:** PDF + CSV/Parquet with data preview
- **Framework:** LangChain
- **Storage:** In-memory
- **Features:**
  - Data preview and statistics
  - Column selection
  - Row filtering
  - Table-aware chunking
- **Use Case:** Document + table analysis
- **Command:** `uv run streamlit run app_tabular.py`

### 3️⃣ **app_llamaindex.py** — Advanced (LlamaIndex)
- **Purpose:** PDF + CSV/Parquet with persistent storage
- **Framework:** LlamaIndex
- **Storage:** Disk-based (reusable indexes)
- **Features:**
  - All features from app_tabular.py
  - Persistent index caching
  - Index reuse across sessions
- **Use Case:** Production deployments
- **Command:** `uv run streamlit run app_llamaindex.py`

### 4️⃣ **app_hybrid.py** — Hybrid (RECOMMENDED) ⭐
- **Purpose:** CSV/Parquet with search + aggregation
- **Framework:** LangChain + AI Agents
- **Storage:** In-memory
- **Features:**
  - Semantic search via RAG
  - Data aggregation (sum, avg, count, etc.)
  - GroupBy operations
  - AI agent routes to best tool
- **Use Case:** Data analytics with Q&A
- **Command:** `uv run streamlit run app_hybrid.py`

---

## 🛠️ Technical Architecture

### Vector Database
- **FAISS** — In-memory and disk-persisted vector storage
- **Embedding Model:** HuggingFace `all-MiniLM-L6-v2` (384 dimensions, free)

### Language Model
- **LLM:** Ollama (local execution)
- **Default Model:** Llama 3.2 1B
- **Endpoint:** `http://localhost:11434`

### Data Processing
- **CSV Parsing:** Multi-encoding detection with fallback chain
- **Parquet:** PyArrow engine
- **Chunking:** Recursive splitting (800 char chunks, 100 char overlap)
- **Table Awareness:** Row-column relationship preservation

### AI Agents
- **Framework:** LangChain's `create_tool_calling_agent`
- **Prompt:** ReAct (Reasoning + Acting)
- **Tool Selection:** Automatic LLM-based routing

---

## 🧪 Testing & Validation

### Test Suite (53 total tests, all passing)

**Dataset Validation Tests (33 tests)**
- File format validation (CSV, Parquet)
- Multi-encoding support (UTF-8, Latin-1, ISO-8859-1, CP1252)
- Data integrity checks (no null columns, unique headers)
- Edge cases (invalid columns, empty selections, invalid operators)

**Aggregator Tests (20 tests)**
- Basic aggregations: sum, average, min, max, median, count, unique
- GroupBy operations with 3 functions
- Filter + aggregate combinations
- Statistics and metadata retrieval
- Error handling (non-existent columns, type mismatches, no matches)

### Running Tests
```bash
# Aggregation tests
pytest test_aggregator.py -v

# Dataset validation tests
pytest test_dataset_validation.py -v

# All tests
pytest -v
```

---

## 📊 Data Support Matrix

| Capability | CSV | Parquet | PDF |
|-----------|-----|---------|-----|
| **Semantic Search** | ✅ | ✅ | ✅ |
| **Data Preview** | ✅ | ✅ | ❌ |
| **Column Selection** | ✅ | ✅ | ❌ |
| **Data Filtering** | ✅ | ✅ | ❌ |
| **Aggregations** | ✅ (hybrid only) | ✅ (hybrid only) | ❌ |
| **Max File Size** | 200 MB | 200 MB | 200 MB |
| **Multi-Encoding** | ✅ | ❌ | ❌ |
| **Persistent Storage** | ✅ (llamaindex only) | ✅ (llamaindex only) | ✅ (llamaindex only) |

---

## 🔐 Privacy & Security

- ✅ **100% Private** — All processing happens locally
- ✅ **No Cloud Calls** — Ollama runs on your machine
- ✅ **No External APIs** — HuggingFace embeddings can run locally with ONNX
- ✅ **Data Stays Local** — Files never leave your computer
- ✅ **Open Source** — Full transparency on what's happening

---

## ⚙️ Configuration

### Environment Variables (Optional)

```bash
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Optional: GPU acceleration
OLLAMA_NUM_GPU=1
```

### File Limits
- **Max File Size:** 200 MB (configurable in `data_loader.py`)
- **Max Chunk Size:** 800 characters (configurable in `data_loader.py`)
- **Chunk Overlap:** 100 characters (configurable in `data_loader.py`)

---

## 🚀 Usage Examples

### Example 1: Semantic Search
```
User Query: "Show me all employees in the Sales department"
System:
  1. Embeds query using HuggingFace model
  2. Searches FAISS vector database
  3. Retrieves top-K matching rows
  4. Passes to LLM with RAG context
  5. Returns: Formatted employee list with source rows
```

### Example 2: Data Aggregation
```
User Query: "What is the average salary?"
System:
  1. LLM recognizes aggregation query
  2. Calls average_column("Salary") tool
  3. Pandas calculates mean
  4. Returns: Single numeric value (e.g., 85,000)
```

### Example 3: GroupBy Analysis
```
User Query: "Average salary by department?"
System:
  1. LLM recognizes groupby query
  2. Calls groupby_average("Salary", "Department") tool
  3. Returns: {HR: 60000, IT: 95000, Sales: 75000, ...}
```

### Example 4: Filter + Aggregate
```
User Query: "What is the average salary for senior employees?"
System:
  1. LLM recognizes filter+aggregate
  2. Calls filter_and_aggregate() with:
     - column="Salary", operation="average"
     - filter_column="Title", filter_value="Senior"
  3. Returns: Aggregated value for filtered subset
```

---

## 📈 Performance

### Typical Response Times
- **Embeddings:** ~100-200ms (first time, cached after)
- **Vector Search:** ~10-50ms
- **LLM Response:** ~1-5 seconds (depends on query complexity)
- **Aggregation:** ~5-20ms (direct pandas operation)

### Memory Usage
- **Base:** ~500 MB (LLM, embeddings, libraries)
- **Per File:** ~1-2x file size (embeddings + FAISS index)
- **Session State:** ~50-100 MB per active session

---

## 🐛 Troubleshooting

### Common Issues

**"Connection refused" on Ollama calls**
- Ensure Ollama server is running: `ollama serve`
- Check endpoint: `http://localhost:11434`

**"CSV encoding error"**
- System automatically tries: UTF-8 → Latin-1 → ISO-8859-1 → CP1252
- If all fail, specify encoding manually in data_loader.py

**"Out of memory" with large files**
- Use `app_llamaindex.py` (better memory management)
- Reduce chunk size in `data_loader.py`
- Split large CSVs into smaller files

**Aggregation returning "no matching rows"**
- Check column name spelling (case-sensitive)
- Verify data type is numeric for sum/average
- Use "Show available columns" in UI first

---

## 🔄 Implementation Details

### Aggregation Module (`data_aggregator.py`)

```python
class DataAggregator:
    @staticmethod
    def sum_column(df: pd.DataFrame, column_name: str) -> float:
        """Sum numeric column values"""
        
    @staticmethod
    def groupby_average(df: pd.DataFrame, column_name: str, group_by: str) -> dict:
        """Average grouped by category"""
        
    @staticmethod
    def filter_and_aggregate(df: pd.DataFrame, column_name: str, 
                            operation: str, filter_column: str, 
                            filter_value: str) -> float:
        """Filter rows then aggregate"""
```

### Tool Creation (`app_hybrid.py`)

```python
def create_aggregation_tools(df: pd.DataFrame):
    @tool
    def sum_column(column_name: str) -> float:
        """Sum a numeric column"""
        return DataAggregator.sum_column(df, column_name)
    
    # ... more tools ...
    
    return [sum_column, average_column, ...]

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# Query automatically routes to correct tool
response = executor.invoke({"input": user_question})
```

---

## 📚 Related Files

- [README.md](README.md) — Installation and setup
- [phase1_brd.md](phase1_brd.md) — Original business requirements
- [test_aggregator.py](test_aggregator.py) — Aggregation test suite
- [test_dataset_validation.py](test_dataset_validation.py) — Data validation tests
- [data_aggregator.py](data_aggregator.py) — Aggregation implementation
- [app_hybrid.py](app_hybrid.py) — Hybrid app with agents

---

## ✨ Future Enhancements

- [ ] Advanced statistics (percentiles, quartiles, correlation)
- [ ] Time-series aggregations (rolling avg, cumulative sum)
- [ ] Multi-file joins across datasets
- [ ] Custom formula support
- [ ] Caching for repeated queries
- [ ] Export results to CSV/Excel
- [ ] Real-time data source integration
- [ ] Visualization support (charts, graphs)

---

## 📝 License & Attribution

This project uses:
- **LangChain** — LLM orchestration framework
- **LlamaIndex** — Data indexing framework
- **Ollama** — Local LLM runtime
- **HuggingFace** — Embedding models
- **FAISS** — Vector similarity search
- **Streamlit** — UI framework
- **Pandas** — Data processing
- **PyArrow** — Parquet support

All open-source with MIT/Apache 2.0 licenses.

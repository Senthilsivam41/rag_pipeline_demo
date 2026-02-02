# 🔒 100% Private Local RAG (Retrieval-Augmented Generation)

A fully local, privacy-preserving RAG pipeline that processes PDFs and answers questions using **Ollama** (local LLM) and **HuggingFace embeddings** — all data stays on your machine, no cloud calls required (except during initial setup).

## 📋 What This Code Does

- **Upload PDFs, CSV, or Parquet files** through a Streamlit web interface
- **Embed documents locally** using HuggingFace's `all-MiniLM-L6-v2` model
- **Create a searchable vector database** using FAISS (in-memory)
- **Answer questions** using Ollama's local LLM (Llama 3.2 1B by default)
- **Cite sources** with page numbers from PDFs or row numbers from tables

### Key Features
- ✅ **100% Private** — No data sent to external APIs
- ✅ **Multi-Format Support** — PDF, CSV, and Parquet files
- ✅ **Table-Aware Chunking** — Preserves column-row relationships for tabular data
- ✅ **Data Filtering** — Preview, select columns, and filter before indexing
- ✅ **Free** — Uses open-source models
- ✅ **Fast** — Runs locally on your Mac CPU
- ✅ **Citation-aware** — Shows which pages/rows answers come from

---

## 🛠️ Prerequisites (macOS)

### 1. **Python 3.11+**
Check if installed:
```bash
python3 --version
```

If not installed, install via [Homebrew](https://brew.sh/):
```bash
brew install python@3.11
```

### 2. **Ollama** (Local LLM Runtime)
Download and install from: https://ollama.com/download/mac

Verify installation:
```bash
ollama --version
```

Pull the default model (Llama 3.2 1B):
```bash
ollama pull llama3.2:1b
```

Start Ollama server (runs in background):
```bash
ollama serve
```
It will be available at `http://localhost:11434`

### 3. **UV** (Python Package Manager - Optional but Recommended)
```bash
brew install uv
```

Or use `pip` if you prefer (comes with Python).

### 4. **Git** (Already on macOS, but verify)
```bash
git --version
```

---

## 📦 Installation

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd rag_pipelines
```

### Step 2: Create Virtual Environment
**Using UV (recommended):**
```bash
uv venv .venv
source .venv/bin/activate
```

**Or using Python's venv:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
uv pip install -r pyproject.toml
```

Or with regular pip:
```bash
pip install -e .
```

Additional dependencies for tabular data support:
```bash
uv pip install pandas pyarrow fastparquet
```

This installs:
- `streamlit` — Web UI framework
- `langchain`, `langchain-core`, `langchain-community` — RAG framework
- `langchain-ollama` — Ollama LLM integration
- `faiss-cpu` — Vector database
- `pypdf` — PDF loading
- `langchain-text-splitters` — Document chunking
- `pandas` — Tabular data processing
- `pyarrow`, `fastparquet` — Parquet file support

---

## 🚀 How to Run

### Prerequisites Check:
1. Ollama server is running:
   ```bash
   ollama serve
   ```
   (Run in a separate terminal)

2. Virtual environment is activated:
   ```bash
   source .venv/bin/activate
   ```

### Start the App:

**LangChain version (original - PDF + CSV/Parquet with in-memory storage):**
```bash
uv run streamlit run app_tabular.py
```

**LlamaIndex version (PDF + CSV/Parquet with persistent disk storage):**
```bash
uv run streamlit run app_llamaindex.py
```

**Hybrid RAG + Analytics version (RECOMMENDED - CSV/Parquet with search + aggregation):**
```bash
uv run streamlit run app_hybrid.py
```

Or with regular Python:
```bash
streamlit run app_hybrid.py
```

The app will open in your browser at **`http://localhost:8501`**

### Using the App:

#### Hybrid RAG + Analytics (`app_hybrid.py`):
1. **Upload a CSV or Parquet file**
2. **Review the data preview and statistics**
3. **Select columns** for semantic indexing
4. **Ask questions** about your data
5. **The AI intelligently chooses**:
   - 🔍 **Semantic Search** for "Show me employees in NYC" 
   - 📊 **Aggregation** for "What is the average salary?"
   - 📈 **GroupBy** for "Sales by department"

#### Example Questions:
- Search: "Who has the highest salary?"
- Aggregation: "What is the average age?"
- GroupBy: "Total sales by region?"
- Filter+Agg: "Average salary in IT department?"

---

## 📁 Project Structure

```
rag_pipelines/
├── app.py                        # Original PDF-only Streamlit app
├── app_tabular.py                # LangChain: PDF + CSV/Parquet (in-memory)
├── app_llamaindex.py             # LlamaIndex: PDF + CSV/Parquet (persistent)
├── app_hybrid.py                 # Hybrid: Search + Aggregation with AI Agent
├── data_loader.py                # LangChain data processing module
├── data_loader_llamaindex.py     # LlamaIndex data processing module
├── data_aggregator.py            # Data aggregation (sum, avg, count, groupby)
├── main.py                       # Placeholder/template (not used)
├── test_dataset_validation.py    # Dataset validation tests
├── test_aggregator.py            # Aggregation tests
├── pyproject.toml                # Project dependencies
├── phase1_brd.md                 # Business requirements for tabular data
├── README.md                     # This file
├── llamaindex_storage/           # LlamaIndex persistent storage (created on first run)
└── .venv/                        # Virtual environment (created after setup)
```

### Application Versions:

| Feature | `app.py` | `app_tabular.py` (LangChain) | `app_llamaindex.py` (LlamaIndex) | `app_hybrid.py` (Hybrid) |
|---------|----------|-----|-----|-----|
| **PDF Support** | ✅ | ✅ | ✅ | ❌ |
| **CSV Support** | ❌ | ✅ | ✅ | ✅ |
| **Parquet Support** | ❌ | ✅ | ✅ | ✅ |
| **Data Preview** | ❌ | ✅ | ✅ | ✅ |
| **Column Selection** | ❌ | ✅ | ✅ | ✅ |
| **Data Filtering** | ❌ | ✅ | ✅ | ✅ |
| **Semantic Search** | ✅ | ✅ | ✅ | ✅ |
| **Aggregations** | ❌ | ❌ | ❌ | ✅ |
| **GroupBy** | ❌ | ❌ | ❌ | ✅ |
| **Smart Agent** | ❌ | ❌ | ❌ | ✅ |
| **Persistent Storage** | ❌ | ❌ | ✅ | ❌ |
| **Framework** | LangChain | LangChain | LlamaIndex | LangChain |

### File Descriptions:

- **`app.py`** — Original Streamlit app (PDF only, LangChain)
  - Simple and lightweight

- **`app_tabular.py`** — Enhanced Streamlit app (LangChain)
  - Supports PDF, CSV, and Parquet files
  - Table-aware chunking for structured data
  - Good for quick demos

- **`app_llamaindex.py`** — Advanced Streamlit app (LlamaIndex)
  - All features of LangChain version
  - Persistent index storage on disk
  - Best for production use with multiple files

- **`app_hybrid.py`** — Hybrid Search + Analytics (NEW - RECOMMENDED)
  - CSV/Parquet only (optimized for tabular data)
  - **AI Agent chooses** between search and aggregation
  - Supports: sum, avg, min, max, median, count, groupby
  - Best for data analysis with Q&A

- **`data_loader.py`** — LangChain data processing module
  - File validation, CSV/Parquet loading
  - Table-aware chunk creation

- **`data_loader_llamaindex.py`** — LlamaIndex data processing module
  - All features of `data_loader.py`
  - Persistent index save/load

- **`data_aggregator.py`** — Data aggregation module (NEW)
  - 9 aggregation functions: sum, avg, min, max, median, count, unique
  - GroupBy operations
  - Filter + aggregate combinations
  - Used by `app_hybrid.py`

---

## ⚙️ Configuration

### Change the Local Model:
Edit line 65 or 88 in `app_tabular.py`:
```python
llm = ChatOllama(model="llama3.2:1b", temperature=0)
```

Available models (pull them first):
```bash
ollama pull llama2
ollama pull mistral
ollama pull neural-chat
```

### Adjust Chunk Size (PDF):
Edit line 50 in `app_tabular.py`:
```python
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
```
- Larger chunks = more context, slower search
- Smaller chunks = less context, faster search

### Adjust Table Chunk Format:
Edit the `create_table_aware_chunks()` method in `data_loader.py` to customize how rows are converted to text:
```python
chunk_text = f"Row {idx + 1}: " + ", ".join([f"{col}: {row[col]}" for col in columns])
```

### Change Temperature:
`temperature=0` → Deterministic (same answer every time)
`temperature=1` → Creative/varied answers

---

## 🎯 Tabular Data Features (CSV/Parquet)

### FR-1: File Validation
- ✅ Supported formats: `.csv`, `.parquet`, `.pq`
- ✅ Max file size: **200 MB**
- ✅ CSV delimiter: **Comma-separated only**

### FR-2: Data Processing & Filtering
- ✅ Data preview: Top 5 rows displayed
- ✅ Column selection: Choose specific columns for indexing
- ✅ Pre-index filtering: Filter rows before creating vector store

### FR-3: RAG Logic (Indexing & Retrieval)
- ✅ Table-aware chunking: Each row includes column names (e.g., `Name: John, Age: 30, City: NYC`)
- ✅ Parquet efficiency: Uses PyArrow engine for memory-efficient handling up to 200MB

---

## 🔀 LangChain vs LlamaIndex Comparison

### Architecture
| Aspect | LangChain | LlamaIndex |
|--------|-----------|-----------|
| **Primary Use** | General LLM orchestration | Document indexing & retrieval |
| **Index Storage** | In-memory (FAISS) | Disk-based (persistent) |
| **Query Engine** | Chains & Retrievers | Query engines with memory |
| **Learning Curve** | Moderate | Steep (more features) |

### Features
| Feature | LangChain | LlamaIndex |
|---------|-----------|-----------|
| **Chains** | ✅ Full control | ⚠️ Limited |
| **Document Loading** | Limited | ✅ Comprehensive |
| **Indexing** | Basic | ✅ Advanced (tree, graph) |
| **Query Engine** | Simple retrieval | ✅ Advanced reasoning |
| **Index Persistence** | Manual | ✅ Built-in |
| **Multi-file Management** | Complex | ✅ Built-in |
| **Memory Management** | Manual | ✅ Automatic |

### When to Use

**Use LangChain (`app_tabular.py`) if:**
- You need full control over chains and prompts
- You're combining LLMs with other tools
- You want a simpler, lightweight solution
- You're building custom workflows
- Data only needs to exist for one session

**Use LlamaIndex (`app_llamaindex.py`) if:**
- You want persistent, reusable indexes
- You need advanced retrieval strategies
- You're building a document management system
- You want automatic memory optimization
- You plan to index many documents over time

### Performance Comparison

| Metric | LangChain | LlamaIndex |
|--------|-----------|-----------|
| **Startup Time** | Fast | Medium |
| **Indexing Speed** | Fast | Medium |
| **Query Latency** | 2-4s | 2-5s |
| **Memory Usage** | Low (session-only) | Medium (persistent) |
| **Disk Usage** | ~1MB | 50-100MB (per index) |

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution:** Make sure virtual environment is activated:
```bash
source .venv/bin/activate
```

### Issue: "Connection refused" when running the app
**Solution:** Ollama server is not running. In another terminal:
```bash
ollama serve
```

### Issue: App is slow
**Solution:** 
- You're using a 1B model (lightweight). For better quality, use a larger model:
  ```bash
  ollama pull llama2
  ```
  Then update `app.py` line 55 to `model="llama2"`
- Close other applications to free up RAM

### Issue: PDF not uploading
**Solution:** 
- Ensure the PDF is under 100MB
- Try a different PDF file to test
- Check browser console for errors (F12)

---

## 📊 Performance Notes

On a Mac with M1/M2/M3 (Apple Silicon):
- **Indexing:** ~5-10 seconds per 10-page PDF
- **Query response:** ~2-5 seconds per question
- **RAM usage:** ~2-3GB while running

On Intel Mac:
- Indexing and queries will be slower (3-4x)
- Consider using smaller models or upgrading RAM

---

## 🔐 Privacy & Security

- ✅ All processing happens locally
- ✅ PDFs are temporarily stored in `temp.pdf` (deleted after upload)
- ✅ Vector embeddings stay in memory (`temp.pkl` after indexing)
- ✅ No data sent to OpenAI, Google, or any cloud service
- ✅ No telemetry or usage tracking

---

## 🚀 Next Steps

1. **Try with your own PDFs** — test with documents from work or research
2. **Experiment with different models** — see which speed/quality tradeoff works best
3. **Integrate into production** — wrap this in an API or use in other applications
4. **Fine-tune prompts** — edit the `system_prompt` in `app.py` for better results

---

## 📚 Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [HuggingFace Embeddings](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

---

## 📝 License

This project is open source. See LICENSE file for details.

---

## 💬 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review error messages in the terminal
3. Check browser console (F12) for UI errors
4. Ensure all prerequisites are properly installed

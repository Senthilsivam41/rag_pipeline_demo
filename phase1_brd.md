Building a **RAG pipeline for tabular data** (CSV and Parquet) requires different handling than standard PDFs. To ensure the AI doesn't lose the relationship between headers and data, we use "Table-Aware Chunking."

Below is the **Business Requirement Document (BRD)** in Markdown format, ready for your records or stakeholder review.

---

# Business Requirement Document (BRD)

## Project: Tabular Data Support for RAG Pipeline

### 1. Document Overview

* **Project Name:** Enhanced Tabular RAG (ET-RAG)
* **Version:** 1.0
* **Status:** Draft
* **Date:** January 31, 2026

---

### 2. Executive Summary

The objective of this enhancement is to upgrade the existing PDF RAG pipeline to support structured data formats (**CSV** and **Parquet**). This will enable business users to perform natural language queries on datasets, such as financial logs or customer records, while maintaining strict local data privacy and high retrieval accuracy.

---

### 3. Business Objectives

* **Unified Ingestion:** Provide a single interface for PDF, CSV, and Parquet files.
* **Context Preservation:** Ensure the LLM understands column-row relationships (Table-Awareness).
* **Data Control:** Allow users to filter or "clean" the data before it is indexed into the vector database.
* **Zero-Cost Operation:** Utilize local LLMs and embedding models to eliminate API overhead.

---

### 4. Functional Requirements

#### 4.1 File Upload & Validation

| ID | Requirement | Specification |
| --- | --- | --- |
| **FR-1.1** | **Supported Formats** | The system must accept `.csv` and `.parquet` file extensions. |
| **FR-1.2** | **File Size Limit** | Maximum file size is strictly capped at **200 MB**. |
| **FR-1.3** | **Delimiter Policy** | For CSV files, only **comma-separated** values are permitted. Semi-colon or Tab-separated files must be rejected. |

#### 4.2 Data Processing & Filtering

| ID | Requirement | Specification |
| --- | --- | --- |
| **FR-2.1** | **Data Preview** | Upon upload, the UI must display a **top-5 row preview** of the data. |
| **FR-2.2** | **Column Selection** | Users must be able to select specific columns for indexing to save memory and improve AI focus. |
| **FR-2.3** | **Pre-Index Filtering** | Users should be able to filter data (e.g., "Only keep rows where Sales > 1000") before the RAG pipeline starts. |

#### 4.3 RAG Logic (Indexing & Retrieval)

| ID | Requirement | Specification |
| --- | --- | --- |
| **FR-3.1** | **Table-Aware Chunking** | Each row must be converted into a text chunk that includes the header names (e.g., `Column1: Value1, Column2: Value2`). |
| **FR-3.2** | **Parquet Efficiency** | Use `FastParquet` or `PyArrow` engines to handle the 200MB threshold without crashing local system RAM. |

---

### 5. Non-Functional Requirements

* **Privacy:** All tabular data must be processed in a local environment; no data should be sent to third-party cloud APIs (OpenAI/Claude).
* **Usability:** The interface must be built using Streamlit with clear progress bars during the 200MB file indexing phase.
* **Performance:** The "Search-to-Answer" latency should not exceed 5 seconds for files up to 100,000 rows.

---

### 6. Technical Constraints

* **Language:** Python 3.10+
* **Library:** LangChain / LangChain-Community
* **Local LLM Engine:** Ollama (Recommended: `Llama-3.2-3B` or `Gemma-2B`)
* **Vector Store:** FAISS (Local)

---

### 7. Next Step

Would you like me to provide the **Python code update** for your `app.py` that specifically implements the **CSV/Parquet** loading and the **200MB size validation**?
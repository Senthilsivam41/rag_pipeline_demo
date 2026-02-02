"""Local RAG using LlamaIndex with Ollama and HuggingFace.

This Streamlit app allows users to upload PDFs, CSV, or Parquet files and ask questions
using LlamaIndex RAG pipeline with local Ollama LLM and HuggingFace embeddings.

Key differences from LangChain version:
- Uses LlamaIndex for indexing and retrieval
- Persistent index storage on disk
- Ability to reuse previously indexed documents
- Built-in query engine with memory management
"""
# pylint: disable=import-error

import warnings
import streamlit as st
from pathlib import Path

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from data_loader_llamaindex import LlamaIndexDataLoader
from shared_ui import (
    display_data_summary,
    display_column_selector,
    display_filter_section,
    display_chat_history,
    display_user_message,
    display_assistant_response,
)

# Suppress Pydantic V1 compatibility warning with Python 3.14
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# --- Page Config ---
st.set_page_config(page_title="LlamaIndex Local RAG", page_icon="🦙", layout="wide")
st.title("🦙 LlamaIndex Private RAG")
st.markdown("All data stays on your machine. Powered by LlamaIndex + Ollama + HuggingFace.")
st.markdown("**Supported formats:** PDF | CSV | Parquet | **Persistent Indexes**")


def initialize_llm_and_embeddings():
    """Initialize LLM and embedding model."""
    llm = Ollama(model="llama3.2:1b", base_url="http://localhost:11434", temperature=0)
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    return llm, embed_model


def process_pdf_llamaindex(file):
    """Load and index a PDF using LlamaIndex.

    Args:
        file: Uploaded PDF file

    Returns:
        VectorStoreIndex or None
    """
    try:
        # Save temporarily
        with open("temp.pdf", "wb") as f:
            f.write(file.getbuffer())

        # Load PDF documents
        documents = LlamaIndexDataLoader.create_pdf_documents("temp.pdf")
        st.info(f"📄 Loaded {len(documents)} document chunks from PDF")

        # Build and save index
        index = LlamaIndexDataLoader.build_index(
            documents,
            index_name=file.name.replace(".pdf", "")
        )
        st.success("✅ PDF indexed and saved!")
        return index
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        return None


def process_tabular_llamaindex(file):
    """Load and index tabular data using LlamaIndex.

    Args:
        file: Uploaded CSV or Parquet file

    Returns:
        VectorStoreIndex or None
    """
    try:
        # Validate file
        LlamaIndexDataLoader.validate_file(file)

        # Load data
        dataframe = LlamaIndexDataLoader.load_data(file)

        # Show preview and summary
        col1, col2 = st.columns(2)
        with col1:
            LlamaIndexDataLoader.preview_data(dataframe)
        with col2:
            summary = LlamaIndexDataLoader.get_data_summary(dataframe)
            display_data_summary(dataframe, summary)

        # Column selection
        all_columns = LlamaIndexDataLoader.get_columns(dataframe)
        selected_columns = display_column_selector(all_columns)
        dataframe = LlamaIndexDataLoader.select_columns(dataframe, selected_columns)

        # Pre-index filtering
        dataframe = display_filter_section(
            dataframe,
            LlamaIndexDataLoader.get_columns,
            LlamaIndexDataLoader.apply_filter
        )

        # Create documents and build index
        st.info(f"📍 Indexing {len(dataframe)} rows...")
        documents = LlamaIndexDataLoader.create_table_aware_documents(dataframe)

        index = LlamaIndexDataLoader.build_index(
            documents,
            index_name=file.name.replace(".csv", "").replace(".parquet", "").replace(".pq", "")
        )
        st.success(f"✅ Indexed {len(documents)} rows and saved!")
        return index

    except ValueError as e:
        st.error(str(e))
        return None
    except Exception as e:
        st.error(f"❌ Error processing data: {str(e)}")
        return None


# --- Sidebar ---
with st.sidebar:
    st.header("📁 Upload & Manage")
    tab1, tab2 = st.tabs(["Upload", "Saved Indexes"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload your file (PDF, CSV, or Parquet)",
            type=["pdf", "csv", "parquet", "pq"]
        )

    with tab2:
        st.subheader("💾 Saved Indexes")
        saved_indexes = LlamaIndexDataLoader.list_saved_indexes()
        if saved_indexes:
            st.write("**Available indexes:**")
            for idx in saved_indexes:
                st.write(f"- {idx}")
        else:
            st.info("No saved indexes yet")

    st.divider()
    st.info("🔒 Using Ollama + HuggingFace - No API keys needed!")
    st.info("💾 Indexes are automatically persisted to disk")


# --- Main Chat Interface ---
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()

    # Process file based on type
    if file_ext == "pdf":
        if "query_engine" not in st.session_state:
            with st.spinner("📄 Indexing PDF with LlamaIndex..."):
                index = process_pdf_llamaindex(uploaded_file)
                if index:
                    llm, embed_model = initialize_llm_and_embeddings()
                    st.session_state.query_engine = index.as_query_engine(
                        llm=llm,
                        embed_model=embed_model
                    )

    elif file_ext in {"csv", "parquet", "pq"}:
        if "query_engine" not in st.session_state:
            with st.spinner("📊 Indexing data with LlamaIndex..."):
                index = process_tabular_llamaindex(uploaded_file)
                if index:
                    llm, embed_model = initialize_llm_and_embeddings()
                    st.session_state.query_engine = index.as_query_engine(
                        llm=llm,
                        embed_model=embed_model
                    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    display_chat_history(st.session_state.messages)

    # Chat input
    if user_input := st.chat_input("Ask about your data"):
        if "query_engine" not in st.session_state:
            st.warning("⚠️ Please wait for indexing to complete before asking questions.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            display_user_message(user_input)

            with st.chat_message("assistant"):
                try:
                    response = st.session_state.query_engine.query(user_input)
                    answer = str(response)

                    # Extract source nodes for citations
                    # pylint: disable=invalid-name
                    sources_text = ""
                    if hasattr(response, "source_nodes") and response.source_nodes:
                        source_list = [
                            f"Node {i}: {node.metadata.get('row_number', 'N/A')}"
                            for i, node in enumerate(response.source_nodes[:3])
                        ]
                        sources_text = "\n\n📍 **Sources:** " + " | ".join(source_list)

                    full_answer = answer + sources_text
                    st.markdown(answer)
                    if sources_text:
                        st.caption(sources_text)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_answer}
                    )
                except Exception as e:
                    st.error(f"❌ Query error: {str(e)}")

else:
    st.info("👈 Upload a PDF, CSV, or Parquet file to get started!")
    st.markdown("""
    ### Features:
    - 🦙 **LlamaIndex Framework** — Advanced indexing and retrieval
    - 💾 **Persistent Storage** — Indexes saved on disk for reuse
    - 📊 **Multi-Format** — PDF, CSV, Parquet support
    - 🔒 **100% Private** — All processing local
    - 🚀 **Fast Queries** — Sub-5 second response times
    """)

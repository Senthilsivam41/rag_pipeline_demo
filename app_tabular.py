"""Local RAG (Retrieval-Augmented Generation) application using Ollama and HuggingFace.

This Streamlit app allows users to upload PDFs, CSV, or Parquet files and ask questions
using a local, privacy-preserving RAG pipeline powered by Ollama LLM and HuggingFace embeddings.
"""
# pylint: disable=import-error

import warnings
import streamlit as st
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from data_loader import DataLoader
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
st.set_page_config(page_title="Local Private RAG", page_icon="🔒", layout="wide")
st.title("🔒 100% Private Local RAG")
st.markdown("All data stays on your machine. Powered by Ollama + HuggingFace.")
st.markdown("**Supported formats:** PDF | CSV | Parquet")

# --- Logic: Process PDF ---
def process_pdf_local(file):
    """Load and process a PDF file into a searchable vector store.

    Args:
        file: Uploaded file object from Streamlit

    Returns:
        Retriever object for searching the document
    """
    with open("temp.pdf", "wb") as f:
        f.write(file.getbuffer())

    loader = PyPDFLoader("temp.pdf")
    docs = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # Use FREE local embeddings (Runs on your CPU)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create Local Vector Store
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    return vectorstore.as_retriever()


# --- Logic: Process CSV/Parquet ---
def process_tabular_data(file):
    """Load and process CSV/Parquet file into a searchable vector store.

    Args:
        file: Uploaded file object from Streamlit

    Returns:
        Tuple of (Retriever object, DataFrame)
    """
    # Validate file
    try:
        DataLoader.validate_file(file)
    except ValueError as e:
        st.error(str(e))
        return None, None

    # Load data
    try:
        dataframe = DataLoader.load_data(file)
    except ValueError as e:
        st.error(str(e))
        return None, None

    # Show preview and summary
    col1, col2 = st.columns(2)
    with col1:
        DataLoader.preview_data(dataframe)
    with col2:
        summary = DataLoader.get_data_summary(dataframe)
        display_data_summary(dataframe, summary)

    # Column selection
    all_columns = DataLoader.get_columns(dataframe)
    selected_columns = display_column_selector(all_columns)
    dataframe = DataLoader.select_columns(dataframe, selected_columns)

    # Pre-index filtering
    dataframe = display_filter_section(
        dataframe,
        DataLoader.get_columns,
        DataLoader.apply_filter
    )
    st.success(f"✅ Filtered to {len(dataframe)} rows")

    # Create table-aware chunks and build vector store
    st.info(f"📍 Indexing {len(dataframe)} rows...")
    try:
        chunks = DataLoader.create_table_aware_chunks(dataframe)
        # Convert chunks to Document objects for FAISS
        documents = [Document(page_content=chunk) for chunk in chunks]

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings)
        st.success(f"✅ Successfully indexed {len(chunks)} rows!")
        return vectorstore.as_retriever(), dataframe
    except Exception as e:
        st.error(f"❌ Error processing data: {str(e)}")
        return None, None


# --- Sidebar ---
with st.sidebar:
    st.header("📁 Upload")
    uploaded_file = st.file_uploader(
        "Upload your file (PDF, CSV, or Parquet)",
        type=["pdf", "csv", "parquet", "pq"]
    )
    st.divider()
    st.info("Using Llama-3.2-1B (Local) - No API keys needed!")
    st.info("Privacy: All data stays on your machine 🔐")

# --- Chat Interface ---
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()

    # Process file based on type
    if file_ext == "pdf":
        if "rag_chain" not in st.session_state:
            with st.spinner("📄 Indexing PDF locally..."):
                retriever = process_pdf_local(uploaded_file)
                if retriever is None:
                    st.stop()

                # Use Local Ollama LLM
                llm = ChatOllama(model="llama3.2:1b", temperature=0)

                # pylint: disable=invalid-name
                system_message = "Answer based ONLY on the context: {context}"
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message), ("human", "{input}")
                ])

                qa_chain = create_stuff_documents_chain(llm, prompt_template)
                st.session_state.rag_chain = create_retrieval_chain(retriever, qa_chain)

    elif file_ext in {"csv", "parquet", "pq"}:
        if "rag_chain" not in st.session_state:
            with st.spinner("📊 Indexing tabular data locally..."):
                retriever, _ = process_tabular_data(uploaded_file)
                if retriever is None:
                    st.stop()

                # Use Local Ollama LLM
                llm = ChatOllama(model="llama3.2:1b", temperature=0)

                # pylint: disable=invalid-name
                system_message = (
                    "You are an expert data analyst. "
                    "Answer questions based ONLY on the provided data. "
                    "Context: {context}"
                )
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_message), ("human", "{input}")
                ])

                qa_chain = create_stuff_documents_chain(llm, prompt_template)
                st.session_state.rag_chain = create_retrieval_chain(retriever, qa_chain)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat history
    display_chat_history(st.session_state.messages)

    # Chat input
    if user_input := st.chat_input("Ask about your data"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        display_user_message(user_input)

        with st.chat_message("assistant"):
            res = st.session_state.rag_chain.invoke({"input": user_input})
            answer = res["answer"]

            # Show Citations
            # pylint: disable=invalid-name
            pages = {str(doc.metadata.get("page", 0) + 1) for doc in res["context"]}
            citation = "\n\n📍 **Sources:** Pages " + ", ".join(sorted(pages))

            display_assistant_response(answer, citation)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer + citation}
            )

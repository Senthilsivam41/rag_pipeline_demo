import streamlit as st
import os
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- Page Config ---
st.set_page_config(page_title="Local Private RAG", page_icon="🔒")
st.title("🔒 100% Private Local RAG")
st.markdown("All data stays on your machine. Powered by Ollama + HuggingFace.")

# --- Logic: Process PDF ---
@st.cache_resource # Cache so it doesn't re-embed every time you ask a question
def process_pdf_local(file):
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

# --- Sidebar ---
with st.sidebar:
    st.header("Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    st.info("Using Llama-3.2-1B (Local)")

# --- Chat Interface ---
if uploaded_file:
    if "rag_chain" not in st.session_state:
        with st.spinner("Indexing PDF locally..."):
            retriever = process_pdf_local(uploaded_file)
            
            # Use Local Ollama LLM
            llm = ChatOllama(model="llama3.2:1b", temperature=0)
            
            system_prompt = "Answer based ONLY on the context: {context}"
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", system_prompt), ("human", "{input}")
            ])
            
            qa_chain = create_stuff_documents_chain(llm, prompt_template)
            st.session_state.rag_chain = create_retrieval_chain(retriever, qa_chain)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask about your PDF"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            res = st.session_state.rag_chain.invoke({"input": user_input})
            answer = res["answer"]
            
            # Show Citations
            pages = {str(doc.metadata.get("page", 0) + 1) for doc in res["context"]}
            citation = f"\n\n📍 **Sources:** Pages " + ", ".join(sorted(pages))
            
            st.markdown(answer)
            st.caption(citation)
            st.session_state.messages.append({"role": "assistant", "content": answer + citation})
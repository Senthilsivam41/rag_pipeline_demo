"""LlamaIndex-based data loading and processing module.

This module handles:
- PDF and tabular data indexing using LlamaIndex
- File validation (format, size, delimiter)
- Data preview and column selection
- Table-aware document creation
- Persistent index storage
"""
# pylint: disable=import-error

import os
import pandas as pd
import streamlit as st
from pathlib import Path

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

# Constants
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB
SUPPORTED_FORMATS = {".csv", ".parquet", ".pq", ".pdf"}
CSV_DELIMITER = ","
PREVIEW_ROWS = 5
INDEX_STORAGE_DIR = "./llamaindex_storage"


class LlamaIndexDataLoader:
    """Handles loading and processing of documents using LlamaIndex."""

    @staticmethod
    def validate_file(uploaded_file) -> bool:
        """Validate file format, size, and delimiter.

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValueError: If file is invalid with descriptive message
        """
        # Check file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"❌ Unsupported format: {file_ext}. "
                f"Supported: {', '.join(SUPPORTED_FORMATS)}"
            )

        # Check file size
        file_size = len(uploaded_file.getbuffer())
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"❌ File too large: {size_mb:.1f} MB. "
                f"Maximum: {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB"
            )

        # For CSV, validate delimiter on first few lines
        if file_ext == ".csv":
            try:
                uploaded_file.seek(0)
                first_line = uploaded_file.readline().decode("utf-8")
                if CSV_DELIMITER not in first_line:
                    raise ValueError(
                        f"❌ Invalid CSV delimiter. Only comma-separated files are supported."
                    )
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    first_line = uploaded_file.readline().decode("latin-1")
                    if CSV_DELIMITER not in first_line:
                        raise ValueError(
                            f"❌ Invalid CSV delimiter. Only comma-separated files are supported."
                        )
                except Exception as e:
                    raise ValueError(
                        f"❌ CSV encoding error. Please ensure UTF-8 or Latin-1 encoding: {str(e)}"
                    )

        return True

    @staticmethod
    def load_data(uploaded_file) -> pd.DataFrame:
        """Load CSV or Parquet file into a DataFrame.

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            pd.DataFrame: Loaded data
        """
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        try:
            uploaded_file.seek(0)
            if file_ext == ".csv":
                encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-16"]
                dataframe = None

                for encoding in encodings:
                    try:
                        uploaded_file.seek(0)
                        dataframe = pd.read_csv(
                            uploaded_file,
                            delimiter=CSV_DELIMITER,
                            encoding=encoding
                        )
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue

                if dataframe is None:
                    raise ValueError(
                        "❌ Could not decode CSV file. Try saving with UTF-8 encoding."
                    )

            elif file_ext in {".parquet", ".pq"}:
                dataframe = pd.read_parquet(uploaded_file, engine="pyarrow")
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            if dataframe.empty:
                raise ValueError("❌ File is empty. Please upload a file with data.")

            return dataframe
        except Exception as e:
            raise ValueError(f"❌ Error loading file: {str(e)}")

    @staticmethod
    def preview_data(dataframe: pd.DataFrame) -> None:
        """Display a preview of the data in Streamlit.

        Args:
            dataframe: Data to preview
        """
        st.subheader(f"📊 Data Preview ({len(dataframe)} rows, {len(dataframe.columns)} columns)")
        preview_df = dataframe.head(PREVIEW_ROWS)
        st.dataframe(preview_df, width="stretch")

    @staticmethod
    def get_columns(dataframe: pd.DataFrame) -> list:
        """Get list of column names.

        Args:
            dataframe: Data to extract columns from

        Returns:
            list: Column names
        """
        return list(dataframe.columns)

    @staticmethod
    def select_columns(dataframe: pd.DataFrame, columns: list) -> pd.DataFrame:
        """Filter DataFrame to selected columns.

        Args:
            dataframe: Original data
            columns: List of columns to keep

        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if not columns:
            return dataframe
        return dataframe[columns]

    @staticmethod
    def apply_filter(dataframe: pd.DataFrame, filter_config: dict) -> pd.DataFrame:
        """Apply pre-index filtering to the data.

        Args:
            dataframe: Original data
            filter_config: Filter configuration dict

        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if not filter_config or not filter_config.get("column"):
            return dataframe

        column = filter_config.get("column")
        operator = filter_config.get("operator", "==")
        value = filter_config.get("value")

        if column not in dataframe.columns:
            raise ValueError(f"❌ Column '{column}' not found in data.")

        try:
            if operator == "==":
                return dataframe[dataframe[column] == value]
            elif operator == ">":
                return dataframe[dataframe[column] > value]
            elif operator == "<":
                return dataframe[dataframe[column] < value]
            elif operator == ">=":
                return dataframe[dataframe[column] >= value]
            elif operator == "<=":
                return dataframe[dataframe[column] <= value]
            elif operator == "!=":
                return dataframe[dataframe[column] != value]
            else:
                raise ValueError(f"❌ Unsupported operator: {operator}")
        except (TypeError, KeyError) as e:
            raise ValueError(f"❌ Error applying filter: {str(e)}")

    @staticmethod
    def create_table_aware_documents(dataframe: pd.DataFrame) -> list:
        """Convert table rows into LlamaIndex Documents with table-aware context.

        Args:
            dataframe: Data to convert

        Returns:
            list: Document objects
        """
        documents = []
        columns = dataframe.columns.tolist()

        row_counter = 0
        for idx, row in dataframe.iterrows():
            # pylint: disable=invalid-name
            # Use counter to avoid type issues with idx
            row_counter += 1
            content = f"Row {row_counter}: " + ", ".join(
                [f"{col}: {row[col]}" for col in columns]
            )
            doc = Document(
                text=content,
                metadata={"row_number": row_counter, "source": "tabular_data"}
            )
            documents.append(doc)

        return documents

    @staticmethod
    def create_pdf_documents(file_path: str) -> list:
        """Load PDF documents using LlamaIndex SimpleDirectoryReader.

        Args:
            file_path: Path to PDF file

        Returns:
            list: Document objects
        """
        reader = SimpleDirectoryReader(input_files=[file_path])
        documents = reader.load_data()
        return documents

    @staticmethod
    def build_index(documents: list, index_name: str = "default") -> VectorStoreIndex:
        """Build a VectorStoreIndex from documents.

        Args:
            documents: List of LlamaIndex Document objects
            index_name: Name for storing the index

        Returns:
            VectorStoreIndex: Built index
        """
        # Initialize embeddings and LLM
        embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        llm = Ollama(model="llama3.2:1b", base_url="http://localhost:11434")

        # Create sentence splitter for chunking
        text_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=20,
            separator=" "
        )

        # Build index
        index = VectorStoreIndex.from_documents(
            documents,
            embed_model=embed_model,
            node_parser=text_splitter,
            show_progress=True
        )

        # Save index to disk
        LlamaIndexDataLoader.save_index(index, index_name)

        return index

    @staticmethod
    def save_index(index: VectorStoreIndex, index_name: str) -> None:
        """Persist index to disk.

        Args:
            index: VectorStoreIndex to save
            index_name: Name for the index
        """
        index_path = Path(INDEX_STORAGE_DIR) / index_name
        index_path.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(str(index_path))

    @staticmethod
    def load_index(index_name: str) -> "VectorStoreIndex | None":
        """Load a persisted index from disk.

        Args:
            index_name: Name of the index

        Returns:
            VectorStoreIndex: Loaded index or None if not found
        """
        index_path = Path(INDEX_STORAGE_DIR) / index_name
        if index_path.exists():
            from llama_index.core import StorageContext, load_index_from_storage

            storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
            # Type ignore: load_index_from_storage returns BaseIndex
            # which can be used as VectorStoreIndex
            return load_index_from_storage(storage_context)  # type: ignore
        return None

    @staticmethod
    def get_data_summary(dataframe: pd.DataFrame) -> dict:
        """Generate summary statistics about the data.

        Args:
            dataframe: Data to summarize

        Returns:
            dict: Summary statistics
        """
        return {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "memory_mb": dataframe.memory_usage(deep=True).sum() / (1024 * 1024),
        }

    @staticmethod
    def list_saved_indexes() -> list:
        """List all saved indexes on disk.

        Returns:
            list: Index names
        """
        if not Path(INDEX_STORAGE_DIR).exists():
            return []
        return [d.name for d in Path(INDEX_STORAGE_DIR).iterdir() if d.is_dir()]

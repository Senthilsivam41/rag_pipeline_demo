"""Data loading and processing module for CSV and Parquet files.

This module handles:
- File validation (format, size, delimiter)
- Data preview and column selection
- Table-aware chunking for RAG indexing
- Pre-index filtering capabilities
"""
# pylint: disable=import-error

import os
import pandas as pd
import streamlit as st


# Constants
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB
SUPPORTED_FORMATS = {".csv", ".parquet", ".pq"}
CSV_DELIMITER = ","
PREVIEW_ROWS = 5


class DataLoader:
    """Handles loading and processing of tabular data files."""

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
                # Try common encodings if UTF-8 fails
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

        Raises:
            ValueError: If data cannot be loaded
        """
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        try:
            uploaded_file.seek(0)
            if file_ext == ".csv":
                # Try UTF-8 first, then fallback to common encodings
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
                # Use PyArrow engine for better memory efficiency
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
            filter_config: Filter configuration dict with keys:
                - column: column name
                - operator: "==", ">", "<", ">=", "<=", "!="
                - value: value to compare

        Returns:
            pd.DataFrame: Filtered DataFrame

        Raises:
            ValueError: If filter config is invalid
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
    def create_table_aware_chunks(dataframe: pd.DataFrame) -> list:
        """Convert table rows into table-aware text chunks for RAG.

        Each chunk includes header names to preserve column-row relationships.

        Args:
            dataframe: Data to chunk

        Returns:
            list: Text chunks with column names included
        """
        chunks = []
        columns = dataframe.columns.tolist()
        for idx, row in dataframe.iterrows():
            # Create chunk with header: value pairs
            # pylint: disable=invalid-name
            row_num = int(idx) + 1 if isinstance(idx, int) else 1
            chunk_text = f"Row {row_num}: " + ", ".join(
                [f"{col}: {row[col]}" for col in columns]
            )
            chunks.append(chunk_text)

        return chunks

    @staticmethod
    def get_data_summary(dataframe: pd.DataFrame) -> dict:
        """Generate summary statistics about the data.

        Args:
            dataframe: Data to summarize

        Returns:
            dict: Summary with keys: rows, columns, memory_mb, dtypes
        """
        return {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "memory_mb": dataframe.memory_usage(deep=True).sum() / (1024 * 1024),
            "dtypes": dataframe.dtypes.to_dict(),
        }

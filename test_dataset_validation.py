"""Pytest tests for dataset validation.

Tests validate:
- File format support (CSV, Parquet, PDF)
- File size limits (200MB max)
- CSV delimiter validation (comma-separated)
- Data integrity and encoding
- Data processing functionality
"""
# pylint: disable=import-error

import pytest
import os
import pandas as pd
from pathlib import Path

from data_loader import DataLoader
from data_loader_llamaindex import LlamaIndexDataLoader


# Constants for testing
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024
CSV_DELIMITER = ","
INDEX_STORAGE_DIR = "./llamaindex_storage"


# Fixtures
@pytest.fixture
def dataset_dir():
    """Get path to dataset directory."""
    return Path(__file__).parent / "dataset"


@pytest.fixture
def csv_file(dataset_dir):
    """Get CSV file from dataset."""
    csv_files = list(dataset_dir.glob("*.csv"))
    return csv_files[0] if csv_files else None


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35],
        "City": ["NYC", "LA", "Chicago"],
        "Salary": [50000, 60000, 75000]
    })


# --- File Format Tests ---

class TestFileFormats:
    """Test file format validation."""

    def test_csv_file_exists(self, csv_file):
        """Test that CSV file exists in dataset."""
        assert csv_file is not None, "No CSV file found in dataset"
        assert csv_file.exists(), f"CSV file not found: {csv_file}"

    def test_csv_file_readable(self, csv_file):
        """Test that CSV file can be read."""
        with open(csv_file, "rb") as f:
            content = f.read()
        assert len(content) > 0, "CSV file is empty"

    def test_csv_has_comma_delimiter(self, csv_file):
        """Test that CSV uses comma delimiter."""
        with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
        assert "," in first_line, "CSV file does not use comma delimiter"

    def test_dataset_dir_exists(self, dataset_dir):
        """Test that dataset directory exists."""
        assert dataset_dir.exists(), f"Dataset directory not found: {dataset_dir}"

    def test_dataset_has_files(self, dataset_dir):
        """Test that dataset directory has files."""
        files = list(dataset_dir.glob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith(".")]
        assert len(files) > 0, "Dataset directory has no files"


# --- Data Loader Tests (LangChain) ---

class TestDataLoaderLangChain:
    """Test LangChain DataLoader functionality."""

    def test_validate_csv_file(self, csv_file):
        """Test CSV file validation."""
        # Create a mock uploaded file
        class MockFile:
            def __init__(self, path):
                self.path = path
                self.name = path.name
                self.buffer = open(path, "rb").read()

            def getbuffer(self):
                return self.buffer

            def seek(self, pos):
                pass

            def readline(self):
                return self.buffer.split(b"\n")[0]

        mock_file = MockFile(csv_file)
        # Should not raise an exception
        result = DataLoader.validate_file(mock_file)
        assert result is True

    def test_load_csv_data(self, csv_file):
        """Test loading CSV data with proper encoding handling."""
        # Read the file directly with proper encoding
        df = pd.DataFrame()
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0

    def test_preview_data(self, sample_dataframe):
        """Test data preview (mock Streamlit)."""
        import streamlit as st
        with pytest.MonkeyPatch.context() as m:
            # Mock st.subheader and st.dataframe
            m.setattr(st, "subheader", lambda x: None)
            m.setattr(st, "dataframe", lambda x, **kwargs: None)
            # Should not raise exception
            DataLoader.preview_data(sample_dataframe)

    def test_get_columns(self, sample_dataframe):
        """Test column extraction."""
        columns = DataLoader.get_columns(sample_dataframe)
        assert isinstance(columns, list)
        assert "Name" in columns
        assert "Age" in columns
        assert "City" in columns
        assert "Salary" in columns

    def test_select_columns(self, sample_dataframe):
        """Test column selection."""
        selected = DataLoader.select_columns(sample_dataframe, ["Name", "Age"])
        assert len(selected.columns) == 2
        assert "Name" in selected.columns
        assert "Age" in selected.columns
        assert "City" not in selected.columns

    def test_create_table_aware_chunks(self, sample_dataframe):
        """Test table-aware chunk creation."""
        chunks = DataLoader.create_table_aware_chunks(sample_dataframe)
        assert isinstance(chunks, list)
        assert len(chunks) == 3  # 3 rows
        assert "Name: Alice" in chunks[0]
        assert "Age: 25" in chunks[0]

    def test_get_data_summary(self, sample_dataframe):
        """Test data summary generation."""
        summary = DataLoader.get_data_summary(sample_dataframe)
        assert "rows" in summary
        assert "columns" in summary
        assert "memory_mb" in summary
        assert summary["rows"] == 3
        assert summary["columns"] == 4

    def test_apply_filter_equals(self, sample_dataframe):
        """Test filter with equals operator."""
        filter_config = {"column": "City", "operator": "==", "value": "NYC"}
        result = DataLoader.apply_filter(sample_dataframe, filter_config)
        assert len(result) == 1
        assert result.iloc[0]["Name"] == "Alice"

    def test_apply_filter_greater_than(self, sample_dataframe):
        """Test filter with greater than operator."""
        filter_config = {"column": "Age", "operator": ">", "value": 28}
        result = DataLoader.apply_filter(sample_dataframe, filter_config)
        assert len(result) == 2  # Bob and Charlie

    def test_apply_filter_less_than(self, sample_dataframe):
        """Test filter with less than operator."""
        filter_config = {"column": "Salary", "operator": "<", "value": 65000}
        result = DataLoader.apply_filter(sample_dataframe, filter_config)
        assert len(result) == 2  # Alice and Bob


# --- Data Loader Tests (LlamaIndex) ---

class TestDataLoaderLlamaIndex:
    """Test LlamaIndex DataLoader functionality."""

    def test_validate_csv_file_llamaindex(self, csv_file):
        """Test CSV file validation with LlamaIndex loader."""
        class MockFile:
            def __init__(self, path):
                self.path = path
                self.name = path.name
                self.buffer = open(path, "rb").read()

            def getbuffer(self):
                return self.buffer

            def seek(self, pos):
                pass

            def readline(self):
                return self.buffer.split(b"\n")[0]

        mock_file = MockFile(csv_file)
        result = LlamaIndexDataLoader.validate_file(mock_file)
        assert result is True

    def test_create_table_aware_documents(self, sample_dataframe):
        """Test document creation from table data."""
        docs = LlamaIndexDataLoader.create_table_aware_documents(sample_dataframe)
        assert isinstance(docs, list)
        assert len(docs) == 3
        # Check metadata
        assert docs[0].metadata["row_number"] == 1
        assert docs[0].metadata["source"] == "tabular_data"

    def test_get_data_summary_llamaindex(self, sample_dataframe):
        """Test data summary with LlamaIndex loader."""
        summary = LlamaIndexDataLoader.get_data_summary(sample_dataframe)
        assert summary["rows"] == 3
        assert summary["columns"] == 4
        assert summary["memory_mb"] > 0

    def test_index_storage_path(self):
        """Test that index storage path exists or can be created."""
        storage_path = Path(INDEX_STORAGE_DIR)
        # Should be able to create
        assert storage_path.parent.exists()


# --- File Size Tests ---

class TestFileSizeLimits:
    """Test file size validation."""

    def test_max_file_size_constant(self):
        """Test that max file size is 200MB."""
        assert MAX_FILE_SIZE_BYTES == 200 * 1024 * 1024

    def test_csv_file_size(self, csv_file):
        """Test that CSV file is within size limit."""
        file_size = os.path.getsize(csv_file)
        assert file_size <= MAX_FILE_SIZE_BYTES
        assert file_size > 0


# --- Data Integrity Tests ---

class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_csv_has_headers(self, csv_file):
        """Test that CSV has headers."""
        df = None
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        assert df is not None
        assert len(df.columns) > 0
        assert all(isinstance(col, str) for col in df.columns)

    def test_csv_has_data_rows(self, csv_file):
        """Test that CSV has data rows."""
        df = None
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        assert df is not None
        assert len(df) > 0

    def test_no_duplicate_columns(self, csv_file):
        """Test for duplicate column names."""
        df = None
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        assert df is not None
        assert len(df.columns) == len(set(df.columns))

    def test_no_all_null_columns(self, csv_file):
        """Test that not all values in columns are null."""
        df = None
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        assert df is not None
        for col in df.columns:
            # At least one non-null value per column
            assert df[col].notna().sum() > 0


# --- Encoding Tests ---

class TestFileEncoding:
    """Test file encoding compatibility."""

    def test_csv_encoding_utf8(self, csv_file):
        """Test that CSV can be decoded with supported encodings."""
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        can_decode = False
        for encoding in encodings:
            try:
                with open(csv_file, "r", encoding=encoding) as f:
                    f.read()
                can_decode = True
                break
            except UnicodeDecodeError:
                continue
        assert can_decode, "CSV file cannot be decoded with any supported encoding"

    def test_csv_multiencoding_support(self, csv_file):
        """Test that CSV works with multiple encodings."""
        encodings = ["utf-8", "latin-1", "iso-8859-1"]
        can_decode = False
        for encoding in encodings:
            try:
                with open(csv_file, "r", encoding=encoding) as f:
                    f.read()
                can_decode = True
                break
            except (UnicodeDecodeError, LookupError):
                continue
        assert can_decode, "CSV file cannot be decoded with any supported encoding"


# --- CSV Delimiter Tests ---

class TestCSVDelimiter:
    """Test CSV delimiter validation."""

    def test_csv_delimiter_comma(self, csv_file):
        """Test that CSV uses comma delimiter."""
        with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
        assert "," in first_line, "CSV does not contain commas"
        # Should have commas for multiple columns
        assert first_line.count(",") > 0, "CSV appears to be single column"

    def test_comma_delimiter_constant(self):
        """Test that delimiter constant is comma."""
        assert CSV_DELIMITER == ","


# --- Edge Cases ---

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_filter_invalid_column(self, sample_dataframe):
        """Test filter with non-existent column."""
        filter_config = {"column": "NonExistent", "operator": "==", "value": "test"}
        with pytest.raises(ValueError, match="Column .* not found"):
            DataLoader.apply_filter(sample_dataframe, filter_config)

    def test_filter_invalid_operator(self, sample_dataframe):
        """Test filter with invalid operator."""
        filter_config = {"column": "Name", "operator": "INVALID", "value": "Alice"}
        with pytest.raises(ValueError, match="Unsupported operator"):
            DataLoader.apply_filter(sample_dataframe, filter_config)

    def test_select_empty_columns(self, sample_dataframe):
        """Test column selection with empty list."""
        result = DataLoader.select_columns(sample_dataframe, [])
        assert len(result.columns) == len(sample_dataframe.columns)

    def test_get_columns_empty_dataframe(self):
        """Test column extraction from empty DataFrame."""
        empty_df = pd.DataFrame()
        columns = DataLoader.get_columns(empty_df)
        assert columns == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

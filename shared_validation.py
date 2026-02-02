"""Shared validation utilities for data loading modules.

This module contains common validation functions used across multiple
data loading implementations to avoid code duplication.
"""
import os
import pandas as pd

# Constants
MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB
SUPPORTED_FORMATS_BASIC = {".csv", ".parquet", ".pq"}
SUPPORTED_FORMATS_WITH_PDF = {".csv", ".parquet", ".pq", ".pdf"}
CSV_DELIMITER = ","
PREVIEW_ROWS = 5


def validate_file(uploaded_file, support_pdf: bool = False) -> bool:
    """Validate file format, size, and delimiter.

    This shared validation function is used by both DataLoader and
    LlamaIndexDataLoader to avoid code duplication.

    Args:
        uploaded_file: Streamlit UploadedFile object
        support_pdf: If True, allow PDF files (for LlamaIndex)

    Returns:
        bool: True if valid, False otherwise

    Raises:
        ValueError: If file is invalid with descriptive message
    """
    # Check file extension
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    supported = SUPPORTED_FORMATS_WITH_PDF if support_pdf else SUPPORTED_FORMATS_BASIC
    if file_ext not in supported:
        raise ValueError(
            f"❌ Unsupported format: {file_ext}. "
            f"Supported: {', '.join(supported)}"
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
                    "❌ Invalid CSV delimiter. Only comma-separated files are supported."
                )
        except UnicodeDecodeError as e:
            # Try common encodings if UTF-8 fails
            try:
                uploaded_file.seek(0)
                first_line = uploaded_file.readline().decode("latin-1")
                if CSV_DELIMITER not in first_line:
                    raise ValueError(
                        "❌ Invalid CSV delimiter. Only comma-separated files are supported."
                    ) from e
            except Exception as inner_e:
                raise ValueError(
                    f"❌ CSV encoding error. Please ensure UTF-8 or Latin-1 encoding: {str(inner_e)}"
                ) from inner_e

    return True

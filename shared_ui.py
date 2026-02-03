"""Shared Streamlit UI utilities for RAG applications.

This module contains common UI patterns used across multiple RAG apps
to avoid code duplication.
"""
import streamlit as st


def display_data_summary(_dataframe, summary):
    """Display data summary metrics in Streamlit.

    Args:
        _dataframe: The pandas DataFrame being analyzed (unused)
        summary: Dictionary with 'rows', 'columns', and 'memory_mb' keys
    """
    st.subheader("📈 Data Summary")
    st.metric("Rows", summary["rows"])
    st.metric("Columns", summary["columns"])
    st.metric("Memory (MB)", f"{summary['memory_mb']:.2f}")


def display_column_selector(all_columns, key_prefix="column_selector"):
    """Display column selection interface.

    Args:
        all_columns: List of available column names
        key_prefix: Unique key for this multiselect widget

    Returns:
        List of selected columns
    """
    st.subheader("🎯 Select Columns for Indexing")
    selected_columns = st.multiselect(
        "Choose columns to include:",
        all_columns,
        default=all_columns,
        key=key_prefix
    )
    return selected_columns


def display_filter_section(dataframe, get_columns_func, apply_filter_func):
    """Display optional data filtering interface.

    Args:
        dataframe: The pandas DataFrame to filter
        get_columns_func: Function to get list of column names
        apply_filter_func: Function that applies filter to dataframe

    Returns:
        Filtered dataframe, or original if no filter applied
    """
    with st.expander("🔍 Optional: Filter Data Before Indexing"):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_column = st.selectbox(
                "Column to filter:",
                get_columns_func(dataframe),
                key="filter_column"
            )
        with col2:
            operator = st.selectbox(
                "Operator:",
                ["==", ">", "<", ">=", "<=", "!="],
                key="filter_operator"
            )
        with col3:
            filter_value = st.text_input("Value:", key="filter_value")

        if st.button("Apply Filter"):
            try:
                filter_config = {
                    "column": filter_column,
                    "operator": operator,
                    "value": filter_value
                }
                dataframe = apply_filter_func(dataframe, filter_config)
                st.success(f"✅ Filtered to {len(dataframe)} rows")
            except ValueError as e:
                st.error(str(e))

    return dataframe


def display_chat_history(messages):
    """Display chat message history.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
    """
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def display_user_message(user_input):
    """Display user message in chat.

    Args:
        user_input: The user's input text
    """
    with st.chat_message("user"):
        st.markdown(user_input)


def display_assistant_response(answer, citation_text=None):
    """Display assistant response with optional citations.

    Args:
        answer: The text response from the assistant
        citation_text: Optional citation/source information
    """
    st.markdown(answer)
    if citation_text:
        st.caption(citation_text)


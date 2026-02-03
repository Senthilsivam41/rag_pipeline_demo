"""Hybrid RAG + Analytics App using LangChain Tools.

Combines semantic search (RAG) with data aggregation (sum, avg, count, etc.)
using LangChain's tool system to let the LLM choose the right operation.
"""
# pylint: disable=import-error

import warnings
import time
import functools
import streamlit as st
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.prebuilt import create_react_agent
import pandas as pd

from data_loader import DataLoader
from data_aggregator import DataAggregator
from agent_telemetry import get_telemetry
from shared_ui import display_chat_history, display_user_message

# Suppress Pydantic V1 compatibility warning with Python 3.14
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# --- Page Config ---
st.set_page_config(
    page_title="Hybrid RAG + Analytics",
    page_icon="📊",
    layout="wide"
)
st.title("📊 Hybrid RAG + Analytics")
st.markdown(
    "Semantic search + Data aggregation. "
    "Upload CSV/Parquet for intelligent Q&A with stats."
)

# Store dataframe globally in session
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

# Initialize telemetry in session state
if "telemetry" not in st.session_state:
    st.session_state.telemetry = get_telemetry()


def instrument_tool(tool_func, telemetry):
    """Wrap a tool function to record telemetry.

    Args:
        tool_func: The tool function to wrap
        telemetry: AgentTelemetry instance

    Returns:
        Wrapped function that records telemetry
    """
    original_func = tool_func.func if hasattr(tool_func, "func") else tool_func
    tool_name = tool_func.name if hasattr(tool_func, "name") else getattr(tool_func, "__name__", "unknown")

    @functools.wraps(original_func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = original_func(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000
            telemetry.log_tool_call(
                tool_name=tool_name,
                tool_input={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                tool_output=str(result)[:200],
                execution_time_ms=execution_time_ms,
                success=True
            )
            return result
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            telemetry.log_tool_call(
                tool_name=tool_name,
                tool_input={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                tool_output=None,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
            raise

    # Return wrapper (preserve tool properties through functools.wraps)
    return wrapper


def create_aggregation_tools(df: pd.DataFrame):
    """Create LangChain tools for data aggregation.

    Args:
        df: DataFrame to create tools for

    Returns:
        list: Tool objects for LangChain
    """
    # pylint: disable=invalid-name

    @tool
    def sum_column(column_name: str) -> float | str:
        """Sum values in a numeric column.

        Args:
            column_name: Name of the column to sum

        Returns:
            Total sum or error message
        """
        try:
            return DataAggregator.sum_column(df, column_name)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def average_column(column_name: str) -> float | str:
        """Calculate average of a numeric column.

        Args:
            column_name: Name of the column

        Returns:
            Average value or error message
        """
        try:
            return DataAggregator.average_column(df, column_name)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def min_column(column_name: str) -> float | str:
        """Get minimum value in a column.

        Args:
            column_name: Name of the column

        Returns:
            Minimum value or error message
        """
        try:
            return DataAggregator.min_column(df, column_name)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def max_column(column_name: str) -> float | str:
        """Get maximum value in a column.

        Args:
            column_name: Name of the column

        Returns:
            Maximum value or error message
        """
        try:
            return DataAggregator.max_column(df, column_name)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def count_column(column_name: str) -> int | str:
        """Count non-null values in a column.

        Args:
            column_name: Name of the column

        Returns:
            Count of non-null values or error message
        """
        try:
            return DataAggregator.count_column(df, column_name)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def groupby_sum(group_column: str, value_column: str) -> dict | str:
        """Group by a column and sum values.

        Args:
            group_column: Column to group by
            value_column: Column to sum

        Returns:
            Dictionary with group results or error message
        """
        try:
            return DataAggregator.groupby_sum(df, group_column, value_column)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def groupby_average(group_column: str, value_column: str) -> dict | str:
        """Group by a column and average values.

        Args:
            group_column: Column to group by
            value_column: Column to average

        Returns:
            Dictionary with group results or error message
        """
        try:
            return DataAggregator.groupby_average(df, group_column, value_column)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def groupby_count(group_column: str) -> dict | str:
        """Group by a column and count rows.

        Args:
            group_column: Column to group by

        Returns:
            Dictionary with group counts or error message
        """
        try:
            return DataAggregator.groupby_count(df, group_column)
        except ValueError as e:
            return f"Error: {str(e)}"

    @tool
    def get_statistics() -> dict:
        """Get comprehensive statistics about the dataset.

        Returns:
            Dictionary with dataset statistics
        """
        return DataAggregator.get_statistics(df)

    @tool
    def get_columns() -> dict | str:
        """Get list of all column names with their data types.

        Returns:
            Dictionary with column names and data types or error message
        """
        column_info = {}
        for col in df.columns:
            column_info[col] = str(df[col].dtype)
        return column_info

    @tool
    def get_column_sample(column_name: str) -> dict | str:
        """Get sample values from a column to understand the data.

        Use this FIRST to understand what values are in a column
        before trying to filter or group by it.

        Args:
            column_name: Column to get samples from

        Returns:
            Dictionary with sample values and unique count or error message
        """
        try:
            if column_name not in df.columns:
                return f"Error: Column '{column_name}' not found"
            sample_values = df[column_name].unique()[:10].tolist()
            return {
                "column": column_name,
                "unique_count": int(df[column_name].nunique()),
                "sample_values": sample_values,
                "data_type": str(df[column_name].dtype)
            }
        except Exception as e:
            return f"Error: {str(e)}"

    @tool
    def filter_count(column_name: str, value: str) -> int | str:
        """Count rows where a specific column matches a value.

        Use this to count occurrences of a specific value in a column.
        Example: Count employees with ethnicity "Asian" by using
        filter_count("ethnicity", "Asian")

        Args:
            column_name: Column to filter on
            value: Value to match

        Returns:
            Count of matching rows or error message
        """
        try:
            if column_name not in df.columns:
                return f"Error: Column '{column_name}' not found"
            count = len(df[df[column_name] == value])
            return count
        except Exception as e:
            return f"Error: {str(e)}"

    return [
        sum_column,
        average_column,
        min_column,
        max_column,
        count_column,
        groupby_sum,
        groupby_average,
        groupby_count,
        get_statistics,
        get_columns,
        get_column_sample,
        filter_count
    ]


def process_tabular_data(file):
    """Load and index tabular data using LangChain.

    Args:
        file: Uploaded file

    Returns:
        VectorStoreIndex or None
    """
    try:
        # Validate file
        DataLoader.validate_file(file)

        # Load data
        dataframe = DataLoader.load_data(file)
        st.session_state.dataframe = dataframe

        # Show preview and summary
        col1, col2 = st.columns(2)
        with col1:
            DataLoader.preview_data(dataframe)
        with col2:
            summary = DataLoader.get_data_summary(dataframe)
            st.subheader("📈 Data Summary")
            st.metric("Rows", summary["rows"])
            st.metric("Columns", summary["columns"])
            st.metric("Memory (MB)", f"{summary['memory_mb']:.2f}")

        # Column selection
        st.subheader("🎯 Select Columns for RAG Indexing")
        all_columns = DataLoader.get_columns(dataframe)
        selected_columns = st.multiselect(
            "Choose columns (for semantic search):",
            all_columns,
            default=all_columns,
            key="column_selector"
        )
        dataframe_indexed = DataLoader.select_columns(dataframe, selected_columns)

        # Create table-aware chunks and build vector store
        st.info(f"📍 Indexing {len(dataframe_indexed)} rows for semantic search...")
        chunks = DataLoader.create_table_aware_chunks(dataframe_indexed)
        documents = [Document(page_content=chunk) for chunk in chunks]

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(documents=documents, embedding=embeddings)
        st.success(f"✅ Indexed {len(chunks)} rows!")
        return vectorstore.as_retriever()

    except ValueError as e:
        st.error(str(e))
        return None
    except Exception as e:
        st.error(f"❌ Error processing data: {str(e)}")
        return None


# --- Sidebar ---
with st.sidebar:
    st.header("📁 Upload")
    uploaded_file = st.file_uploader(
        "Upload CSV or Parquet",
        type=["csv", "parquet", "pq"]
    )
    st.divider()
    st.info("🤖 Uses agent to choose: semantic search or aggregation")
    st.info("✨ Powered by Ollama + HuggingFace (local, private)")

    # Show data schema if available
    if uploaded_file and "dataframe" in st.session_state and st.session_state.dataframe is not None:
        with st.expander("📊 Data Schema", expanded=False):
            df_info = st.session_state.dataframe
            st.write(f"**Rows:** {len(df_info)}")
            st.write(f"**Columns:** {len(df_info.columns)}")
            st.write("**Column Types:**")
            for col in df_info.columns:
                st.write(f"  • {col}: {df_info[col].dtype}")

            st.write("**Sample Values:**")
            for col in df_info.columns[:5]:  # Show first 5 columns
                unique_vals = df_info[col].unique()[:5].tolist()
                st.write(f"  • {col}: {unique_vals}")

    # Telemetry dashboard
    with st.expander("📈 Tool Usage Telemetry", expanded=False):
        if "telemetry" in st.session_state:
            telemetry = st.session_state.telemetry
            summary = telemetry.get_summary()

            st.write(f"**Total Tool Calls:** {summary['total_tool_calls']}")

            if summary['tool_call_counts']:
                st.write("**Calls per Tool:**")
                for tool_name, count in sorted(
                    summary['tool_call_counts'].items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    st.write(f"  • {tool_name}: {count}")

            if summary['tool_success_rates']:
                st.write("**Success Rates:**")
                for tool_name, rate in sorted(
                    summary['tool_success_rates'].items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    pct = rate * 100
                    st.write(f"  • {tool_name}: {pct:.1f}%")

            if summary['average_execution_times_ms']:
                st.write("**Avg Execution Time (ms):**")
                for tool_name, avg_time in sorted(
                    summary['average_execution_times_ms'].items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    st.write(f"  • {tool_name}: {avg_time:.2f}ms")

            # Show recent calls
            st.divider()
            st.write("**Recent Tool Calls:**")
            recent_calls = telemetry.get_call_history(n=5)
            for i, call in enumerate(recent_calls, 1):
                status_icon = "✅" if call.success else "❌"
                st.write(
                    f"{i}. {status_icon} **{call.tool_name}** "
                    f"({call.execution_time_ms:.2f}ms) - {call.timestamp[-8:]}"
                )

            # Clear telemetry button
            if st.button("🗑️ Clear Telemetry"):
                st.session_state.telemetry.clear()
                st.rerun()
        else:
            st.info("No telemetry data yet. Run queries to collect tool usage data.")

# --- Main App ---
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()

    if file_ext in {"csv", "parquet", "pq"}:
        if "retriever" not in st.session_state:
            with st.spinner("📊 Processing data..."):
                retriever = process_tabular_data(uploaded_file)
                if retriever:
                    st.session_state.retriever = retriever
                else:
                    st.stop()

        if st.session_state.dataframe is not None:
            st.subheader("🔍 Intelligent Q&A (Search + Aggregation)")

            # Get available columns for the prompt
            available_columns = list(st.session_state.dataframe.columns)
            column_info = {col: str(st.session_state.dataframe[col].dtype)
                          for col in available_columns}

            # Create tools
            agg_tools = create_aggregation_tools(st.session_state.dataframe)

            # Instrument tools with telemetry
            telemetry = st.session_state.telemetry
            instrumented_tools = [
                instrument_tool(tool, telemetry) for tool in agg_tools
            ]

            # Create LLM with tools
            llm = ChatOllama(model="llama3.2:1b", temperature=0)

            # Create enhanced system prompt with column information
            column_list = "\n".join([f"  - {col} ({col_type})"
                                    for col, col_type in column_info.items()])

            system_prompt = f"""You are a helpful data analyst assistant with access to employee/demographic data.

IMPORTANT - Before performing any analysis:
1. ALWAYS use get_column_sample() first to see what values are in a column
2. For filtering queries (like "count Asian employees"), use filter_count() tool
3. For numerical aggregations, use sum_column, average_column, etc.
4. For grouping operations, use groupby_sum, groupby_average, groupby_count

Available columns in the dataset:
{column_list}

Available tools:
- get_columns: Get list of all columns and their data types
- get_column_sample: See sample values in a column (USE THIS FIRST!)
- filter_count: Count rows matching a specific value
- sum_column, average_column, min_column, max_column, median_column, count_column
- groupby_sum, groupby_average, groupby_count
- get_statistics: Get min, max, avg, median for numeric columns

When user asks about counting specific categories:
1. Use get_column_sample() to see what column contains the category
2. Use filter_count(column_name, category_value) to count matches

When user asks for counts by a category (for example: "Count employees by department"):
1. Use groupby_count(group_column) with the appropriate group column
2. Return the results as a markdown table: first column = group, second column = count

Example: "Count Asian employees"
1. Call get_column_sample("ethnicity") - to see available values
2. Call filter_count("ethnicity", "Asian") - to count matches

Formatting: For groupby results return a markdown table like:

| Department | Count |
|---|---|
| IT | 12 |
| Sales | 8 |

Always be precise about column names and values. Ask for clarification if needed."""
            # Create agent using LangGraph with instrumented tools
            agent = create_react_agent(llm, instrumented_tools, prompt=system_prompt)

            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display chat history
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Quick Analytics: run common queries directly
            with st.expander("Quick Analytics (Run immediate queries)", expanded=False):
                st.caption("Run frequent analytics directly without using the agent")
                quick_op = st.selectbox("Operation", ["GroupBy Count", "GroupBy Average", "Filter Count", "Column Sample"], key="quick_op")

                if quick_op == "GroupBy Count":
                    group_col = st.selectbox("Group Column", available_columns, key="gbc_col")
                    if st.button("Run GroupBy Count") and group_col:
                        try:
                            res = DataAggregator.groupby_count(st.session_state.dataframe, group_col)
                            df_res = pd.DataFrame(list(res.items()), columns=[group_col, "count"]).sort_values("count", ascending=False)
                            st.table(df_res)
                        except Exception as e:
                            st.error(str(e))

                if quick_op == "GroupBy Average":
                    value_col = st.selectbox("Value Column (numeric)", available_columns, key="gba_value")
                    group_col = st.selectbox("Group Column", available_columns, key="gba_group")
                    if st.button("Run GroupBy Average") and group_col and value_col:
                        try:
                            res = DataAggregator.groupby_average(st.session_state.dataframe, group_col, value_col)
                            df_res = pd.DataFrame(list(res.items()), columns=[group_col, f"average_{value_col}"]).sort_values(f"average_{value_col}", ascending=False)
                            st.table(df_res)
                        except Exception as e:
                            st.error(str(e))

                if quick_op == "Filter Count":
                    col = st.selectbox("Column", available_columns, key="fc_col")
                    val = st.text_input("Value to match", key="fc_val")
                    if st.button("Run Filter Count") and col and val:
                        try:
                            cnt = int(len(st.session_state.dataframe[st.session_state.dataframe[col] == val]))
                            st.metric("Count", cnt)
                        except Exception as e:
                            st.error(str(e))

                if quick_op == "Column Sample":
                    col = st.selectbox("Column to sample", available_columns, key="sample_col")
                    if st.button("Show Sample") and col:
                        try:
                            unique_vals = DataAggregator.unique_values(st.session_state.dataframe, col)
                            st.write({"column": col, "unique_count": DataAggregator.unique_count(st.session_state.dataframe, col), "sample_values": unique_vals[:10]})
                        except Exception as e:
                            st.error(str(e))

            # Chat input
            if user_input := st.chat_input("Ask about your data (search or stats)"):
                st.session_state.messages.append({"role": "user", "content": user_input})
                display_user_message(user_input)

                with st.chat_message("assistant"):
                    try:
                        # Use agent to process query
                        response = agent.invoke({"messages": [
                            {"role": "user", "content": user_input}
                        ]})

                        # Extract answer from response
                        if "messages" in response and response["messages"]:
                            last_message = response["messages"][-1]
                            if hasattr(last_message, "content"):
                                answer = last_message.content
                            else:
                                answer = str(last_message)
                        else:
                            answer = str(response)

                        st.markdown(answer)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": answer}
                        )

                        # Display tool usage telemetry
                        telemetry = st.session_state.telemetry
                        latest_call = telemetry.get_latest_call()
                        if latest_call:
                            with st.expander("🔍 Tool Usage Details", expanded=False):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Tool Used", latest_call.tool_name)
                                with col2:
                                    st.metric("Execution Time", f"{latest_call.execution_time_ms:.2f}ms")
                                with col3:
                                    st.metric("Status", "✅ Success" if latest_call.success else "❌ Failed")

                                st.write("**Input:**")
                                st.code(str(latest_call.tool_input), language="json")
                                st.write("**Output:**")
                                st.code(str(latest_call.tool_output)[:500], language="json")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

else:
    st.info("👈 Upload a CSV or Parquet file to get started!")
    st.markdown("""
    ### Features:
    - 🔍 **Semantic Search** — Find specific information in your data
    - 📊 **Data Aggregation** — Sum, average, count, min, max, groupby
    - 🤖 **Intelligent Agent** — LLM chooses the right tool for your question
    - 🔒 **100% Private** — All processing local

    ### Example Questions:
    - "What is the sum of sales?"
    - "What is the average salary by department?"
    - "How many employees are in each location?"
    - "Show me the highest and lowest values"
    """)

"""Data aggregation module for CSV/Parquet analysis.

Provides aggregation functions (sum, average, count, min, max, groupby)
that can be used by LangChain/LlamaIndex tools for hybrid RAG + Analytics.
"""
# pylint: disable=import-error

import pandas as pd
import json


class DataAggregator:
    """Handles data aggregation and statistical queries."""

    @staticmethod
    def get_available_aggregations(dataframe: pd.DataFrame) -> dict:
        """Get available aggregation operations based on data types.

        Args:
            dataframe: DataFrame to analyze

        Returns:
            dict: Available aggregations for each column
        """
        aggregations = {}
        for col in dataframe.columns:
            col_type = dataframe[col].dtype
            if pd.api.types.is_numeric_dtype(col_type):
                aggregations[col] = ["sum", "avg", "min", "max", "median", "count"]
            else:
                aggregations[col] = ["count", "unique_values"]
        return aggregations

    @staticmethod
    def count_rows(dataframe: pd.DataFrame) -> int:
        """Count total rows in dataset.

        Args:
            dataframe: Data to count

        Returns:
            int: Row count
        """
        return len(dataframe)

    @staticmethod
    def count_columns(dataframe: pd.DataFrame) -> int:
        """Count total columns in dataset.

        Args:
            dataframe: Data to analyze

        Returns:
            int: Column count
        """
        return len(dataframe.columns)

    @staticmethod
    def sum_column(dataframe: pd.DataFrame, column: str) -> float:
        """Calculate sum of a numeric column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            float: Sum value

        Raises:
            ValueError: If column not found or not numeric
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        return float(dataframe[column].sum())

    @staticmethod
    def average_column(dataframe: pd.DataFrame, column: str) -> float:
        """Calculate average of a numeric column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            float: Average value

        Raises:
            ValueError: If column not found or not numeric
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        return float(dataframe[column].mean())

    @staticmethod
    def min_column(dataframe: pd.DataFrame, column: str) -> float:
        """Get minimum value in a numeric column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            float: Minimum value
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        return float(dataframe[column].min())

    @staticmethod
    def max_column(dataframe: pd.DataFrame, column: str) -> float:
        """Get maximum value in a numeric column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            float: Maximum value
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        return float(dataframe[column].max())

    @staticmethod
    def median_column(dataframe: pd.DataFrame, column: str) -> float:
        """Get median value in a numeric column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            float: Median value
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        return float(dataframe[column].median())

    @staticmethod
    def count_column(dataframe: pd.DataFrame, column: str) -> int:
        """Count non-null values in a column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            int: Count of non-null values
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        return int(dataframe[column].count())

    @staticmethod
    def unique_count(dataframe: pd.DataFrame, column: str) -> int:
        """Count unique values in a column.

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            int: Count of unique values
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        return int(dataframe[column].nunique())

    @staticmethod
    def unique_values(dataframe: pd.DataFrame, column: str) -> list:
        """Get unique values in a column (limited to 20).

        Args:
            dataframe: Source data
            column: Column name

        Returns:
            list: List of unique values
        """
        if column not in dataframe.columns:
            raise ValueError(f"Column '{column}' not found")
        unique_vals = dataframe[column].unique().tolist()
        # Limit to 20 values for readability
        return unique_vals[:20]

    @staticmethod
    def groupby_sum(dataframe: pd.DataFrame, group_column: str, value_column: str) -> dict:
        """Group by column and sum values.

        Args:
            dataframe: Source data
            group_column: Column to group by
            value_column: Column to sum

        Returns:
            dict: Group results {group_value: sum}

        Raises:
            ValueError: If columns not found
        """
        if group_column not in dataframe.columns:
            raise ValueError(f"Group column '{group_column}' not found")
        if value_column not in dataframe.columns:
            raise ValueError(f"Value column '{value_column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[value_column]):
            raise ValueError(f"Column '{value_column}' is not numeric")

        grouped = dataframe.groupby(group_column)[value_column].sum()
        # Convert to JSON-serializable format
        return {str(k): float(v) for k, v in grouped.items()}

    @staticmethod
    def groupby_average(dataframe: pd.DataFrame, group_column: str, value_column: str) -> dict:
        """Group by column and average values.

        Args:
            dataframe: Source data
            group_column: Column to group by
            value_column: Column to average

        Returns:
            dict: Group results {group_value: average}
        """
        if group_column not in dataframe.columns:
            raise ValueError(f"Group column '{group_column}' not found")
        if value_column not in dataframe.columns:
            raise ValueError(f"Value column '{value_column}' not found")
        if not pd.api.types.is_numeric_dtype(dataframe[value_column]):
            raise ValueError(f"Column '{value_column}' is not numeric")

        grouped = dataframe.groupby(group_column)[value_column].mean()
        return {str(k): float(v) for k, v in grouped.items()}

    @staticmethod
    def groupby_count(dataframe: pd.DataFrame, group_column: str) -> dict:
        """Group by column and count rows.

        Args:
            dataframe: Source data
            group_column: Column to group by

        Returns:
            dict: Group results {group_value: count}
        """
        if group_column not in dataframe.columns:
            raise ValueError(f"Group column '{group_column}' not found")

        grouped = dataframe.groupby(group_column).size()
        return {str(k): int(v) for k, v in grouped.items()}

    @staticmethod
    def filter_and_aggregate(
        dataframe: pd.DataFrame,
        filter_column: str,
        filter_value: str,
        agg_column: str,
        agg_func: str
    ) -> float:
        """Filter data and then aggregate.

        Args:
            dataframe: Source data
            filter_column: Column to filter by
            filter_value: Value to match
            agg_column: Column to aggregate
            agg_func: Aggregation function (sum, avg, min, max, median, count)

        Returns:
            float: Aggregation result
        """
        filtered = dataframe[dataframe[filter_column] == filter_value]

        if filtered.empty:
            raise ValueError(f"No rows found where {filter_column} == {filter_value}")

        if agg_func == "sum":
            return DataAggregator.sum_column(filtered, agg_column)
        elif agg_func == "avg":
            return DataAggregator.average_column(filtered, agg_column)
        elif agg_func == "min":
            return DataAggregator.min_column(filtered, agg_column)
        elif agg_func == "max":
            return DataAggregator.max_column(filtered, agg_column)
        elif agg_func == "median":
            return DataAggregator.median_column(filtered, agg_column)
        elif agg_func == "count":
            return DataAggregator.count_column(filtered, agg_column)
        else:
            raise ValueError(f"Unknown aggregation function: {agg_func}")

    @staticmethod
    def get_statistics(dataframe: pd.DataFrame) -> dict:
        """Get comprehensive statistics about the dataset.

        Args:
            dataframe: Data to analyze

        Returns:
            dict: Statistics summary
        """
        stats = {
            "total_rows": len(dataframe),
            "total_columns": len(dataframe.columns),
            "memory_mb": dataframe.memory_usage(deep=True).sum() / (1024 * 1024),
            "columns": list(dataframe.columns),
            "numeric_columns": dataframe.select_dtypes(include=['number']).columns.tolist(),
            "text_columns": dataframe.select_dtypes(include=['object']).columns.tolist(),
        }
        return stats

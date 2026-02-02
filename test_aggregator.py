"""Tests for data aggregation module."""
# pylint: disable=import-error

import pytest
import pandas as pd
from data_aggregator import DataAggregator


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "Department": ["Sales", "IT", "Sales", "HR", "IT"],
        "Salary": [50000, 80000, 55000, 60000, 85000],
        "Age": [25, 30, 28, 35, 32],
        "Bonus": [5000, 10000, 5500, 6000, 8500]
    })


class TestBasicAggregations:
    """Test basic aggregation functions."""

    def test_sum_column(self, sample_df):
        """Test sum calculation."""
        result = DataAggregator.sum_column(sample_df, "Salary")
        assert result == 330000

    def test_average_column(self, sample_df):
        """Test average calculation."""
        result = DataAggregator.average_column(sample_df, "Salary")
        assert result == 66000

    def test_min_column(self, sample_df):
        """Test minimum value."""
        result = DataAggregator.min_column(sample_df, "Salary")
        assert result == 50000

    def test_max_column(self, sample_df):
        """Test maximum value."""
        result = DataAggregator.max_column(sample_df, "Salary")
        assert result == 85000

    def test_median_column(self, sample_df):
        """Test median value."""
        result = DataAggregator.median_column(sample_df, "Salary")
        assert result == 60000  # Middle value of sorted [50000, 55000, 60000, 80000, 85000]

    def test_count_column(self, sample_df):
        """Test row count."""
        result = DataAggregator.count_column(sample_df, "Salary")
        assert result == 5

    def test_unique_count(self, sample_df):
        """Test unique count."""
        result = DataAggregator.unique_count(sample_df, "Department")
        assert result == 3  # Sales, IT, HR


class TestGroupByAggregations:
    """Test groupby aggregation functions."""

    def test_groupby_sum(self, sample_df):
        """Test groupby sum."""
        result = DataAggregator.groupby_sum(sample_df, "Department", "Salary")
        assert result["Sales"] == 105000  # 50000 + 55000
        assert result["IT"] == 165000  # 80000 + 85000
        assert result["HR"] == 60000

    def test_groupby_average(self, sample_df):
        """Test groupby average."""
        result = DataAggregator.groupby_average(sample_df, "Department", "Salary")
        assert result["Sales"] == 52500  # (50000 + 55000) / 2
        assert result["IT"] == 82500  # (80000 + 85000) / 2
        assert result["HR"] == 60000

    def test_groupby_count(self, sample_df):
        """Test groupby count."""
        result = DataAggregator.groupby_count(sample_df, "Department")
        assert result["Sales"] == 2
        assert result["IT"] == 2
        assert result["HR"] == 1


class TestFilterAndAggregate:
    """Test filter + aggregate operations."""

    def test_filter_and_sum(self, sample_df):
        """Test filter and sum."""
        result = DataAggregator.filter_and_aggregate(
            sample_df, "Department", "Sales", "Salary", "sum"
        )
        assert result == 105000

    def test_filter_and_average(self, sample_df):
        """Test filter and average."""
        result = DataAggregator.filter_and_aggregate(
            sample_df, "Department", "IT", "Salary", "avg"
        )
        assert result == 82500

    def test_filter_and_max(self, sample_df):
        """Test filter and max."""
        result = DataAggregator.filter_and_aggregate(
            sample_df, "Department", "Sales", "Salary", "max"
        )
        assert result == 55000


class TestStatistics:
    """Test statistics functions."""

    def test_get_statistics(self, sample_df):
        """Test statistics generation."""
        stats = DataAggregator.get_statistics(sample_df)
        assert stats["total_rows"] == 5
        assert stats["total_columns"] == 5
        assert "Salary" in stats["numeric_columns"]
        assert "Name" in stats["text_columns"]

    def test_get_available_aggregations(self, sample_df):
        """Test available aggregations."""
        aggs = DataAggregator.get_available_aggregations(sample_df)
        assert "Salary" in aggs
        assert "sum" in aggs["Salary"]
        assert "avg" in aggs["Salary"]
        assert "Name" in aggs
        assert "count" in aggs["Name"]


class TestErrorHandling:
    """Test error handling."""

    def test_sum_nonexistent_column(self, sample_df):
        """Test sum on non-existent column."""
        with pytest.raises(ValueError, match="not found"):
            DataAggregator.sum_column(sample_df, "NonExistent")

    def test_sum_non_numeric_column(self, sample_df):
        """Test sum on non-numeric column."""
        with pytest.raises(ValueError, match="not numeric"):
            DataAggregator.sum_column(sample_df, "Name")

    def test_groupby_nonexistent_column(self, sample_df):
        """Test groupby on non-existent column."""
        with pytest.raises(ValueError, match="not found"):
            DataAggregator.groupby_sum(sample_df, "NonExistent", "Salary")

    def test_filter_and_aggregate_no_match(self, sample_df):
        """Test filter that returns no rows."""
        with pytest.raises(ValueError, match="No rows found"):
            DataAggregator.filter_and_aggregate(
                sample_df, "Department", "NonExistent", "Salary", "sum"
            )

    def test_invalid_agg_function(self, sample_df):
        """Test invalid aggregation function."""
        with pytest.raises(ValueError, match="Unknown aggregation"):
            DataAggregator.filter_and_aggregate(
                sample_df, "Department", "Sales", "Salary", "invalid"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

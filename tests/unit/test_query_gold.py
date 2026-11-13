from datetime import date
from unittest.mock import Mock

import pytest

from climatewatch.application.query_gold import QueryGold
from climatewatch.infrastructure.gold_reader import GoldReader


def test_daily_filters_and_returns_reader_result() -> None:
    reader = Mock()
    expected = [{"location_id": "sp", "precipitation_mm": 12.0}]
    reader.daily.return_value = expected
    query = QueryGold(reader)

    result = query.daily("sp", date(2024, 1, 1), date(2024, 1, 2))

    assert result == expected
    reader.daily.assert_called_once_with("sp", date(2024, 1, 1), date(2024, 1, 2))


def test_empty_location_and_reversed_period_are_rejected() -> None:
    spark = Mock()
    query = QueryGold(GoldReader(spark))

    with pytest.raises(ValueError, match="location_id"):
        query.daily("  ", date(2024, 1, 1), date(2024, 1, 2))
    with pytest.raises(ValueError, match="posterior"):
        query.daily("sp", date(2024, 1, 2), date(2024, 1, 1))
    spark.table.assert_not_called()


def test_reader_caps_row_limit() -> None:
    with pytest.raises(ValueError, match="max_rows"):
        GoldReader(Mock(), max_rows=10_001)


def test_missing_gold_tables_return_empty_results() -> None:
    spark = Mock()
    spark.catalog.tableExists.return_value = False
    reader = GoldReader(spark)

    assert reader.daily("sp", date(2024, 1, 1), date(2024, 1, 2)) == []
    assert reader.indicators("sp", date(2024, 1, 1), date(2024, 1, 2)) == []
    assert spark.table.call_count == 0

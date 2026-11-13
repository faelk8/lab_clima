"""Testes do cálculo de cobertura horária para o relatório batch."""

from datetime import date, datetime, timedelta

from climatewatch.application.coverage import hourly_coverage


def test_duplicate_timestamps_do_not_hide_missing_hours() -> None:
    """Duplicatas não são contadas como horas únicas recebidas."""
    coverage = hourly_coverage(
        date(2024, 1, 1),
        date(2024, 1, 1),
        "UTC",
        ["2024-01-01T00:00"] * 24,
    )
    assert coverage == {
        "expected_hours": 24,
        "received_hours": 1,
        "missing_hours": 23,
        "duplicate_hours": 23,
        "extra_hours": 0,
    }


def test_coverage_reports_duplicates_and_timestamps_outside_range() -> None:
    """Duplicatas e timestamps extras são mostrados sem compensar lacunas."""
    timestamps = [
        (datetime(2024, 1, 1) + timedelta(hours=offset)).isoformat(timespec="minutes")
        for offset in range(23)
    ]
    timestamps.extend([timestamps[0], "2024-01-02T01:00"])
    coverage = hourly_coverage(date(2024, 1, 1), date(2024, 1, 1), "UTC", timestamps)
    assert coverage == {
        "expected_hours": 24,
        "received_hours": 23,
        "missing_hours": 1,
        "duplicate_hours": 1,
        "extra_hours": 1,
    }


def test_coverage_handles_complete_local_day_and_dst_length() -> None:
    """A expectativa segue o fuso local, incluindo um dia civil de 23 horas."""
    timestamps = [f"2024-03-10T{hour:02d}:00" for hour in [0, 1, *range(3, 24)]]
    coverage = hourly_coverage(date(2024, 3, 10), date(2024, 3, 10), "America/New_York", timestamps)
    assert coverage["expected_hours"] == 23
    assert coverage["received_hours"] == 23
    assert coverage["missing_hours"] == 0

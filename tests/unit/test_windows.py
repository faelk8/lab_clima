"""Testes de partição inclusiva de intervalos batch."""

from datetime import date

import pytest

from climatewatch.application.windows import plan_windows


def test_windows_cover_leap_month_without_gaps_or_overlap() -> None:
    """Particiona fevereiro bissexto em janelas contíguas."""
    windows = plan_windows(date(2024, 2, 26), date(2024, 3, 2), max_days=3)
    assert [(w.start, w.end) for w in windows] == [
        (date(2024, 2, 26), date(2024, 2, 28)),
        (date(2024, 2, 29), date(2024, 3, 2)),
    ]
    assert sum(w.days for w in windows) == 6


def test_windows_enforce_request_budget_and_date_order() -> None:
    """Bloqueia intervalo invertido ou que exceda orçamento."""
    with pytest.raises(ValueError, match="orçamento"):
        plan_windows(date(2024, 1, 1), date(2024, 1, 20), max_days=2, max_requests=2)
    with pytest.raises(ValueError, match="anterior"):
        plan_windows(date(2024, 1, 2), date(2024, 1, 1))


def test_thirty_day_backfill_three_locations_fits_request_budget() -> None:
    """Cinco janelas por cidade usam 15 chamadas antes dos retries."""
    windows = plan_windows(date(2026, 10, 1), date(2026, 10, 30), max_days=7, max_requests=30)
    assert len(windows) == 5
    assert len(windows) * 3 == 15

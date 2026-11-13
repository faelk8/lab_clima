"""Cálculo de cobertura horária sem mascarar duplicatas ou valores extras."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


def hourly_coverage(
    start: date, end: date, timezone_name: str, timestamps: list[str]
) -> dict[str, int]:
    """Compara timestamps únicos normalizados com as horas esperadas do intervalo."""
    if end < start:
        raise ValueError("end deve ser igual ou posterior a start")
    zone = ZoneInfo(timezone_name)
    first_local = datetime.combine(start, time.min, zone)
    end_local = datetime.combine(end + timedelta(days=1), time.min, zone)
    first_utc = first_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    expected = {
        first_utc + timedelta(hours=offset)
        for offset in range(int((end_utc - first_utc).total_seconds() // 3600))
    }
    actual_values = []
    for value in timestamps:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=zone)
        actual_values.append(parsed.astimezone(timezone.utc))
    actual = set(actual_values)
    return {
        "expected_hours": len(expected),
        "received_hours": len(expected & actual),
        "missing_hours": len(expected - actual),
        "duplicate_hours": len(actual_values) - len(actual),
        "extra_hours": len(actual - expected),
    }

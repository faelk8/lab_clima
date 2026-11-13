import pytest

from climatewatch.domain.thresholds import (
    ThresholdState,
    evaluate_precipitation_threshold,
)


@pytest.mark.parametrize(
    ("rain", "expected"),
    [
        (49.9, ThresholdState.BELOW),
        (50.0, ThresholdState.AT),
        (50.1, ThresholdState.ABOVE),
        (None, ThresholdState.INCONCLUSIVE),
    ],
)
def test_threshold_boundaries(rain: float | None, expected: ThresholdState) -> None:
    assert evaluate_precipitation_threshold(rain, 24).state == expected


def test_insufficient_coverage_is_inconclusive() -> None:
    assert evaluate_precipitation_threshold(100.0, 17).state == ThresholdState.INCONCLUSIVE
    assert evaluate_precipitation_threshold(100.0, 23).state == ThresholdState.INCONCLUSIVE
    assert evaluate_precipitation_threshold(100.0, 24).state == ThresholdState.ABOVE
    assert (
        evaluate_precipitation_threshold(100.0, 24, complete_window=False).state
        == ThresholdState.INCONCLUSIVE
    )


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        evaluate_precipitation_threshold(1.0, 24, threshold_mm=-1)

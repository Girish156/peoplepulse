"""
Unit tests for progress calculation service.
Verifies the spec requirement:
KR1: target=10, actual=8, weight=0.6
KR2: target=20, actual=15, weight=0.4
Expected weighted progress is 78% (0.78).
"""

import pytest
from app.services.progress import calculate_goal_progress, calculate_key_result_progress


def test_weighted_progress_spec_example():
    """
    Test the exact specification example:
    KR1: target=10, actual=8, weight=0.6 -> 8/10 = 0.8 * 0.6 = 0.48
    KR2: target=20, actual=15, weight=0.4 -> 15/20 = 0.75 * 0.4 = 0.30
    Total = 0.48 + 0.30 = 0.78 (78%)
    """
    krs = [
        {"baseline": 0, "actual": 8, "target": 10, "weight": 0.6, "metric_type": "count", "allowed_scale": 1.0},
        {"baseline": 0, "actual": 15, "target": 20, "weight": 0.4, "metric_type": "count", "allowed_scale": 1.0},
    ]
    res = calculate_goal_progress(krs)
    assert abs(res["weighted_progress"] - 0.78) < 1e-6
    assert res["weight_sum"] == 1.0
    assert res["missing_kr_count"] == 0


def test_missing_actual_values():
    """Missing actual values (None) must be excluded from weight sum and count recorded."""
    krs = [
        {"baseline": 0, "actual": 8, "target": 10, "weight": 0.6, "metric_type": "count", "allowed_scale": 1.0},
        {"baseline": 0, "actual": None, "target": 20, "weight": 0.4, "metric_type": "count", "allowed_scale": 1.0},
    ]
    res = calculate_goal_progress(krs)
    # Only KR1 is included: 0.8 * 0.6 / 0.6 = 0.8
    assert abs(res["weighted_progress"] - 0.80) < 1e-6
    assert res["missing_kr_count"] == 1
    assert res["weight_sum"] == 0.6


def test_all_missing_actuals():
    """If all actuals are missing, weighted_progress is 0.0 and weight_sum is 0.0."""
    krs = [
        {"baseline": 0, "actual": None, "target": 10, "weight": 0.5, "metric_type": "count"},
        {"baseline": 0, "actual": None, "target": 20, "weight": 0.5, "metric_type": "count"},
    ]
    res = calculate_goal_progress(krs)
    assert res["weighted_progress"] == 0.0
    assert res["weight_sum"] == 0.0
    assert res["missing_kr_count"] == 2


def test_zero_target_or_zero_range():
    """Target equal to baseline must not trigger divide-by-zero."""
    res = calculate_key_result_progress(baseline=10, actual=10, target=10, metric_type="count")
    assert res["zero_range"] is True
    assert res["capped_progress"] == 0.0


def test_overachievement_and_capping():
    """Overachievement (actual > target) should be capped at allowed_scale for capped_progress, but preserved in raw_progress."""
    res = calculate_key_result_progress(baseline=0, actual=150, target=100, metric_type="count", allowed_scale=1.0)
    assert res["raw_progress"] == 1.5
    assert res["capped_progress"] == 1.0

    # With higher scale
    res_scaled = calculate_key_result_progress(baseline=0, actual=150, target=100, metric_type="count", allowed_scale=1.5)
    assert res_scaled["raw_progress"] == 1.5
    assert res_scaled["capped_progress"] == 1.5


def test_boolean_metric_type():
    """Boolean metric type returns 1.0 if actual >= target, else 0.0."""
    res_pass = calculate_key_result_progress(baseline=0, actual=1, target=1, metric_type="boolean")
    assert res_pass["capped_progress"] == 1.0

    res_fail = calculate_key_result_progress(baseline=0, actual=0, target=1, metric_type="boolean")
    assert res_fail["capped_progress"] == 0.0


def test_negative_weight_raises():
    """Negative weight is invalid and must raise ValueError."""
    krs = [{"baseline": 0, "actual": 5, "target": 10, "weight": -0.5, "metric_type": "count"}]
    with pytest.raises(ValueError):
        calculate_goal_progress(krs)


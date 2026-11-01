"""
Progress calculation service for PeoplePulse.

All calculations are formula-driven — no values are hardcoded.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def calculate_key_result_progress(
    baseline: float,
    actual: Optional[float],
    target: float,
    metric_type: str,
    allowed_scale: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate key result progress as a ratio.

    Parameters
    ----------
    baseline:
        The starting value before any progress.
    actual:
        The current measured value.  ``None`` means the KR has no data yet.
    target:
        The goal value to reach for 100 % completion.
    metric_type:
        One of ``percentage``, ``count``, ``boolean``, ``currency``, ``score``.
    allowed_scale:
        Maximum allowed over-achievement ratio (e.g. ``1.5`` allows up to 150 %).
        Progress is capped at this value.

    Returns
    -------
    dict with keys:
        - ``raw_progress``    – uncapped ratio (may exceed allowed_scale)
        - ``capped_progress`` – ratio capped at *allowed_scale*
        - ``missing``         – True when *actual* is None
        - ``zero_range``      – True when target == baseline (undefined progress)
    """
    if actual is None:
        return {
            "raw_progress": None,
            "capped_progress": None,
            "missing": True,
            "zero_range": False,
        }

    if metric_type == "boolean":
        raw = 1.0 if float(actual) >= float(target) else 0.0
        capped = min(raw, float(allowed_scale))
        return {
            "raw_progress": raw,
            "capped_progress": capped,
            "missing": False,
            "zero_range": False,
        }

    baseline_f = float(baseline)
    target_f = float(target)
    actual_f = float(actual)
    allowed_f = float(allowed_scale)

    range_ = target_f - baseline_f
    if range_ == 0:
        # Target equals baseline — progress is undefined; treat as 0
        return {
            "raw_progress": 0.0,
            "capped_progress": 0.0,
            "missing": False,
            "zero_range": True,
        }

    raw = (actual_f - baseline_f) / range_
    capped = min(raw, allowed_f)
    # Floor at 0 to avoid negative progress ratios
    capped = max(capped, 0.0)
    raw = max(raw, 0.0)

    return {
        "raw_progress": raw,
        "capped_progress": capped,
        "missing": False,
        "zero_range": False,
    }


def calculate_goal_progress(key_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute a weighted-average goal progress from a list of key result dicts.

    Each element of *key_results* must contain:
        - ``baseline``        (numeric)
        - ``actual``          (numeric or None)
        - ``target``          (numeric)
        - ``weight``          (non-negative numeric)
        - ``metric_type``     (str)
        - ``allowed_scale``   (numeric, default 1.0)

    Returns
    -------
    dict with keys:
        - ``weighted_progress`` – final weighted-average progress ratio
        - ``raw_progress``      – unweighted simple average of capped progresses
        - ``weight_sum``        – sum of weights for KRs with data
        - ``missing_kr_count``  – number of KRs with no actual value
        - ``details``           – per-KR breakdown list

    Example
    -------
    KR1: baseline=0, actual=8, target=10, weight=0.6 → progress = 0.8
    KR2: baseline=0, actual=15, target=20, weight=0.4 → progress = 0.75
    weighted = (0.8 * 0.6 + 0.75 * 0.4) / (0.6 + 0.4) = (0.48 + 0.30) / 1.0 = 0.78
    """
    if not key_results:
        return {
            "weighted_progress": 0.0,
            "raw_progress": 0.0,
            "weight_sum": 0.0,
            "missing_kr_count": 0,
            "details": [],
        }

    details = []
    weighted_sum = 0.0
    weight_sum = 0.0
    missing_count = 0
    progress_values = []

    for kr in key_results:
        weight = float(kr.get("weight", 1.0))
        if weight < 0:
            raise ValueError(f"KR weight must be non-negative, got {weight}")

        allowed_scale = float(kr.get("allowed_scale", 1.0))
        result = calculate_key_result_progress(
            baseline=float(kr.get("baseline", 0)),
            actual=kr.get("actual"),
            target=float(kr["target"]),
            metric_type=kr.get("metric_type", "count"),
            allowed_scale=allowed_scale,
        )

        detail = {
            "weight": weight,
            "raw_progress": result["raw_progress"],
            "capped_progress": result["capped_progress"],
            "missing": result["missing"],
            "zero_range": result["zero_range"],
        }
        details.append(detail)

        if result["missing"]:
            missing_count += 1
        else:
            # Only include KRs with data in weighted calculation
            capped = result["capped_progress"]
            weighted_sum += capped * weight
            weight_sum += weight
            progress_values.append(capped)

    if weight_sum == 0.0:
        weighted_progress = 0.0
    else:
        weighted_progress = weighted_sum / weight_sum

    raw_progress = (sum(progress_values) / len(progress_values)) if progress_values else 0.0

    return {
        "weighted_progress": weighted_progress,
        "raw_progress": raw_progress,
        "weight_sum": weight_sum,
        "missing_kr_count": missing_count,
        "details": details,
    }

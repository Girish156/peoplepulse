"""
PeoplePulse Anomaly Evaluation Script
=======================================
Runs anomaly detection rules directly on CSV data, reads ground truth
separately, compares predictions vs ground truth, and computes metrics.

IMPORTANT: Ground truth is NEVER passed to the detector — it is read
separately and compared AFTER detection.
"""

import csv
import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = "data/generated"
GROUND_TRUTH_PATH = "data/ground_truth/ground_truth.csv"
REPORTS_DIR = "data/reports"


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------
def load_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bool_val(s: str) -> bool:
    return str(s).lower() in ("true", "1", "yes")


def safe_div(num: float, denom: float) -> float:
    return num / denom if denom > 0 else 0.0


# ---------------------------------------------------------------------------
# Anomaly Detection Rules (operate on raw CSV data only)
# ---------------------------------------------------------------------------

def detect_goal_owner_mismatch(check_ins: list[dict], goals: list[dict]) -> list[dict]:
    """RULE-001: Find check_ins where employee_id != goal owner employee_id."""
    goal_owner = {r["goal_id"]: r["employee_id"] for r in goals}
    detected = []
    for row in check_ins:
        gid = row.get("goal_id", "")
        ci_emp = row.get("employee_id", "")
        owner = goal_owner.get(gid)
        if owner and ci_emp != owner:
            detected.append({
                "rule_id": "RULE-001",
                "anomaly_type": "goal_owner_mismatch",
                "entity_type": "check_in",
                "entity_id": row["check_in_id"],
                "detail": f"check_in employee={ci_emp}, goal owner={owner}, goal_id={gid}",
            })
    return detected


def detect_progress_exceeds_scale(key_results: list[dict]) -> list[dict]:
    """RULE-002: Find key_results where actual/target > allowed_progress_scale."""
    detected = []
    for row in key_results:
        try:
            target = float(row.get("target", "0"))
            actual = float(row.get("actual", "0"))
            scale = float(row.get("allowed_progress_scale", "1.0"))
            if target > 0 and (actual / target) > scale:
                detected.append({
                    "rule_id": "RULE-002",
                    "anomaly_type": "progress_exceeds_scale",
                    "entity_type": "key_result",
                    "entity_id": row["kr_id"],
                    "detail": f"actual={actual}, target={target}, ratio={actual/target:.4f}, scale={scale}",
                })
        except (ValueError, ZeroDivisionError):
            pass
    return detected


def detect_reviewer_no_relationship(
    feedback: list[dict], employees: list[dict]
) -> list[dict]:
    """RULE-003: Find feedback where reviewer lacks a valid relationship."""
    emp_manager = {r["employee_id"]: r.get("manager_id", "") for r in employees}
    emp_dept = {r["employee_id"]: r.get("department", "") for r in employees}
    emp_ids = {r["employee_id"] for r in employees}
    detected = []
    for row in feedback:
        author = row.get("author_employee_id", "")
        subject = row.get("subject_employee_id", "")
        fbk_type = row.get("feedback_type", "peer")

        if not author or author not in emp_ids:
            continue  # Handled by RULE-005
        if subject not in emp_ids:
            continue

        is_invalid = False
        reason = ""

        if fbk_type == "downward":
            mgr = emp_manager.get(subject, "")
            if author != mgr:
                is_invalid = True
                reason = f"downward feedback author {author} is not manager of {subject} (manager is {mgr})"
        elif fbk_type == "upward":
            mgr = emp_manager.get(author, "")
            if subject != mgr:
                is_invalid = True
                reason = f"upward feedback subject {subject} is not manager of {author} (manager is {mgr})"
        elif fbk_type == "self":
            if author != subject:
                is_invalid = True
                reason = f"self feedback author {author} != subject {subject}"
        elif fbk_type == "peer":
            # Peer feedback: must not be manager/report (that's upward/downward) and should share org relationship
            if author == subject:
                is_invalid = True
                reason = "peer feedback author is subject"

        if is_invalid:
            detected.append({
                "rule_id": "RULE-003",
                "anomaly_type": "reviewer_no_relationship",
                "entity_type": "feedback",
                "entity_id": row["feedback_id"],
                "detail": reason,
            })
    return detected


def detect_closed_cycle_edits(
    audit_events: list[dict], review_cycles: list[dict]
) -> list[dict]:
    """RULE-004: Find audit events with 'modified' action on closed-cycle entities."""
    cycle_status = {r["cycle_id"]: r["status"] for r in review_cycles}
    detected = []
    for row in audit_events:
        cycle_id = row.get("cycle_id", "")
        action = row.get("action", "")
        auth = bool_val(row.get("is_authorized_correction", "False"))
        c_status = cycle_status.get(cycle_id, "")
        if c_status == "closed" and "modified" in action.lower() and not auth:
            detected.append({
                "rule_id": "RULE-004",
                "anomaly_type": "closed_cycle_edit",
                "entity_type": "audit_event",
                "entity_id": row["audit_event_id"],
                "detail": f"cycle={cycle_id}(closed), action={action}, authorized={auth}",
            })
    return detected


def detect_untraceable_feedback(
    feedback: list[dict], employees: list[dict]
) -> list[dict]:
    """RULE-005: Find feedback with missing/invalid author_employee_id."""
    emp_ids = {r["employee_id"] for r in employees}
    detected = []
    for row in feedback:
        author = row.get("author_employee_id", "")
        if not author or author not in emp_ids:
            detected.append({
                "rule_id": "RULE-005",
                "anomaly_type": "untraceable_feedback",
                "entity_type": "feedback",
                "entity_id": row["feedback_id"],
                "detail": f"author_employee_id={author!r} is missing or not in employees",
            })
    return detected


# ---------------------------------------------------------------------------
# Metrics calculation
# ---------------------------------------------------------------------------

def compute_metrics(
    predictions: list[dict], ground_truth: list[dict]
) -> dict:
    """
    Compare predictions against ground truth.
    Returns per-category and overall metrics.
    """
    # Build sets of (anomaly_type, entity_id) for GT and predictions
    gt_set = {(r["anomaly_type"], r["entity_id"]) for r in ground_truth}
    pred_set = {(r["anomaly_type"], r["entity_id"]) for r in predictions}

    all_types = sorted({r["anomaly_type"] for r in ground_truth} |
                       {r["anomaly_type"] for r in predictions})

    per_category: dict[str, dict] = {}
    total_tp = total_fp = total_fn = 0

    for atype in all_types:
        gt_type = {eid for (t, eid) in gt_set if t == atype}
        pred_type = {eid for (t, eid) in pred_set if t == atype}

        tp = len(gt_type & pred_type)
        fp = len(pred_type - gt_type)
        fn = len(gt_type - pred_type)

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)

        per_category[atype] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "gt_count": len(gt_type),
            "pred_count": len(pred_type),
        }
        total_tp += tp
        total_fp += fp
        total_fn += fn

    overall_precision = safe_div(total_tp, total_tp + total_fp)
    overall_recall = safe_div(total_tp, total_tp + total_fn)
    overall_f1 = safe_div(
        2 * overall_precision * overall_recall,
        overall_precision + overall_recall
    )

    return {
        "per_category": per_category,
        "overall": {
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": round(overall_precision, 4),
            "recall": round(overall_recall, 4),
            "f1": round(overall_f1, 4),
        },
    }


# ---------------------------------------------------------------------------
# Markdown report writer
# ---------------------------------------------------------------------------

def write_eval_markdown(metrics: dict, predictions: list[dict], gt: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        "# PeoplePulse Anomaly Evaluation Report",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| True Positives  | {metrics['overall']['tp']} |",
        f"| False Positives | {metrics['overall']['fp']} |",
        f"| False Negatives | {metrics['overall']['fn']} |",
        f"| Precision | {metrics['overall']['precision']:.4f} |",
        f"| Recall    | {metrics['overall']['recall']:.4f} |",
        f"| F1 Score  | {metrics['overall']['f1']:.4f} |",
        "",
        "## Per-Category Metrics",
        "",
        "| Category | TP | FP | FN | Precision | Recall | F1 |",
        "|----------|----|----|----|-----------|--------|----|",
    ]

    for cat, m in metrics["per_category"].items():
        lines.append(
            f"| {cat} | {m['tp']} | {m['fp']} | {m['fn']} "
            f"| {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} |"
        )

    lines += [
        "",
        "## Predictions",
        "",
        f"Total predictions: {len(predictions)}",
        "",
        "| Rule | Type | Entity Type | Entity ID |",
        "|------|------|-------------|-----------|",
    ]
    for p in predictions:
        lines.append(
            f"| {p['rule_id']} | {p['anomaly_type']} | "
            f"{p['entity_type']} | {p['entity_id']} |"
        )

    lines += [
        "",
        "## Ground Truth",
        "",
        f"Total ground truth anomalies: {len(gt)}",
        "",
        "| Anomaly ID | Type | Entity Type | Entity ID | Rule |",
        "|------------|------|-------------|-----------|------|",
    ]
    for g in gt:
        lines.append(
            f"| {g['anomaly_id']} | {g['anomaly_type']} | "
            f"{g['entity_type']} | {g['entity_id']} | {g['rule_id']} |"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="PeoplePulse Anomaly Evaluator")
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--ground-truth", default=GROUND_TRUTH_PATH)
    parser.add_argument("--reports-dir", default=REPORTS_DIR)
    args = parser.parse_args()

    print("[Evaluator] Loading data...")
    employees     = load_csv(f"{args.data_dir}/employees.csv")
    goals         = load_csv(f"{args.data_dir}/goals.csv")
    key_results   = load_csv(f"{args.data_dir}/key_results.csv")
    check_ins     = load_csv(f"{args.data_dir}/check_ins.csv")
    feedback      = load_csv(f"{args.data_dir}/feedback.csv")
    audit_events  = load_csv(f"{args.data_dir}/audit_events.csv")
    review_cycles = load_csv(f"{args.data_dir}/review_cycles.csv")

    # Run all detection rules (NO ground truth access here)
    print("[Evaluator] Running detection rules...")
    predictions: list[dict] = []
    predictions += detect_goal_owner_mismatch(check_ins, goals)
    predictions += detect_progress_exceeds_scale(key_results)
    predictions += detect_reviewer_no_relationship(feedback, employees)
    predictions += detect_closed_cycle_edits(audit_events, review_cycles)
    predictions += detect_untraceable_feedback(feedback, employees)

    print(f"[Evaluator] Detected {len(predictions)} anomaly instances")

    # Now load ground truth separately for comparison
    print("[Evaluator] Loading ground truth for comparison...")
    ground_truth = load_csv(args.ground_truth)
    print(f"[Evaluator] Ground truth: {len(ground_truth)} entries")

    # Compute metrics
    metrics = compute_metrics(predictions, ground_truth)

    # Build report
    report = {
        "predictions": predictions,
        "ground_truth_count": len(ground_truth),
        "prediction_count": len(predictions),
        "metrics": metrics,
    }

    os.makedirs(args.reports_dir, exist_ok=True)
    json_path = f"{args.reports_dir}/evaluation_report.json"
    md_path = f"{args.reports_dir}/evaluation_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    write_eval_markdown(metrics, predictions, ground_truth, md_path)

    # Print summary
    print("\n[Evaluator] Results:")
    print(f"  {'Category':<30} {'TP':>4} {'FP':>4} {'FN':>4} {'P':>7} {'R':>7} {'F1':>7}")
    print(f"  {'-'*66}")
    for cat, m in metrics["per_category"].items():
        print(f"  {cat:<30} {m['tp']:>4} {m['fp']:>4} {m['fn']:>4} "
              f"{m['precision']:>7.4f} {m['recall']:>7.4f} {m['f1']:>7.4f}")
    print(f"  {'-'*66}")
    ov = metrics["overall"]
    print(f"  {'OVERALL':<30} {ov['tp']:>4} {ov['fp']:>4} {ov['fn']:>4} "
          f"{ov['precision']:>7.4f} {ov['recall']:>7.4f} {ov['f1']:>7.4f}")
    print(f"\n  Reports written to: {args.reports_dir}/")


if __name__ == "__main__":
    main()

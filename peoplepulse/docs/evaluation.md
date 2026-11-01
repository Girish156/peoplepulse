# Anomaly evaluation

## Detector rules

| Rule | Type | Signal |
|------|------|--------|
| RULE-001 | goal_owner_mismatch | Check-in employee ≠ goal owner |
| RULE-002 | progress_exceeds_scale | KR progress > allowed scale without rationale |
| RULE-003 | reviewer_no_relationship | Reviewer is not manager / authorized participant |
| RULE-004 | closed_cycle_edit | Mutation against a closed cycle (or seeded policy-violation event) |
| RULE-005 | untraceable_feedback | Missing/invalid author or evidence trail |

The detector never reads `data/ground_truth/*`.

## Metrics

`scripts/evaluate_anomalies.py` compares detector issue keys `(issue_type, entity_id)` to ground truth and reports precision, recall, F1, TP, FP, FN overall and per category. Zero denominators yield 0.0 rather than exceptions.

```bash
python scripts/evaluate_anomalies.py
```

Reports: `data/reports/evaluation_report.json` and `.md`.

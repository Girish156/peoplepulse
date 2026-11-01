"""
PeoplePulse Data Validation Script
====================================
Reads all CSV files from data/generated/, runs comprehensive checks,
reports intentional anomalies separately from accidental failures.

Exit code 0  → only intentional anomalies found (no unexpected failures)
Exit code 1  → unexpected failures detected
"""

import csv
import json
import os
import re
import sys
from pathlib import Path
from datetime import date


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = "data/generated"
REPORTS_DIR = "data/reports"
GROUND_TRUTH_PATH = "data/ground_truth/ground_truth.csv"

EXPECTED_ANOMALY_COUNT = 5
EXPECTED_ANOMALY_TYPES = {
    "goal_owner_mismatch",
    "progress_exceeds_scale",
    "reviewer_no_relationship",
    "closed_cycle_edit",
    "untraceable_feedback",
}

# Regex patterns for ID validation
ID_PATTERNS = {
    "employee_id":      r"^EMP-\d{6}$",
    "goal_id":          r"^GOAL-EMP-\d{6}-\d{3}$",
    "kr_id":            r"^KR-GOAL-EMP-\d{6}-\d{3}-\d{2}$",
    "check_in_id":      r"^CHK-EMP-\d{6}-\d{8}-\d{3}$",
    "review_id":        r"^REV-\d{4}-\d{6}$",
    "feedback_id":      r"^FBK-\d{6}$",
    "plan_id":          r"^DEV-EMP-\d{6}-\d{3}$",
    "evidence_id":      r"^EVD-\d{6}$",
    "audit_event_id":   r"^AUD-\d{9}$",
    "competency_id":    r"^COMP-\d{3}$",
    "cycle_id":         r"^CYCLE-\d{4}-H[12]$",
}

VALID_ENUMS = {
    "status_employee":   {"active", "on_leave", "terminated"},
    "status_goal":       {"draft", "active", "completed", "cancelled"},
    "status_kr":         {"on_track", "at_risk", "behind", "completed"},
    "status_review":     {"not_started", "in_progress", "completed", "calibrated"},
    "status_feedback":   {"submitted", "acknowledged", "archived"},
    "status_devplan":    {"draft", "active", "completed"},
    "feedback_type":     {"peer", "upward", "downward", "self"},
    "cycle_status":      {"draft", "active", "closed"},
    "evidence_type":     {"document", "link", "screenshot", "metric"},
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def load_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_ground_truth(path: str) -> list[dict]:
    return load_csv(path)


def parse_date(s: str):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def bool_val(s: str) -> bool:
    return str(s).lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Validation runner
# ---------------------------------------------------------------------------
class Validator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.failures: list[dict] = []
        self.warnings: list[dict] = []
        self.intentional_anomalies: list[dict] = []

        # Load all tables
        self.competencies   = load_csv(f"{data_dir}/competencies.csv")
        self.employees      = load_csv(f"{data_dir}/employees.csv")
        self.review_cycles  = load_csv(f"{data_dir}/review_cycles.csv")
        self.goals          = load_csv(f"{data_dir}/goals.csv")
        self.key_results    = load_csv(f"{data_dir}/key_results.csv")
        self.check_ins      = load_csv(f"{data_dir}/check_ins.csv")
        self.reviews        = load_csv(f"{data_dir}/reviews.csv")
        self.feedback       = load_csv(f"{data_dir}/feedback.csv")
        self.dev_plans      = load_csv(f"{data_dir}/development_plans.csv")
        self.evidence       = load_csv(f"{data_dir}/evidence.csv")
        self.audit_events   = load_csv(f"{data_dir}/audit_events.csv")

        # Build index sets for FK checks
        self.emp_ids    = {r["employee_id"] for r in self.employees}
        self.cycle_ids  = {r["cycle_id"] for r in self.review_cycles}
        self.goal_ids   = {r["goal_id"] for r in self.goals}
        self.kr_ids     = {r["kr_id"] for r in self.key_results}
        self.ci_ids     = {r["check_in_id"] for r in self.check_ins}
        self.rev_ids    = {r["review_id"] for r in self.reviews}
        self.fbk_ids    = {r["feedback_id"] for r in self.feedback}
        self.dp_ids     = {r["plan_id"] for r in self.dev_plans}
        self.evd_ids    = {r["evidence_id"] for r in self.evidence}
        self.aud_ids    = {r["audit_event_id"] for r in self.audit_events}
        self.comp_ids   = {r["competency_id"] for r in self.competencies}

        # Map goal_id → employee_id for mismatch checks
        self.goal_owner = {r["goal_id"]: r["employee_id"] for r in self.goals}
        # Map employee_id → manager_id
        self.emp_manager = {r["employee_id"]: r["manager_id"] for r in self.employees}
        # Map cycle_id → status
        self.cycle_status = {r["cycle_id"]: r["status"] for r in self.review_cycles}

    def fail(self, check: str, entity: str, entity_id: str, msg: str, is_anomaly: bool = False):
        record = {
            "check": check,
            "entity": entity,
            "entity_id": entity_id,
            "message": msg,
            "is_intentional_anomaly": is_anomaly,
        }
        if is_anomaly:
            self.intentional_anomalies.append(record)
        else:
            self.failures.append(record)

    def warn(self, check: str, entity: str, entity_id: str, msg: str):
        self.warnings.append({
            "check": check,
            "entity": entity,
            "entity_id": entity_id,
            "message": msg,
        })

    # ------------------------------------------------------------------
    # Check: primary key uniqueness
    # ------------------------------------------------------------------
    def check_pk_uniqueness(self):
        tables = [
            ("employees",        self.employees,     "employee_id"),
            ("review_cycles",    self.review_cycles,  "cycle_id"),
            ("goals",            self.goals,          "goal_id"),
            ("key_results",      self.key_results,    "kr_id"),
            ("check_ins",        self.check_ins,      "check_in_id"),
            ("reviews",          self.reviews,        "review_id"),
            ("feedback",         self.feedback,       "feedback_id"),
            ("development_plans",self.dev_plans,      "plan_id"),
            ("evidence",         self.evidence,       "evidence_id"),
            ("audit_events",     self.audit_events,   "audit_event_id"),
            ("competencies",     self.competencies,   "competency_id"),
        ]
        for table_name, rows, pk_col in tables:
            seen = {}
            for row in rows:
                val = row.get(pk_col, "")
                if val in seen:
                    self.fail("pk_uniqueness", table_name, val,
                              f"Duplicate {pk_col}: {val}")
                seen[val] = True

    # ------------------------------------------------------------------
    # Check: ID naming conventions
    # ------------------------------------------------------------------
    def check_id_patterns(self):
        checks = [
            (self.employees,    "employee_id"),
            (self.goals,        "goal_id"),
            (self.key_results,  "kr_id"),
            (self.check_ins,    "check_in_id"),
            (self.reviews,      "review_id"),
            (self.feedback,     "feedback_id"),
            (self.dev_plans,    "plan_id"),
            (self.evidence,     "evidence_id"),
            (self.audit_events, "audit_event_id"),
            (self.competencies, "competency_id"),
        ]
        for rows, id_col in checks:
            pattern = ID_PATTERNS.get(id_col)
            if not pattern:
                continue
            for row in rows:
                val = row.get(id_col, "")
                if not re.match(pattern, val):
                    self.fail("id_pattern", id_col, val,
                              f"ID {val!r} does not match pattern {pattern}")

        # Cycle IDs
        for row in self.review_cycles:
            val = row.get("cycle_id", "")
            if not re.match(ID_PATTERNS["cycle_id"], val):
                self.fail("id_pattern", "cycle_id", val,
                          f"Cycle ID {val!r} does not match pattern")

    # ------------------------------------------------------------------
    # Check: required fields not null
    # ------------------------------------------------------------------
    def check_required_fields(self):
        required = {
            "employees":        ["employee_id", "first_name", "last_name", "email", "department", "status"],
            "goals":            ["goal_id", "employee_id", "cycle_id", "title", "status"],
            "key_results":      ["kr_id", "goal_id", "target"],
            "check_ins":        ["check_in_id", "goal_id", "employee_id", "check_in_date"],
            "reviews":          ["review_id", "employee_id", "cycle_id", "status"],
            "feedback":         ["feedback_id", "subject_employee_id", "feedback_type", "content"],
            "development_plans":["plan_id", "employee_id", "competency_id", "title"],
            "competencies":     ["competency_id", "name", "description"],
        }
        table_map = {
            "employees": self.employees,
            "goals": self.goals,
            "key_results": self.key_results,
            "check_ins": self.check_ins,
            "reviews": self.reviews,
            "feedback": self.feedback,
            "development_plans": self.dev_plans,
            "competencies": self.competencies,
        }
        for table_name, fields in required.items():
            rows = table_map[table_name]
            for row in rows:
                for field in fields:
                    # author_employee_id is allowed null for untraceable_feedback anomaly
                    if field == "author_employee_id":
                        continue
                    val = row.get(field, "")
                    is_anomaly_row = bool_val(row.get("anomaly_flag", "False"))
                    if val == "" or val is None:
                        self.fail("required_field", table_name,
                                  row.get(list(row.keys())[0], "?"),
                                  f"Required field {field!r} is empty",
                                  is_anomaly=is_anomaly_row)

    # ------------------------------------------------------------------
    # Check: foreign key integrity
    # ------------------------------------------------------------------
    def check_foreign_keys(self):
        # Goals → employees and cycles
        for row in self.goals:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["employee_id"] not in self.emp_ids:
                self.fail("fk_integrity", "goals", row["goal_id"],
                          f"employee_id {row['employee_id']} not in employees",
                          is_anomaly=is_anomaly)
            if row["cycle_id"] not in self.cycle_ids:
                self.fail("fk_integrity", "goals", row["goal_id"],
                          f"cycle_id {row['cycle_id']} not in review_cycles",
                          is_anomaly=is_anomaly)

        # Key results → goals
        for row in self.key_results:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["goal_id"] not in self.goal_ids:
                self.fail("fk_integrity", "key_results", row["kr_id"],
                          f"goal_id {row['goal_id']} not in goals",
                          is_anomaly=is_anomaly)

        # Check-ins → goals and employees
        for row in self.check_ins:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["goal_id"] not in self.goal_ids:
                self.fail("fk_integrity", "check_ins", row["check_in_id"],
                          f"goal_id {row['goal_id']} not in goals",
                          is_anomaly=is_anomaly)
            if row["employee_id"] not in self.emp_ids:
                self.fail("fk_integrity", "check_ins", row["check_in_id"],
                          f"employee_id {row['employee_id']} not in employees",
                          is_anomaly=is_anomaly)

        # Reviews → employees and cycles
        for row in self.reviews:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["employee_id"] not in self.emp_ids:
                self.fail("fk_integrity", "reviews", row["review_id"],
                          f"employee_id {row['employee_id']} not in employees",
                          is_anomaly=is_anomaly)
            if row["cycle_id"] not in self.cycle_ids:
                self.fail("fk_integrity", "reviews", row["review_id"],
                          f"cycle_id {row['cycle_id']} not in review_cycles",
                          is_anomaly=is_anomaly)

        # Feedback → subject employees (author may be null/invalid for anomaly)
        for row in self.feedback:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["subject_employee_id"] not in self.emp_ids:
                self.fail("fk_integrity", "feedback", row["feedback_id"],
                          f"subject_employee_id {row['subject_employee_id']} not in employees",
                          is_anomaly=is_anomaly)
            author = row.get("author_employee_id", "")
            if author and author not in self.emp_ids:
                self.fail("fk_integrity", "feedback", row["feedback_id"],
                          f"author_employee_id {author} not in employees",
                          is_anomaly=is_anomaly)

        # Development plans → employees and competencies
        for row in self.dev_plans:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["employee_id"] not in self.emp_ids:
                self.fail("fk_integrity", "development_plans", row["plan_id"],
                          f"employee_id {row['employee_id']} not in employees",
                          is_anomaly=is_anomaly)
            if row["competency_id"] not in self.comp_ids:
                self.fail("fk_integrity", "development_plans", row["plan_id"],
                          f"competency_id {row['competency_id']} not in competencies",
                          is_anomaly=is_anomaly)

        # Evidence → check_ins
        for row in self.evidence:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            if row["check_in_id"] not in self.ci_ids:
                self.fail("fk_integrity", "evidence", row["evidence_id"],
                          f"check_in_id {row['check_in_id']} not in check_ins",
                          is_anomaly=is_anomaly)

    # ------------------------------------------------------------------
    # Check: enum values
    # ------------------------------------------------------------------
    def check_enums(self):
        for row in self.employees:
            if row["status"] not in VALID_ENUMS["status_employee"]:
                self.fail("enum_check", "employees", row["employee_id"],
                          f"Invalid status: {row['status']!r}")

        for row in self.goals:
            if row["status"] not in VALID_ENUMS["status_goal"]:
                self.fail("enum_check", "goals", row["goal_id"],
                          f"Invalid status: {row['status']!r}")

        for row in self.key_results:
            if row["status"] not in VALID_ENUMS["status_kr"]:
                self.fail("enum_check", "key_results", row["kr_id"],
                          f"Invalid status: {row['status']!r}")

        for row in self.reviews:
            if row["status"] not in VALID_ENUMS["status_review"]:
                self.fail("enum_check", "reviews", row["review_id"],
                          f"Invalid status: {row['status']!r}")

        for row in self.feedback:
            if row["feedback_type"] not in VALID_ENUMS["feedback_type"]:
                self.fail("enum_check", "feedback", row["feedback_id"],
                          f"Invalid feedback_type: {row['feedback_type']!r}")

        for row in self.review_cycles:
            if row["status"] not in VALID_ENUMS["cycle_status"]:
                self.fail("enum_check", "review_cycles", row["cycle_id"],
                          f"Invalid status: {row['status']!r}")

    # ------------------------------------------------------------------
    # Check: date ordering
    # ------------------------------------------------------------------
    def check_date_ordering(self):
        for row in self.employees:
            hire = parse_date(row.get("hire_date", ""))
            term = parse_date(row.get("termination_date", ""))
            if hire and term and term <= hire:
                self.fail("date_ordering", "employees", row["employee_id"],
                          f"termination_date {term} must be after hire_date {hire}")

        for row in self.goals:
            start = parse_date(row.get("start_date", ""))
            due = parse_date(row.get("due_date", ""))
            if start and due and due <= start:
                self.fail("date_ordering", "goals", row["goal_id"],
                          f"due_date {due} must be after start_date {start}")

        for row in self.dev_plans:
            start = parse_date(row.get("start_date", ""))
            end = parse_date(row.get("target_completion_date", ""))
            if start and end and end <= start:
                self.fail("date_ordering", "development_plans", row["plan_id"],
                          f"target_completion_date {end} must be after start_date {start}")

    # ------------------------------------------------------------------
    # Check: weight validation
    # ------------------------------------------------------------------
    def check_weights(self):
        for row in self.goals:
            try:
                w = float(row.get("weight", "0"))
                if w < 0:
                    self.fail("weight_check", "goals", row["goal_id"],
                              f"weight {w} must be non-negative")
            except ValueError:
                self.fail("weight_check", "goals", row["goal_id"],
                          f"weight {row.get('weight')!r} is not numeric")

    # ------------------------------------------------------------------
    # Check: computed progress vs stored values
    # ------------------------------------------------------------------
    def check_progress(self):
        for row in self.key_results:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            try:
                target = float(row.get("target", "0"))
                actual = float(row.get("actual", "0"))
                stored = float(row.get("computed_progress", "0"))
                scale = float(row.get("allowed_progress_scale", "1.0"))

                if target > 0:
                    expected = round(actual / target, 4)
                    if abs(expected - stored) > 0.01:
                        self.fail("progress_check", "key_results", row["kr_id"],
                                  f"computed_progress {stored} != actual/target {expected}",
                                  is_anomaly=is_anomaly)
                    # Check scale
                    if actual / target > scale:
                        self.fail("progress_scale", "key_results", row["kr_id"],
                                  f"actual/target={actual/target:.4f} exceeds allowed_scale={scale}",
                                  is_anomaly=is_anomaly)
            except (ValueError, ZeroDivisionError):
                pass

    # ------------------------------------------------------------------
    # Check: goal owner mismatch in check-ins
    # ------------------------------------------------------------------
    def check_goal_owner_mismatch(self):
        for row in self.check_ins:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            goal_id = row.get("goal_id", "")
            ci_emp = row.get("employee_id", "")
            goal_owner = self.goal_owner.get(goal_id)
            if goal_owner and ci_emp != goal_owner:
                self.fail("goal_owner_mismatch", "check_ins", row["check_in_id"],
                          f"check_in employee {ci_emp} != goal owner {goal_owner}",
                          is_anomaly=is_anomaly)

    # ------------------------------------------------------------------
    # Check: reviewer relationships
    # ------------------------------------------------------------------
    def check_reviewer_relationships(self):
        for row in self.feedback:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            author = row.get("author_employee_id", "")
            subject = row.get("subject_employee_id", "")
            if not author or author not in self.emp_ids:
                # untraceable feedback anomaly
                self.fail("untraceable_feedback", "feedback", row["feedback_id"],
                          f"author_employee_id {author!r} not found in employees",
                          is_anomaly=is_anomaly)
                continue
            mgr = self.emp_manager.get(subject, "")
            if author != mgr:
                # Not the manager — check if it's a peer review (allowed) or anomaly
                if is_anomaly:
                    self.fail("reviewer_no_relationship", "feedback", row["feedback_id"],
                              f"author {author} is not manager of subject {subject}",
                              is_anomaly=True)

    # ------------------------------------------------------------------
    # Check: closed cycle edits in audit events
    # ------------------------------------------------------------------
    def check_closed_cycle_edits(self):
        for row in self.audit_events:
            is_anomaly = bool_val(row.get("anomaly_flag", "False"))
            cycle_id = row.get("cycle_id", "")
            action = row.get("action", "")
            auth = bool_val(row.get("is_authorized_correction", "False"))
            c_status = self.cycle_status.get(cycle_id, "")

            if c_status == "closed" and "modified" in action.lower() and not auth:
                self.fail("closed_cycle_edit", "audit_events", row["audit_event_id"],
                          f"Unauthorized modification in closed cycle {cycle_id}",
                          is_anomaly=is_anomaly)

    # ------------------------------------------------------------------
    # Check: review lifecycle transitions
    # ------------------------------------------------------------------
    def check_review_lifecycle(self):
        valid_transitions = {
            "not_started": {"in_progress"},
            "in_progress": {"completed"},
            "completed": {"calibrated"},
            "calibrated": set(),
        }
        # We validate that closed cycles have calibrated reviews
        closed_cycle_ids = {cid for cid, s in self.cycle_status.items() if s == "closed"}
        for row in self.reviews:
            if row["cycle_id"] in closed_cycle_ids:
                if row["status"] not in ("calibrated", "completed"):
                    self.warn("review_lifecycle", "reviews", row["review_id"],
                              f"Review in closed cycle should be calibrated, got: {row['status']}")

    # ------------------------------------------------------------------
    # Check: anomaly counts
    # ------------------------------------------------------------------
    def check_anomaly_counts(self):
        gt = load_ground_truth(GROUND_TRUTH_PATH)
        actual_count = len(gt)
        if actual_count != EXPECTED_ANOMALY_COUNT:
            self.fail("anomaly_count", "ground_truth", "N/A",
                      f"Expected {EXPECTED_ANOMALY_COUNT} anomalies, found {actual_count}")

        actual_types = {row["anomaly_type"] for row in gt}
        missing = EXPECTED_ANOMALY_TYPES - actual_types
        if missing:
            self.fail("anomaly_types", "ground_truth", "N/A",
                      f"Missing anomaly types: {missing}")
        extra = actual_types - EXPECTED_ANOMALY_TYPES
        if extra:
            self.fail("anomaly_types", "ground_truth", "N/A",
                      f"Unexpected anomaly types: {extra}")

    # ------------------------------------------------------------------
    # Run all checks
    # ------------------------------------------------------------------
    def run(self):
        self.check_pk_uniqueness()
        self.check_id_patterns()
        self.check_required_fields()
        self.check_foreign_keys()
        self.check_enums()
        self.check_date_ordering()
        self.check_weights()
        self.check_progress()
        self.check_goal_owner_mismatch()
        self.check_reviewer_relationships()
        self.check_closed_cycle_edits()
        self.check_review_lifecycle()
        self.check_anomaly_counts()


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def build_report(validator: Validator) -> dict:
    return {
        "summary": {
            "total_failures": len(validator.failures),
            "total_warnings": len(validator.warnings),
            "total_intentional_anomalies": len(validator.intentional_anomalies),
            "passed": len(validator.failures) == 0,
        },
        "failures": validator.failures,
        "warnings": validator.warnings,
        "intentional_anomalies": validator.intentional_anomalies,
    }


def write_markdown_report(report: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        "# PeoplePulse Data Validation Report",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Unexpected Failures | {report['summary']['total_failures']} |",
        f"| Warnings | {report['summary']['total_warnings']} |",
        f"| Intentional Anomalies | {report['summary']['total_intentional_anomalies']} |",
        f"| Overall Status | {'✅ PASS' if report['summary']['passed'] else '❌ FAIL'} |",
        "",
    ]

    if report["failures"]:
        lines += [
            "## ❌ Unexpected Failures",
            "",
            "| Check | Entity | Entity ID | Message |",
            "|-------|--------|-----------|---------|",
        ]
        for f in report["failures"]:
            lines.append(
                f"| {f['check']} | {f['entity']} | {f['entity_id']} | {f['message']} |"
            )
        lines.append("")

    if report["intentional_anomalies"]:
        lines += [
            "## ⚠️ Intentional Anomalies (Expected)",
            "",
            "| Check | Entity | Entity ID | Message |",
            "|-------|--------|-----------|---------|",
        ]
        for a in report["intentional_anomalies"]:
            lines.append(
                f"| {a['check']} | {a['entity']} | {a['entity_id']} | {a['message']} |"
            )
        lines.append("")

    if report["warnings"]:
        lines += [
            "## ⚠️ Warnings",
            "",
            "| Check | Entity | Entity ID | Message |",
            "|-------|--------|-----------|---------|",
        ]
        for w in report["warnings"]:
            lines.append(
                f"| {w['check']} | {w['entity']} | {w['entity_id']} | {w['message']} |"
            )
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="PeoplePulse Data Validator")
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--reports-dir", default=REPORTS_DIR)
    args = parser.parse_args()

    print("[Validator] Loading data files...")
    validator = Validator(args.data_dir)

    print("[Validator] Running checks...")
    validator.run()

    report = build_report(validator)

    os.makedirs(args.reports_dir, exist_ok=True)
    json_path = f"{args.reports_dir}/validation_report.json"
    md_path = f"{args.reports_dir}/validation_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    write_markdown_report(report, md_path)

    print(f"\n[Validator] Results:")
    print(f"  Unexpected failures  : {report['summary']['total_failures']}")
    print(f"  Intentional anomalies: {report['summary']['total_intentional_anomalies']}")
    print(f"  Warnings             : {report['summary']['total_warnings']}")
    print(f"  Status               : {'PASS' if report['summary']['passed'] else 'FAIL'}")
    print(f"\n  Report written to: {json_path}")
    print(f"  Report written to: {md_path}")

    if not report["summary"]["passed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

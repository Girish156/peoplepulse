"""
PeoplePulse Synthetic Data Generator
=====================================
Generates deterministic synthetic data for the PeoplePulse platform.
All randomness is seeded — same seed + mode = identical output + checksums.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GENERATOR_VERSION = "1.0.0"
FIXED_GENERATION_TIMESTAMP = "2026-01-01T00:00:00Z"
BASE_DATE = date(2026, 1, 1)

# Reference date used to compute hire dates and other timestamps
EPOCH_DATE = date(2020, 1, 1)

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Susan", "Richard", "Jessica",
    "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Lisa", "Christopher",
    "Nancy", "Daniel", "Betty", "Matthew", "Margaret", "Anthony", "Sandra",
    "Mark", "Ashley", "Donald", "Dorothy", "Steven", "Kimberly", "Paul",
    "Emily", "Andrew", "Donna", "Joshua", "Michelle", "Kenneth", "Carol",
    "Kevin", "Amanda", "Brian", "Melissa", "George", "Deborah", "Timothy",
    "Stephanie", "Ronald", "Rebecca", "Edward", "Sharon", "Jason", "Laura",
    "Jeffrey", "Cynthia", "Ryan", "Kathleen", "Jacob", "Amy", "Gary",
    "Angela", "Nicholas", "Shirley", "Eric", "Anna", "Jonathan", "Brenda",
    "Stephen", "Pamela", "Larry", "Emma", "Justin", "Nicole", "Scott",
    "Helen", "Brandon", "Samantha", "Benjamin", "Katherine", "Samuel",
    "Christine", "Raymond", "Debra", "Gregory", "Rachel", "Frank", "Carolyn",
    "Alexander", "Janet", "Patrick", "Catherine", "Jack", "Maria", "Dennis",
    "Heather", "Jerry", "Diane", "Tyler", "Julie", "Aaron", "Joyce",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris",
    "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
    "Cooper", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos",
    "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks", "Chavez",
    "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long",
    "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
]

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Marketing", "Sales",
    "Human Resources", "Finance", "Operations", "Customer Success", "Legal",
    "Data Science", "Security", "IT", "Research", "Strategy",
]

JOB_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer",
    "Product Manager", "Senior Product Manager", "Director of Product",
    "UX Designer", "Senior Designer", "Design Lead",
    "Marketing Manager", "Content Strategist", "Growth Manager",
    "Account Executive", "Sales Manager", "Business Development Rep",
    "HR Business Partner", "Recruiter", "HR Manager",
    "Financial Analyst", "Senior Analyst", "Finance Manager",
    "Operations Manager", "Program Manager", "Project Manager",
    "Customer Success Manager", "Support Engineer", "Account Manager",
    "Data Scientist", "ML Engineer", "Data Analyst",
    "Security Engineer", "IT Administrator", "Systems Administrator",
    "Research Scientist", "Technical Writer", "Strategy Analyst",
]

EMAIL_DOMAINS = ["@example.com", "@corp.example.com"]

STATUSES_EMPLOYEE = ["active", "on_leave", "terminated"]
STATUSES_GOAL = ["draft", "active", "completed", "cancelled"]
STATUSES_KR = ["on_track", "at_risk", "behind", "completed"]
STATUSES_REVIEW = ["not_started", "in_progress", "completed", "calibrated"]
STATUSES_FEEDBACK = ["submitted", "acknowledged", "archived"]
STATUSES_DEV_PLAN = ["draft", "active", "completed"]

COMPETENCY_NAMES = [
    "Communication", "Leadership", "Problem Solving", "Teamwork",
    "Adaptability", "Technical Expertise", "Customer Focus",
    "Innovation", "Execution Excellence", "Strategic Thinking",
]

COMPETENCY_DESCRIPTIONS = [
    "Ability to convey ideas clearly and listen actively",
    "Inspiring and guiding teams toward shared goals",
    "Identifying root causes and developing effective solutions",
    "Collaborating effectively within and across teams",
    "Embracing change and thriving in dynamic environments",
    "Deep proficiency in relevant technical domains",
    "Prioritizing customer needs in all decisions",
    "Generating creative ideas and driving improvements",
    "Delivering results with quality and efficiency",
    "Thinking beyond the immediate to shape long-term direction",
]

GOAL_TITLE_TEMPLATES = [
    "Improve {} performance by {}%",
    "Launch {} initiative for {} quarter",
    "Reduce {} time by {}%",
    "Increase {} adoption to {}%",
    "Deliver {} project on schedule",
    "Complete {} certification",
    "Build {} capability within team",
    "Optimize {} workflow efficiency",
    "Establish {} best practices",
    "Drive {} revenue growth",
]

GOAL_DOMAINS = [
    "system", "pipeline", "product", "customer", "team", "process",
    "platform", "service", "feature", "infrastructure",
]

FEEDBACK_TYPES = ["peer", "upward", "downward", "self"]
AUDIT_ACTIONS = [
    "created", "updated", "deleted", "submitted", "approved",
    "rejected", "modified", "reviewed", "escalated",
]
AUDIT_ENTITY_TYPES = ["goal", "review", "feedback", "check_in", "development_plan"]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def fmt_employee_id(n: int) -> str:
    return f"EMP-{n:06d}"


def fmt_goal_id(emp_n: int, seq: int) -> str:
    return f"GOAL-EMP-{emp_n:06d}-{seq:03d}"


def fmt_kr_id(goal_id: str, seq: int) -> str:
    return f"KR-{goal_id}-{seq:02d}"


def fmt_checkin_id(emp_n: int, d: date, seq: int) -> str:
    return f"CHK-EMP-{emp_n:06d}-{d.strftime('%Y%m%d')}-{seq:03d}"


def fmt_review_id(n: int) -> str:
    return f"REV-2026-{n:06d}"


def fmt_feedback_id(n: int) -> str:
    return f"FBK-{n:06d}"


def fmt_dev_plan_id(emp_n: int, seq: int) -> str:
    return f"DEV-EMP-{emp_n:06d}-{seq:03d}"


def fmt_evidence_id(n: int) -> str:
    return f"EVD-{n:06d}"


def fmt_audit_id(n: int) -> str:
    return f"AUD-{n:09d}"


def fmt_issue_id(n: int) -> str:
    return f"ISS-{n:09d}"


def date_to_str(d: date) -> str:
    return d.isoformat()


def offset_date(base: date, days: int) -> date:
    return base + timedelta(days=int(days))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Data Generators
# ---------------------------------------------------------------------------

class DataGenerator:
    def __init__(self, seed: int, mode: str, output_dir: str, ground_truth_dir: str):
        self.seed = seed
        self.mode = mode
        self.output_dir = output_dir
        self.ground_truth_dir = ground_truth_dir
        self.rng = np.random.default_rng(seed)

        if mode == "small":
            self.n_employees = 100
            self.n_managers = 20
            self.n_goals = 300
            self.n_checkins = 600
        else:
            self.n_employees = 3000
            self.n_managers = 500
            self.n_goals = 10000
            self.n_checkins = 20000

        # Storage for generated data (list of dicts)
        self.competencies: list[dict] = []
        self.employees: list[dict] = []
        self.review_cycles: list[dict] = []
        self.goals: list[dict] = []
        self.key_results: list[dict] = []
        self.check_ins: list[dict] = []
        self.reviews: list[dict] = []
        self.feedback: list[dict] = []
        self.development_plans: list[dict] = []
        self.evidence: list[dict] = []
        self.audit_events: list[dict] = []

        # Ground truth anomalies
        self.ground_truth: list[dict] = []

    # ------------------------------------------------------------------
    # Step 1: Competencies
    # ------------------------------------------------------------------
    def generate_competencies(self):
        for i, (name, desc) in enumerate(zip(COMPETENCY_NAMES, COMPETENCY_DESCRIPTIONS), 1):
            self.competencies.append({
                "competency_id": f"COMP-{i:03d}",
                "name": name,
                "description": desc,
                "is_active": True,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 2: Employees
    # ------------------------------------------------------------------
    def generate_employees(self):
        n = self.n_employees
        n_mgr = self.n_managers

        # Pre-generate name pool deterministically
        fn_idx = self.rng.integers(0, len(FIRST_NAMES), size=n)
        ln_idx = self.rng.integers(0, len(LAST_NAMES), size=n)
        dept_idx = self.rng.integers(0, len(DEPARTMENTS), size=n)
        title_idx = self.rng.integers(0, len(JOB_TITLES), size=n)
        domain_idx = self.rng.integers(0, len(EMAIL_DOMAINS), size=n)
        hire_offsets = self.rng.integers(0, 365 * 6, size=n)  # within 6 years of epoch
        status_weights = self.rng.integers(0, 100, size=n)
        salary_base = self.rng.integers(60000, 200000, size=n)

        manager_pool = list(range(1, n_mgr + 1))  # employee numbers that are managers

        for i in range(1, n + 1):
            idx = i - 1
            first = FIRST_NAMES[fn_idx[idx]]
            last = LAST_NAMES[ln_idx[idx]]
            # Make email unique by appending employee number
            email_local = f"{first.lower()}.{last.lower()}.{i}"
            domain = EMAIL_DOMAINS[domain_idx[idx]]
            email = f"{email_local}{domain}"

            hire_date = offset_date(EPOCH_DATE, int(hire_offsets[idx]))

            # Status: 85% active, 10% on_leave, 5% terminated
            sw = int(status_weights[idx])
            if sw < 85:
                status = "active"
                termination_date = ""
            elif sw < 95:
                status = "on_leave"
                termination_date = ""
            else:
                status = "terminated"
                term_offset = self.rng.integers(30, 365)
                termination_date = date_to_str(offset_date(hire_date, int(term_offset)))

            # Manager assignment: first n_mgr employees are managers
            # Non-managers get a random manager
            is_manager = (i <= n_mgr)
            if i == 1:
                manager_id = ""  # top-level
            elif is_manager:
                # Managers report to a manager earlier in the list
                mgr_num = int(self.rng.integers(1, i))
                manager_id = fmt_employee_id(mgr_num)
            else:
                mgr_num = manager_pool[int(self.rng.integers(0, len(manager_pool)))]
                manager_id = fmt_employee_id(mgr_num)

            self.employees.append({
                "employee_id": fmt_employee_id(i),
                "first_name": first,
                "last_name": last,
                "email": email,
                "department": DEPARTMENTS[dept_idx[idx]],
                "job_title": JOB_TITLES[title_idx[idx]],
                "manager_id": manager_id,
                "hire_date": date_to_str(hire_date),
                "termination_date": termination_date,
                "status": status,
                "salary": int(salary_base[idx]),
                "is_manager": is_manager,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 3: Review Cycles
    # ------------------------------------------------------------------
    def generate_review_cycles(self):
        cycles = [
            {
                "cycle_id": "CYCLE-2025-H1",
                "name": "2025 H1 Performance Review",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
                "status": "closed",
                "is_active": False,
                "created_at": "2025-01-01",
                "updated_at": "2025-07-15",
            },
            {
                "cycle_id": "CYCLE-2025-H2",
                "name": "2025 H2 Performance Review",
                "start_date": "2025-07-01",
                "end_date": "2025-12-31",
                "status": "closed",
                "is_active": False,
                "created_at": "2025-07-01",
                "updated_at": "2026-01-15",
            },
            {
                "cycle_id": "CYCLE-2026-H1",
                "name": "2026 H1 Performance Review",
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
                "status": "active",
                "is_active": True,
                "created_at": "2026-01-01",
                "updated_at": "2026-01-01",
            },
            {
                "cycle_id": "CYCLE-2026-H2",
                "name": "2026 H2 Performance Review",
                "start_date": "2026-07-01",
                "end_date": "2026-12-31",
                "status": "draft",
                "is_active": False,
                "created_at": "2026-01-01",
                "updated_at": "2026-01-01",
            },
        ]
        self.review_cycles = cycles

    # ------------------------------------------------------------------
    # Step 4: Goals
    # ------------------------------------------------------------------
    def generate_goals(self):
        n = self.n_goals
        n_emp = self.n_employees

        # Valid cycles for goal assignment: active + closed (not draft)
        valid_cycles = ["CYCLE-2025-H1", "CYCLE-2025-H2", "CYCLE-2026-H1"]
        cycle_statuses = {
            "CYCLE-2025-H1": "closed",
            "CYCLE-2025-H2": "closed",
            "CYCLE-2026-H1": "active",
        }

        # Track goal sequence per employee
        emp_goal_seq: dict[int, int] = {}

        emp_indices = self.rng.integers(1, n_emp + 1, size=n)
        cycle_indices = self.rng.integers(0, len(valid_cycles), size=n)
        status_rolls = self.rng.integers(0, 100, size=n)
        weight_vals = self.rng.integers(1, 11, size=n)  # 1-10
        start_offsets = self.rng.integers(0, 60, size=n)
        due_offsets = self.rng.integers(60, 180, size=n)
        domain_idx = self.rng.integers(0, len(GOAL_DOMAINS), size=n)
        tmpl_idx = self.rng.integers(0, len(GOAL_TITLE_TEMPLATES), size=n)
        pct_vals = self.rng.integers(10, 51, size=n)

        for i in range(n):
            emp_num = int(emp_indices[i])
            seq = emp_goal_seq.get(emp_num, 0) + 1
            emp_goal_seq[emp_num] = seq

            goal_id = fmt_goal_id(emp_num, seq)
            cycle_id = valid_cycles[int(cycle_indices[i])]
            c_status = cycle_statuses[cycle_id]

            # Goal status relative to cycle status
            sr = int(status_rolls[i])
            if c_status == "closed":
                status = "completed" if sr < 70 else "cancelled"
            else:
                if sr < 20:
                    status = "draft"
                elif sr < 80:
                    status = "active"
                else:
                    status = "completed"

            start_d = offset_date(BASE_DATE, int(start_offsets[i]))
            due_d = offset_date(start_d, int(due_offsets[i]))

            title = GOAL_TITLE_TEMPLATES[int(tmpl_idx[i])].format(
                GOAL_DOMAINS[int(domain_idx[i])], int(pct_vals[i])
            )

            self.goals.append({
                "goal_id": goal_id,
                "employee_id": fmt_employee_id(emp_num),
                "cycle_id": cycle_id,
                "title": title,
                "description": f"Objective for {cycle_id}: {title}",
                "status": status,
                "weight": float(int(weight_vals[i])),
                "start_date": date_to_str(start_d),
                "due_date": date_to_str(due_d),
                "completion_date": date_to_str(due_d) if status == "completed" else "",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 5: Key Results
    # ------------------------------------------------------------------
    def generate_key_results(self):
        kr_seq = 0
        kr_per_goal = self.rng.integers(2, 4, size=len(self.goals))  # 2 or 3

        # Pre-generate values
        targets = self.rng.integers(10, 101, size=len(self.goals) * 3)
        actuals_pct = self.rng.integers(0, 101, size=len(self.goals) * 3)
        scales = self.rng.choice([1.0, 1.2, 1.5], size=len(self.goals) * 3)

        val_i = 0
        for g_idx, goal in enumerate(self.goals):
            n_kr = int(kr_per_goal[g_idx])
            for k in range(1, n_kr + 1):
                kr_seq += 1
                target = float(int(targets[val_i]))
                pct = float(int(actuals_pct[val_i]))
                actual = round(target * pct / 100.0, 2)
                scale = float(scales[val_i])
                progress = round(actual / target, 4) if target > 0 else 0.0

                self.key_results.append({
                    "kr_id": fmt_kr_id(goal["goal_id"], k),
                    "goal_id": goal["goal_id"],
                    "employee_id": goal["employee_id"],
                    "title": f"Key Result {k} for {goal['goal_id']}",
                    "description": f"Measurable outcome {k}",
                    "target": target,
                    "actual": actual,
                    "unit": "percent",
                    "allowed_progress_scale": scale,
                    "computed_progress": progress,
                    "status": "completed" if pct >= 90 else ("on_track" if pct >= 50 else "at_risk"),
                    "anomaly_flag": False,
                    "created_at": date_to_str(BASE_DATE),
                    "updated_at": date_to_str(BASE_DATE),
                })
                val_i += 1

    # ------------------------------------------------------------------
    # Step 6: Check-ins
    # ------------------------------------------------------------------
    def generate_checkins(self):
        n = self.n_checkins
        n_goals = len(self.goals)

        goal_indices = self.rng.integers(0, n_goals, size=n)
        date_offsets = self.rng.integers(0, 180, size=n)
        progress_vals = self.rng.integers(0, 101, size=n)
        seq_tracker: dict[tuple, int] = {}

        for i in range(n):
            goal = self.goals[int(goal_indices[i])]
            emp_id = goal["employee_id"]
            emp_num = int(emp_id.split("-")[1])
            checkin_date = offset_date(BASE_DATE, int(date_offsets[i]))
            key = (emp_num, checkin_date)
            seq = seq_tracker.get(key, 0) + 1
            seq_tracker[key] = seq

            self.check_ins.append({
                "check_in_id": fmt_checkin_id(emp_num, checkin_date, seq),
                "goal_id": goal["goal_id"],
                "employee_id": emp_id,
                "check_in_date": date_to_str(checkin_date),
                "progress_update": float(int(progress_vals[i])),
                "notes": f"Progress update for {goal['goal_id']} on {date_to_str(checkin_date)}",
                "blockers": "",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 7: Reviews
    # ------------------------------------------------------------------
    def generate_reviews(self):
        rev_seq = 0
        # Only for closed and active cycles
        valid_cycles = ["CYCLE-2025-H1", "CYCLE-2025-H2", "CYCLE-2026-H1"]
        cycle_statuses = {
            "CYCLE-2025-H1": "closed",
            "CYCLE-2025-H2": "closed",
            "CYCLE-2026-H1": "active",
        }

        n_reviews = min(self.n_employees, 200 if self.mode == "small" else 2000)
        emp_indices = self.rng.integers(0, self.n_employees, size=n_reviews)
        cycle_indices = self.rng.integers(0, len(valid_cycles), size=n_reviews)
        rating_vals = self.rng.integers(1, 6, size=n_reviews)
        mgr_rating_vals = self.rng.integers(1, 6, size=n_reviews)
        seen = set()

        for i in range(n_reviews):
            emp = self.employees[int(emp_indices[i])]
            cycle_id = valid_cycles[int(cycle_indices[i])]
            key = (emp["employee_id"], cycle_id)
            if key in seen:
                continue
            seen.add(key)

            rev_seq += 1
            c_status = cycle_statuses[cycle_id]

            if c_status == "closed":
                status = "calibrated"
            else:
                status = self.rng.choice(["not_started", "in_progress", "completed"])

            # Find manager
            mgr_id = emp["manager_id"] if emp["manager_id"] else emp["employee_id"]

            self.reviews.append({
                "review_id": fmt_review_id(rev_seq),
                "employee_id": emp["employee_id"],
                "reviewer_id": mgr_id,
                "cycle_id": cycle_id,
                "status": status,
                "self_rating": float(int(rating_vals[i])),
                "manager_rating": float(int(mgr_rating_vals[i])),
                "overall_rating": round((int(rating_vals[i]) + int(mgr_rating_vals[i])) / 2, 2),
                "strengths": f"Strong performance in key areas",
                "areas_for_improvement": f"Opportunity to grow in strategic thinking",
                "submitted_at": date_to_str(BASE_DATE) if status in ("completed", "calibrated") else "",
                "calibrated_at": date_to_str(BASE_DATE) if status == "calibrated" else "",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 8: Feedback
    # ------------------------------------------------------------------
    def generate_feedback(self):
        n_feedback = min(self.n_employees * 2, 400 if self.mode == "small" else 6000)
        n_emp = self.n_employees

        type_indices = self.rng.integers(0, len(FEEDBACK_TYPES), size=n_feedback)
        rating_vals = self.rng.integers(1, 6, size=n_feedback)
        emp_indices = self.rng.integers(0, n_emp, size=n_feedback)

        # Build mapping for peer lookups (employees by manager and department)
        dept_emps: dict[str, list[dict]] = {}
        for emp in self.employees:
            dept = emp.get("department", "General")
            dept_emps.setdefault(dept, []).append(emp)

        for i in range(n_feedback):
            ftype = FEEDBACK_TYPES[int(type_indices[i])]
            curr_emp = self.employees[int(emp_indices[i])]
            mgr_id = curr_emp.get("manager_id")

            if ftype == "downward":
                if not mgr_id:
                    continue
                author_id = mgr_id
                subject_id = curr_emp["employee_id"]
            elif ftype == "upward":
                if not mgr_id:
                    continue
                author_id = curr_emp["employee_id"]
                subject_id = mgr_id
            elif ftype == "self":
                author_id = curr_emp["employee_id"]
                subject_id = curr_emp["employee_id"]
            else:  # peer
                peers = dept_emps.get(curr_emp.get("department", ""), [])
                candidate_peers = [p for p in peers if p["employee_id"] != curr_emp["employee_id"]]
                if not candidate_peers:
                    continue
                chosen_peer = candidate_peers[int(self.rng.integers(0, len(candidate_peers)))]
                author_id = chosen_peer["employee_id"]
                subject_id = curr_emp["employee_id"]

            fbk_id = fmt_feedback_id(len(self.feedback) + 1)
            self.feedback.append({
                "feedback_id": fbk_id,
                "author_employee_id": author_id,
                "subject_employee_id": subject_id,
                "feedback_type": ftype,
                "content": f"Constructive feedback from {author_id} for {subject_id}",
                "rating": float(int(rating_vals[i])),
                "cycle_id": "CYCLE-2026-H1",
                "is_anonymous": False,
                "status": "submitted",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 9: Development Plans
    # ------------------------------------------------------------------
    def generate_development_plans(self):
        # Create dev plans for employees who have calibrated reviews
        calibrated_emps = {r["employee_id"] for r in self.reviews if r["status"] == "calibrated"}
        dev_seq_per_emp: dict[str, int] = {}

        comp_ids = [c["competency_id"] for c in self.competencies]
        comp_indices = self.rng.integers(0, len(comp_ids), size=len(calibrated_emps))
        start_offsets = self.rng.integers(0, 30, size=len(calibrated_emps))
        end_offsets = self.rng.integers(90, 365, size=len(calibrated_emps))

        for i, emp_id in enumerate(sorted(calibrated_emps)):
            seq = dev_seq_per_emp.get(emp_id, 0) + 1
            dev_seq_per_emp[emp_id] = seq
            emp_num = int(emp_id.split("-")[1])

            start_d = offset_date(BASE_DATE, int(start_offsets[i]))
            end_d = offset_date(start_d, int(end_offsets[i]))

            self.development_plans.append({
                "plan_id": fmt_dev_plan_id(emp_num, seq),
                "employee_id": emp_id,
                "competency_id": comp_ids[int(comp_indices[i])],
                "title": f"Development Plan {seq} for {emp_id}",
                "description": "Structured development to enhance identified competencies",
                "start_date": date_to_str(start_d),
                "target_completion_date": date_to_str(end_d),
                "status": "active",
                "progress_percentage": float(self.rng.integers(0, 100)),
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 10: Evidence
    # ------------------------------------------------------------------
    def generate_evidence(self):
        n_ev = min(len(self.check_ins), 200 if self.mode == "small" else 3000)
        ci_indices = self.rng.integers(0, len(self.check_ins), size=n_ev)

        for i in range(n_ev):
            ci = self.check_ins[int(ci_indices[i])]
            evd_id = fmt_evidence_id(len(self.evidence) + 1)
            self.evidence.append({
                "evidence_id": evd_id,
                "check_in_id": ci["check_in_id"],
                "employee_id": ci["employee_id"],
                "goal_id": ci["goal_id"],
                "title": f"Evidence for {ci['check_in_id']}",
                "description": "Supporting evidence for progress update",
                "evidence_type": self.rng.choice(["document", "link", "screenshot", "metric"]),
                "url": f"https://evidence.example.com/{evd_id.lower()}",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # Step 11: Audit Events
    # ------------------------------------------------------------------
    def generate_audit_events(self):
        # One audit event per review (creation)
        for rev in self.reviews[:50]:
            aud_id = fmt_audit_id(len(self.audit_events) + 1)
            self.audit_events.append({
                "audit_event_id": aud_id,
                "actor_employee_id": rev["reviewer_id"],
                "entity_type": "review",
                "entity_id": rev["review_id"],
                "action": "created",
                "cycle_id": rev["cycle_id"],
                "is_authorized_correction": False,
                "details": f"Review {rev['review_id']} created",
                "anomaly_flag": False,
                "event_timestamp": date_to_str(BASE_DATE),
                "created_at": date_to_str(BASE_DATE),
            })

        # One audit event per goal (first 50)
        for goal in self.goals[:50]:
            aud_id = fmt_audit_id(len(self.audit_events) + 1)
            self.audit_events.append({
                "audit_event_id": aud_id,
                "actor_employee_id": goal["employee_id"],
                "entity_type": "goal",
                "entity_id": goal["goal_id"],
                "action": "created",
                "cycle_id": goal["cycle_id"],
                "is_authorized_correction": False,
                "details": f"Goal {goal['goal_id']} created",
                "anomaly_flag": False,
                "event_timestamp": date_to_str(BASE_DATE),
                "created_at": date_to_str(BASE_DATE),
            })

    # ------------------------------------------------------------------
    # ANOMALY INJECTION
    # ------------------------------------------------------------------
    def inject_anomalies(self):
        """Inject exactly 5 anomalies, one per category."""

        # ---------------------------------------------------------------
        # ANOMALY 1: goal_owner_mismatch
        # ---------------------------------------------------------------
        # Find goal GOAL-EMP-000010-001 (or closest match)
        # If n_employees < 10, we use employee 2
        target_emp_num = min(10, self.n_employees)
        mismatch_emp_num = min(20, self.n_employees)
        # Adjust so they're different
        if mismatch_emp_num == target_emp_num:
            mismatch_emp_num = (target_emp_num % self.n_employees) + 1

        # Find the target goal
        target_goal_id = None
        for g in self.goals:
            if g["employee_id"] == fmt_employee_id(target_emp_num):
                target_goal_id = g["goal_id"]
                break
        if target_goal_id is None:
            # Create a placeholder goal for the target employee
            target_goal_id = fmt_goal_id(target_emp_num, 1)
            self.goals.append({
                "goal_id": target_goal_id,
                "employee_id": fmt_employee_id(target_emp_num),
                "cycle_id": "CYCLE-2026-H1",
                "title": "Anomaly injection goal",
                "description": "Auto-created for anomaly injection",
                "status": "active",
                "weight": 1.0,
                "start_date": date_to_str(BASE_DATE),
                "due_date": date_to_str(offset_date(BASE_DATE, 90)),
                "completion_date": "",
                "anomaly_flag": False,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

        # Inject anomalous check-in: employee_id != goal owner
        anomaly_checkin_date = offset_date(BASE_DATE, 15)
        anomaly_ci_id = fmt_checkin_id(mismatch_emp_num, anomaly_checkin_date, 999)
        anomaly_ci = {
            "check_in_id": anomaly_ci_id,
            "goal_id": target_goal_id,
            "employee_id": fmt_employee_id(mismatch_emp_num),  # WRONG employee
            "check_in_date": date_to_str(anomaly_checkin_date),
            "progress_update": 50.0,
            "notes": "Anomaly: goal owner mismatch injection",
            "blockers": "",
            "anomaly_flag": True,
            "created_at": date_to_str(BASE_DATE),
            "updated_at": date_to_str(BASE_DATE),
        }
        self.check_ins.append(anomaly_ci)

        self.ground_truth.append({
            "anomaly_id": "ANO-001",
            "anomaly_type": "goal_owner_mismatch",
            "entity_type": "check_in",
            "entity_id": anomaly_ci_id,
            "rule_id": "RULE-001",
            "description": "Check-in employee_id does not match goal owner employee_id",
            "expected_value": fmt_employee_id(target_emp_num),
            "actual_value": fmt_employee_id(mismatch_emp_num),
            "injection_mechanism": f"check_in.employee_id set to {fmt_employee_id(mismatch_emp_num)} while goal {target_goal_id} is owned by {fmt_employee_id(target_emp_num)}",
        })

        # ---------------------------------------------------------------
        # ANOMALY 2: progress_exceeds_scale
        # ---------------------------------------------------------------
        target_kr_goal_emp = min(5, self.n_employees)
        kr_anomaly_target_goal_id = None
        for g in self.goals:
            if g["employee_id"] == fmt_employee_id(target_kr_goal_emp):
                kr_anomaly_target_goal_id = g["goal_id"]
                break
        if kr_anomaly_target_goal_id is None:
            kr_anomaly_target_goal_id = fmt_goal_id(target_kr_goal_emp, 1)

        kr_anomaly_id = fmt_kr_id(kr_anomaly_target_goal_id, 1)
        # Check if that KR already exists; if so update it, else inject it
        existing_kr = None
        for kr in self.key_results:
            if kr["kr_id"] == kr_anomaly_id:
                existing_kr = kr
                break

        target_val = 100.0
        actual_val = round(target_val * 2.5, 2)  # 250% of target
        progress_val = round(actual_val / target_val, 4) if target_val > 0 else 0.0
        allowed_scale = 1.0

        if existing_kr:
            existing_kr["actual"] = actual_val
            existing_kr["target"] = target_val
            existing_kr["computed_progress"] = progress_val
            existing_kr["allowed_progress_scale"] = allowed_scale
            existing_kr["anomaly_flag"] = True
        else:
            self.key_results.append({
                "kr_id": kr_anomaly_id,
                "goal_id": kr_anomaly_target_goal_id,
                "employee_id": fmt_employee_id(target_kr_goal_emp),
                "title": f"Key Result 1 for {kr_anomaly_target_goal_id} (anomaly)",
                "description": "Anomaly: progress exceeds allowed scale",
                "target": target_val,
                "actual": actual_val,
                "unit": "percent",
                "allowed_progress_scale": allowed_scale,
                "computed_progress": progress_val,
                "status": "on_track",
                "anomaly_flag": True,
                "created_at": date_to_str(BASE_DATE),
                "updated_at": date_to_str(BASE_DATE),
            })

        self.ground_truth.append({
            "anomaly_id": "ANO-002",
            "anomaly_type": "progress_exceeds_scale",
            "entity_type": "key_result",
            "entity_id": kr_anomaly_id,
            "rule_id": "RULE-002",
            "description": "KR actual value is 250% of target, exceeding allowed_progress_scale of 1.0",
            "expected_value": f"actual/target <= {allowed_scale}",
            "actual_value": str(progress_val),
            "injection_mechanism": f"actual={actual_val} set to target*2.5 with allowed_scale={allowed_scale}",
        })

        # ---------------------------------------------------------------
        # ANOMALY 3: reviewer_no_relationship
        # ---------------------------------------------------------------
        author_num = min(50, self.n_employees)
        subject_num = min(100, self.n_employees)
        if author_num == subject_num:
            subject_num = (author_num % self.n_employees) + 1

        # Ensure author is NOT the manager of subject
        subject_emp = self.employees[subject_num - 1]
        author_emp_id = fmt_employee_id(author_num)
        # If author happens to be manager of subject, adjust
        if subject_emp["manager_id"] == author_emp_id:
            # Move subject to someone whose manager is different
            subject_num = (subject_num % self.n_employees) + 1
            if subject_num == author_num:
                subject_num = (subject_num % self.n_employees) + 1

        fbk_anomaly_id = fmt_feedback_id(len(self.feedback) + 1)
        self.feedback.append({
            "feedback_id": fbk_anomaly_id,
            "author_employee_id": fmt_employee_id(author_num),
            "subject_employee_id": fmt_employee_id(subject_num),
            "feedback_type": "downward",
            "content": "Anomaly: reviewer has no relationship to subject",
            "rating": 3.0,
            "cycle_id": "CYCLE-2026-H1",
            "is_anonymous": False,
            "status": "submitted",
            "anomaly_flag": True,
            "created_at": date_to_str(BASE_DATE),
            "updated_at": date_to_str(BASE_DATE),
        })

        self.ground_truth.append({
            "anomaly_id": "ANO-003",
            "anomaly_type": "reviewer_no_relationship",
            "entity_type": "feedback",
            "entity_id": fbk_anomaly_id,
            "rule_id": "RULE-003",
            "description": f"EMP-{author_num:06d} gave feedback on EMP-{subject_num:06d} without being their manager or review participant",
            "expected_value": f"author is manager of subject or in review_participants",
            "actual_value": f"author={fmt_employee_id(author_num)}, subject={fmt_employee_id(subject_num)}, no relationship",
            "injection_mechanism": f"feedback injected with author={fmt_employee_id(author_num)} who is not manager of subject={fmt_employee_id(subject_num)}",
        })

        # ---------------------------------------------------------------
        # ANOMALY 4: closed_cycle_edit
        # ---------------------------------------------------------------
        # Find a goal in CYCLE-2025-H1 (closed)
        closed_goal = None
        for g in self.goals:
            if g["cycle_id"] == "CYCLE-2025-H1":
                closed_goal = g
                break
        if closed_goal is None:
            # Create one
            closed_goal_id = fmt_goal_id(1, 999)
            self.goals.append({
                "goal_id": closed_goal_id,
                "employee_id": fmt_employee_id(1),
                "cycle_id": "CYCLE-2025-H1",
                "title": "Anomaly closed cycle goal",
                "description": "Auto-created for closed cycle anomaly",
                "status": "completed",
                "weight": 1.0,
                "start_date": "2025-01-01",
                "due_date": "2025-06-30",
                "completion_date": "2025-06-30",
                "anomaly_flag": False,
                "created_at": "2025-01-01",
                "updated_at": "2025-01-01",
            })
            closed_goal = self.goals[-1]

        aud_anomaly_id = fmt_audit_id(len(self.audit_events) + 1)
        self.audit_events.append({
            "audit_event_id": aud_anomaly_id,
            "actor_employee_id": closed_goal["employee_id"],
            "entity_type": "goal",
            "entity_id": closed_goal["goal_id"],
            "action": "modified",
            "cycle_id": "CYCLE-2025-H1",
            "is_authorized_correction": False,
            "details": "Goal modified after cycle closure without authorized correction flag",
            "anomaly_flag": True,
            "event_timestamp": "2026-02-15",  # After cycle end 2025-06-30
            "created_at": date_to_str(BASE_DATE),
        })

        self.ground_truth.append({
            "anomaly_id": "ANO-004",
            "anomaly_type": "closed_cycle_edit",
            "entity_type": "audit_event",
            "entity_id": aud_anomaly_id,
            "rule_id": "RULE-004",
            "description": "Goal in closed cycle CYCLE-2025-H1 was modified without authorized_correction flag",
            "expected_value": "is_authorized_correction=True OR cycle is not closed",
            "actual_value": "action=modified, is_authorized_correction=False, cycle_status=closed",
            "injection_mechanism": f"Audit event with action=modified on {closed_goal['goal_id']} in CYCLE-2025-H1 (closed) with is_authorized_correction=False",
        })

        # ---------------------------------------------------------------
        # ANOMALY 5: untraceable_feedback
        # ---------------------------------------------------------------
        fbk_untraceable_id = fmt_feedback_id(len(self.feedback) + 1)
        self.feedback.append({
            "feedback_id": fbk_untraceable_id,
            "author_employee_id": "EMP-999999",  # Non-existent
            "subject_employee_id": fmt_employee_id(min(3, self.n_employees)),
            "feedback_type": "peer",
            "content": "Anomaly: untraceable feedback from non-existent employee",
            "rating": 4.0,
            "cycle_id": "CYCLE-2026-H1",
            "is_anonymous": False,
            "status": "submitted",
            "anomaly_flag": True,
            "created_at": date_to_str(BASE_DATE),
            "updated_at": date_to_str(BASE_DATE),
        })

        self.ground_truth.append({
            "anomaly_id": "ANO-005",
            "anomaly_type": "untraceable_feedback",
            "entity_type": "feedback",
            "entity_id": fbk_untraceable_id,
            "rule_id": "RULE-005",
            "description": "Feedback record references non-existent author employee ID EMP-999999",
            "expected_value": "author_employee_id must reference a valid employee",
            "actual_value": "EMP-999999",
            "injection_mechanism": "author_employee_id set to EMP-999999 which does not exist in employees table",
        })

    # ------------------------------------------------------------------
    # Write all output files
    # ------------------------------------------------------------------
    def write_outputs(self):
        out = self.output_dir
        gt = self.ground_truth_dir

        # Competencies
        comp_fields = ["competency_id", "name", "description", "is_active", "created_at", "updated_at"]
        write_csv(f"{out}/competencies.csv", self.competencies, comp_fields)
        write_json(f"{out}/competencies.json", self.competencies)

        # Employees
        emp_fields = ["employee_id", "first_name", "last_name", "email", "department",
                      "job_title", "manager_id", "hire_date", "termination_date", "status",
                      "salary", "is_manager", "created_at", "updated_at"]
        write_csv(f"{out}/employees.csv", self.employees, emp_fields)
        write_json(f"{out}/employees.json", self.employees)

        # Review Cycles
        rc_fields = ["cycle_id", "name", "start_date", "end_date", "status",
                     "is_active", "created_at", "updated_at"]
        write_csv(f"{out}/review_cycles.csv", self.review_cycles, rc_fields)
        write_json(f"{out}/review_cycles.json", self.review_cycles)

        # Goals
        goal_fields = ["goal_id", "employee_id", "cycle_id", "title", "description",
                       "status", "weight", "start_date", "due_date", "completion_date",
                       "anomaly_flag", "created_at", "updated_at"]
        write_csv(f"{out}/goals.csv", self.goals, goal_fields)
        write_json(f"{out}/goals.json", self.goals)

        # Key Results
        kr_fields = ["kr_id", "goal_id", "employee_id", "title", "description",
                     "target", "actual", "unit", "allowed_progress_scale",
                     "computed_progress", "status", "anomaly_flag", "created_at", "updated_at"]
        write_csv(f"{out}/key_results.csv", self.key_results, kr_fields)
        write_json(f"{out}/key_results.json", self.key_results)

        # Check-ins
        ci_fields = ["check_in_id", "goal_id", "employee_id", "check_in_date",
                     "progress_update", "notes", "blockers", "anomaly_flag",
                     "created_at", "updated_at"]
        write_csv(f"{out}/check_ins.csv", self.check_ins, ci_fields)
        write_json(f"{out}/check_ins.json", self.check_ins)

        # Reviews
        rev_fields = ["review_id", "employee_id", "reviewer_id", "cycle_id", "status",
                      "self_rating", "manager_rating", "overall_rating", "strengths",
                      "areas_for_improvement", "submitted_at", "calibrated_at",
                      "anomaly_flag", "created_at", "updated_at"]
        write_csv(f"{out}/reviews.csv", self.reviews, rev_fields)
        write_json(f"{out}/reviews.json", self.reviews)

        # Feedback
        fbk_fields = ["feedback_id", "author_employee_id", "subject_employee_id",
                      "feedback_type", "content", "rating", "cycle_id", "is_anonymous",
                      "status", "anomaly_flag", "created_at", "updated_at"]
        write_csv(f"{out}/feedback.csv", self.feedback, fbk_fields)
        write_json(f"{out}/feedback.json", self.feedback)

        # Development Plans
        dp_fields = ["plan_id", "employee_id", "competency_id", "title", "description",
                     "start_date", "target_completion_date", "status", "progress_percentage",
                     "anomaly_flag", "created_at", "updated_at"]
        write_csv(f"{out}/development_plans.csv", self.development_plans, dp_fields)
        write_json(f"{out}/development_plans.json", self.development_plans)

        # Evidence
        ev_fields = ["evidence_id", "check_in_id", "employee_id", "goal_id", "title",
                     "description", "evidence_type", "url", "anomaly_flag",
                     "created_at", "updated_at"]
        write_csv(f"{out}/evidence.csv", self.evidence, ev_fields)
        write_json(f"{out}/evidence.json", self.evidence)

        # Audit Events
        aud_fields = ["audit_event_id", "actor_employee_id", "entity_type", "entity_id",
                      "action", "cycle_id", "is_authorized_correction", "details",
                      "anomaly_flag", "event_timestamp", "created_at"]
        write_csv(f"{out}/audit_events.csv", self.audit_events, aud_fields)
        write_json(f"{out}/audit_events.json", self.audit_events)

        # Ground Truth
        gt_fields = ["anomaly_id", "anomaly_type", "entity_type", "entity_id",
                     "rule_id", "description", "expected_value", "actual_value",
                     "injection_mechanism"]
        write_csv(f"{gt}/ground_truth.csv", self.ground_truth, gt_fields)
        write_json(f"{gt}/ground_truth.json", self.ground_truth)

    def write_manifest(self):
        manifest_dir = os.path.join(os.path.dirname(self.output_dir), "manifests")
        os.makedirs(manifest_dir, exist_ok=True)

        out = self.output_dir
        csv_files = [
            "competencies.csv", "employees.csv", "review_cycles.csv", "goals.csv",
            "key_results.csv", "check_ins.csv", "reviews.csv", "feedback.csv",
            "development_plans.csv", "evidence.csv", "audit_events.csv",
        ]

        row_counts = {
            "competencies": len(self.competencies),
            "employees": len(self.employees),
            "review_cycles": len(self.review_cycles),
            "goals": len(self.goals),
            "key_results": len(self.key_results),
            "check_ins": len(self.check_ins),
            "reviews": len(self.reviews),
            "feedback": len(self.feedback),
            "development_plans": len(self.development_plans),
            "evidence": len(self.evidence),
            "audit_events": len(self.audit_events),
            "ground_truth": len(self.ground_truth),
        }

        checksums = {}
        for fname in csv_files:
            fpath = os.path.join(out, fname)
            if os.path.exists(fpath):
                checksums[fname] = sha256_file(fpath)

        manifest = {
            "seed": self.seed,
            "mode": self.mode,
            "generator_version": GENERATOR_VERSION,
            "generation_timestamp": FIXED_GENERATION_TIMESTAMP,
            "row_counts": row_counts,
            "checksums": checksums,
            "config": {
                "n_employees": self.n_employees,
                "n_managers": self.n_managers,
                "n_goals": self.n_goals,
                "n_checkins": self.n_checkins,
                "n_anomalies": 5,
                "base_date": str(BASE_DATE),
                "epoch_date": str(EPOCH_DATE),
            },
        }

        manifest_path = os.path.join(manifest_dir, "manifest.json")
        write_json(manifest_path, manifest)
        return manifest

    # ------------------------------------------------------------------
    # Main generate pipeline
    # ------------------------------------------------------------------
    def generate(self):
        print(f"[PeoplePulse] Generating data: mode={self.mode}, seed={self.seed}")

        print("  [1/11] Generating competencies...")
        self.generate_competencies()

        print("  [2/11] Generating employees...")
        self.generate_employees()

        print("  [3/11] Generating review cycles...")
        self.generate_review_cycles()

        print("  [4/11] Generating goals...")
        self.generate_goals()

        print("  [5/11] Generating key results...")
        self.generate_key_results()

        print("  [6/11] Generating check-ins...")
        self.generate_checkins()

        print("  [7/11] Generating reviews...")
        self.generate_reviews()

        print("  [8/11] Generating feedback...")
        self.generate_feedback()

        print("  [9/11] Generating development plans...")
        self.generate_development_plans()

        print("  [10/11] Generating evidence...")
        self.generate_evidence()

        print("  [11/11] Generating audit events...")
        self.generate_audit_events()

        print("  [INJECT] Injecting 5 anomalies...")
        self.inject_anomalies()

        print("  [WRITE] Writing output files...")
        self.write_outputs()

        print("  [MANIFEST] Writing manifest...")
        manifest = self.write_manifest()

        print("\n[PeoplePulse] Generation complete!")
        print(f"  Output dir   : {self.output_dir}")
        print(f"  Ground truth : {self.ground_truth_dir}")
        print(f"  Row counts   :")
        for table, count in manifest["row_counts"].items():
            print(f"    {table:<20} {count:>7}")
        print(f"  Anomalies    : {len(self.ground_truth)} (expected 5)")

        return manifest


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def parse_args():
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="PeoplePulse Synthetic Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=20261022, help="Random seed (default: 20261022)")
    parser.add_argument(
        "--mode",
        choices=["small", "full"],
        default="small",
        help="Generation mode: small (100 employees) or full (3000 employees)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(project_root / "data" / "generated"),
        help="Output directory for generated CSV/JSON files",
    )
    parser.add_argument(
        "--ground-truth-dir",
        default=str(project_root / "data" / "ground_truth"),
        help="Output directory for ground truth files",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generator = DataGenerator(
        seed=args.seed,
        mode=args.mode,
        output_dir=args.output_dir,
        ground_truth_dir=args.ground_truth_dir,
    )
    generator.generate()

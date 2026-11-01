# PeoplePulse Data Dictionary

This document describes every table, column, relationship, and business rule in the PeoplePulse database schema.

---

## Table: employees

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| employee_id | VARCHAR(20) | No | Business ID: `EMP-000001` (unique) |
| name | VARCHAR(200) | No | Full name (synthetic only) |
| email | VARCHAR(255) | No | Email address (`@example.com` domain) |
| department | VARCHAR(100) | Yes | Organizational department |
| job_title | VARCHAR(200) | Yes | Job title/role |
| employment_status | ENUM | No | `active`, `on_leave`, `terminated`, `contractor` |
| manager_id | UUID FK | Yes | References `employees.id` (self-referential) |
| hire_date | DATE | Yes | Date of hire |
| termination_date | DATE | Yes | Date of termination (null if active) |
| created_at | TIMESTAMP | No | Record creation time |
| updated_at | TIMESTAMP | No | Last update time |

**Rules:**
- `employee_id` must match pattern `^EMP-\d{6}$`
- `termination_date` must be >= `hire_date` if both present
- `employment_status` = 'terminated' requires `termination_date`
- Self-referential `manager_id` cannot form cycles

---

## Table: review_cycles

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| cycle_id | VARCHAR(30) | No | Business ID: `CYCLE-2026-H1` (unique) |
| name | VARCHAR(200) | No | Human-readable name |
| start_date | DATE | No | Cycle start date |
| end_date | DATE | No | Cycle end date |
| status | ENUM | No | `draft`, `active`, `closed`, `archived` |
| version | INTEGER | No | Optimistic locking version |
| created_at | TIMESTAMP | No | Creation time |
| updated_at | TIMESTAMP | No | Last update time |
| closed_at | TIMESTAMP | Yes | When cycle was closed |

**Lifecycle Transitions:**
- `draft` → `active` (open for submissions)
- `active` → `closed` (no more submissions)
- `closed` → `archived` (historical record only)

**Rules:**
- `end_date` must be > `start_date`
- Closed/archived cycles reject ordinary mutations
- Authorized corrections create versioned records with audit events

---

## Table: goals

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| goal_id | VARCHAR(40) | No | Business ID: `GOAL-EMP-000001-001` |
| employee_id | UUID FK | No | References `employees.id` |
| cycle_id | UUID FK | No | References `review_cycles.id` |
| title | VARCHAR(300) | No | Goal title |
| description | TEXT | Yes | Detailed description |
| status | ENUM | No | `draft`, `active`, `completed`, `cancelled` |
| weight | NUMERIC(5,2) | No | Goal weight (≥ 0) |
| start_date | DATE | Yes | When work begins |
| due_date | DATE | Yes | Target completion date |
| version | INTEGER | No | Version counter |
| rationale | TEXT | Yes | Reason for goal or changes |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

**Rules:**
- `goal_id` format: `GOAL-{employee_id}-{NNN}` where NNN is zero-padded sequence
- `weight` must be ≥ 0
- `due_date` must be ≥ `start_date` if both present
- Cannot create goals in closed/archived cycles

---

## Table: key_results

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| key_result_id | VARCHAR(50) | No | Business ID: `KR-GOAL-EMP-000001-001-01` |
| goal_id | UUID FK | No | References `goals.id` |
| title | VARCHAR(300) | No | KR title |
| metric_type | ENUM | No | `percentage`, `count`, `boolean`, `currency`, `score` |
| unit | VARCHAR(50) | Yes | Unit of measurement (e.g., "%" , "USD", "tickets") |
| baseline | NUMERIC(15,4) | No | Starting value (default 0) |
| target | NUMERIC(15,4) | No | Target value |
| actual | NUMERIC(15,4) | Yes | Current actual value (null = not yet reported) |
| weight | NUMERIC(5,4) | No | Weight within goal (≥ 0) |
| allowed_progress_scale | NUMERIC(5,2) | No | Max allowed progress ratio (1.0 = 100%) |
| version | INTEGER | No | Version counter |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

**Progress Calculation:**
```
raw_progress = (actual - baseline) / (target - baseline)
capped_progress = min(raw_progress, allowed_progress_scale)
```

**Rules:**
- `target` must not equal `baseline` (would cause divide by zero)
- For `percentage` and `count` types: target must be > baseline
- `actual` = null means KR not yet reported (excluded from weighted average)
- `weight` must be ≥ 0
- `allowed_progress_scale` = 1.0 means capped at 100%
- Overachievement (raw > scale) stored separately, not silently discarded

---

## Table: check_ins

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| check_in_id | VARCHAR(40) | No | Business ID: `CHK-EMP-000001-20261001-001` |
| employee_id | UUID FK | No | References `employees.id` (must match goal owner) |
| goal_id | UUID FK | No | References `goals.id` |
| cycle_id | UUID FK | No | References `review_cycles.id` |
| check_in_date | DATE | No | Date of check-in |
| notes | TEXT | Yes | Progress notes |
| progress_snapshot | JSON | Yes | `{kr_id: actual_value, ...}` snapshot |
| status | ENUM | No | `draft`, `submitted` |
| created_at | TIMESTAMP | No | Creation time |

**Rules:**
- `employee_id` must match `goals.employee_id` for referenced goal
- `cycle_id` must match `goals.cycle_id`
- Cannot submit check-ins for closed/archived cycles

---

## Table: competencies

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| competency_id | VARCHAR(10) | No | Business ID: `COMP-001` |
| name | VARCHAR(200) | No | Competency name (unique) |
| description | TEXT | Yes | Detailed description |
| rating_scale | INTEGER | No | Max rating (default 5) |
| is_active | BOOLEAN | No | Whether competency is active |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

**Standard Competencies:**
1. Leadership
2. Communication
3. Technical Expertise
4. Collaboration
5. Innovation
6. Execution & Delivery
7. Customer Focus
8. Problem Solving
9. Adaptability
10. Integrity & Ethics

---

## Table: reviews

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| review_id | VARCHAR(20) | No | Business ID: `REV-2026-000001` |
| employee_id | UUID FK | No | References `employees.id` (subject) |
| cycle_id | UUID FK | No | References `review_cycles.id` |
| reviewer_id | UUID FK | No | References `employees.id` (reviewer) |
| status | ENUM | No | `pending`, `in_progress`, `submitted`, `approved`, `archived` |
| goal_score | NUMERIC(5,2) | Yes | Calculated from goal progress |
| feedback_score | NUMERIC(5,2) | Yes | Calculated from feedback ratings |
| overall_score | NUMERIC(5,2) | Yes | Weighted combination |
| summary | TEXT | Yes | Review summary text |
| submitted_at | TIMESTAMP | Yes | Submission timestamp |
| version | INTEGER | No | Version counter |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

---

## Table: feedback

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| feedback_id | VARCHAR(15) | No | Business ID: `FBK-000001` |
| subject_employee_id | UUID FK | No | References `employees.id` (about whom) |
| author_employee_id | UUID FK | No | References `employees.id` (who wrote) |
| review_id | UUID FK | Yes | References `reviews.id` |
| feedback_type | ENUM | No | `self`, `manager`, `peer` |
| competency_id | UUID FK | Yes | References `competencies.id` |
| rating | INTEGER | Yes | 1-5 rating |
| comments | TEXT | No | Feedback text |
| submitted_at | TIMESTAMP | No | When submitted |
| status | ENUM | No | `draft`, `submitted`, `acknowledged` |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

**Rules:**
- `self` feedback: `author_employee_id` must equal `subject_employee_id`
- `manager` feedback: `author_employee_id` must be direct manager of subject
- `peer` feedback: `author_employee_id` must be in `review_participants` for this review with `peer` role
- `rating` must be 1-5 if provided
- `author_employee_id` is required (untraceable feedback = anomaly)

---

## Table: development_plans

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| plan_id | VARCHAR(25) | No | Business ID: `DEV-EMP-000001-001` |
| employee_id | UUID FK | No | References `employees.id` |
| review_id | UUID FK | Yes | References `reviews.id` (source review) |
| objectives | TEXT | No | Plan objectives |
| status | ENUM | No | `draft`, `active`, `completed`, `cancelled` |
| approver_id | UUID FK | Yes | References `employees.id` |
| approved_at | TIMESTAMP | Yes | When approved |
| completion_date | DATE | Yes | Target completion |
| version | INTEGER | No | Version counter |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

---

## Table: audit_events

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| event_id | VARCHAR(15) | No | Business ID: `AUD-000000001` |
| actor_employee_id | UUID FK | Yes | References `employees.id` (null = system) |
| actor_role | VARCHAR(50) | Yes | Role at time of action |
| action | VARCHAR(100) | No | Action taken: `goal.created`, `review.submitted` |
| entity_type | VARCHAR(100) | No | Entity type: `goal`, `review`, `employee` |
| entity_id | VARCHAR(200) | No | Business ID of affected entity |
| before_state | JSONB | Yes | Full state before change |
| after_state | JSONB | Yes | Full state after change |
| reason | TEXT | Yes | Explanation for change |
| correlation_id | VARCHAR(100) | Yes | Links related events |
| created_at | TIMESTAMP | No | When event occurred |

---

## Table: issues

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Internal primary key |
| issue_id | VARCHAR(15) | No | Business ID: `ISS-000000001` |
| issue_type | ENUM | No | One of 5 anomaly categories |
| entity_type | VARCHAR(100) | No | Entity with the issue |
| entity_id | VARCHAR(200) | No | Business ID |
| severity | ENUM | No | `low`, `medium`, `high`, `critical` |
| rule_id | VARCHAR(20) | No | Rule that detected this: `RULE-001` etc. |
| explanation | TEXT | No | Human-readable explanation |
| expected_value | TEXT | Yes | What was expected |
| actual_value | TEXT | Yes | What was found |
| detected_at | TIMESTAMP | No | When detected |
| resolution_status | ENUM | No | `open`, `investigating`, `resolved`, `dismissed` |
| resolved_at | TIMESTAMP | Yes | When resolved |
| resolved_by | UUID FK | Yes | References `employees.id` |
| evidence_refs | JSONB | Yes | List of related entity IDs |
| created_at, updated_at | TIMESTAMP | No | Timestamps |

---

## ID Convention Summary

| Entity | Format | Example |
|--------|--------|---------|
| Employee | `EMP-{6digits}` | `EMP-000001` |
| Review Cycle | `CYCLE-{YYYY}-{H1/H2}` | `CYCLE-2026-H1` |
| Goal | `GOAL-{employee_id}-{3digits}` | `GOAL-EMP-000001-001` |
| Key Result | `KR-{goal_id}-{2digits}` | `KR-GOAL-EMP-000001-001-01` |
| Check-in | `CHK-{employee_id}-{YYYYMMDD}-{3digits}` | `CHK-EMP-000001-20261001-001` |
| Review | `REV-{YYYY}-{6digits}` | `REV-2026-000001` |
| Feedback | `FBK-{6digits}` | `FBK-000001` |
| Development Plan | `DEV-{employee_id}-{3digits}` | `DEV-EMP-000001-001` |
| Competency | `COMP-{3digits}` | `COMP-001` |
| Evidence | `EVD-{6digits}` | `EVD-000001` |
| Audit Event | `AUD-{9digits}` | `AUD-000000001` |
| Issue | `ISS-{9digits}` | `ISS-000000001` |


# Business Rules

## Review-cycle lifecycle

Allowed transitions:

- `draft` → `active`
- `active` → `closed`
- `closed` → `archived`
- `archived` is terminal

Ordinary mutations (goals, check-ins, reviews) are allowed only while the cycle is `draft` or `active`. Closed/archived cycles return HTTP 409. Authorized corrections must create a new version plus an audit event.

## Progress

Key-result progress uses baseline, actual, target, and metric type:

- Never divide by zero: equal baseline and target yields `zero_range=true` and capped progress 0.
- Missing actuals are excluded from the goal weight denominator.
- Negative or invalid targets are treated as invalid and excluded.
- Overachievement is retained as raw progress and capped at `allowed_progress_scale` for display.
- Goal progress is Σ(capped KR progress × weight) / Σ(valid weights).

Spec example: KR1 actual/target 8/10 weight 0.6 and KR2 15/20 weight 0.4 ⇒ 0.78 (78%). This is calculated, not hardcoded.

## Feedback and reviews

- Self feedback: author must equal subject.
- Manager feedback: author must be the subject’s current `manager_id`.
- Peer feedback: author and subject must be recorded; participation can be captured on `review_participants`.
- Review overall score = 0.5 × goal_score + 0.5 × feedback_score when overall is omitted.

## Development plans

Plans start `active` on create. Approval sets `completed`, stamps `approved_at`, increments version, and writes an audit event.

## Permissions (demo JWT)

Roles: `admin`, `hr_partner`, `manager`, `peer_reviewer`, `employee`, `it_operations`.

Admin generate-data is restricted to `admin`. Validation reports: admin, HR, IT. This demo store is **not** production IAM.

## Audit

State changes persist `actor`, `action`, `entity`, timestamp, before/after, reason, and optional correlation id. Audit rows are append-only from ordinary APIs.

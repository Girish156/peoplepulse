-- =============================================================================
-- PeoplePulse Database Schema (PostgreSQL 16)
-- Complete DDL with constraints, indexes, and foreign keys
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    job_title VARCHAR(200) NOT NULL,
    employment_status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (employment_status IN ('active', 'on_leave', 'terminated')),
    manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    hire_date DATE NOT NULL,
    termination_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_term_date CHECK (termination_date IS NULL OR termination_date >= hire_date)
);

CREATE INDEX IF NOT EXISTS idx_employees_emp_id ON employees(employee_id);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_manager ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(employment_status);

-- 2. Review Cycles Table
CREATE TABLE IF NOT EXISTS review_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'closed', 'archived')),
    version INTEGER NOT NULL DEFAULT 1,
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_cycle_dates CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_review_cycles_cycle_id ON review_cycles(cycle_id);
CREATE INDEX IF NOT EXISTS idx_review_cycles_status ON review_cycles(status);

-- 3. Competencies Table
CREATE TABLE IF NOT EXISTS competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competency_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    rating_scale INTEGER NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_competencies_comp_id ON competencies(competency_id);

-- 4. Goals Table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id VARCHAR(50) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES review_cycles(id) ON DELETE RESTRICT,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),
    weight NUMERIC(5, 2) NOT NULL DEFAULT 1.00 CHECK (weight >= 0),
    start_date DATE,
    due_date DATE,
    version INTEGER NOT NULL DEFAULT 1,
    rationale TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_goal_dates CHECK (due_date IS NULL OR start_date IS NULL OR due_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_goals_goal_id ON goals(goal_id);
CREATE INDEX IF NOT EXISTS idx_goals_employee ON goals(employee_id);
CREATE INDEX IF NOT EXISTS idx_goals_cycle ON goals(cycle_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

-- 5. Goal Versions Table
CREATE TABLE IF NOT EXISTS goal_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    snapshot JSONB NOT NULL,
    changed_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    reason TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_goal_versions_goal ON goal_versions(goal_id);

-- 6. Key Results Table
CREATE TABLE IF NOT EXISTS key_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_result_id VARCHAR(60) UNIQUE NOT NULL,
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    metric_type VARCHAR(20) NOT NULL DEFAULT 'percentage' CHECK (metric_type IN ('percentage', 'count', 'boolean', 'currency', 'score')),
    unit VARCHAR(50),
    baseline NUMERIC(15, 4) NOT NULL DEFAULT 0.0000,
    target NUMERIC(15, 4) NOT NULL,
    actual NUMERIC(15, 4),
    weight NUMERIC(5, 4) NOT NULL DEFAULT 1.0000 CHECK (weight >= 0),
    allowed_progress_scale NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kr_key_result_id ON key_results(key_result_id);
CREATE INDEX IF NOT EXISTS idx_kr_goal ON key_results(goal_id);

-- 7. Check-ins Table
CREATE TABLE IF NOT EXISTS check_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_in_id VARCHAR(50) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES review_cycles(id) ON DELETE RESTRICT,
    check_in_date DATE NOT NULL,
    notes TEXT,
    progress_snapshot JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted' CHECK (status IN ('draft', 'submitted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checkins_ci_id ON check_ins(check_in_id);
CREATE INDEX IF NOT EXISTS idx_checkins_employee ON check_ins(employee_id);
CREATE INDEX IF NOT EXISTS idx_checkins_goal ON check_ins(goal_id);
CREATE INDEX IF NOT EXISTS idx_checkins_cycle ON check_ins(cycle_id);

-- 8. Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id VARCHAR(30) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES review_cycles(id) ON DELETE RESTRICT,
    reviewer_id UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'submitted', 'approved', 'archived')),
    goal_score NUMERIC(5, 2),
    feedback_score NUMERIC(5, 2),
    overall_score NUMERIC(5, 2),
    summary TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_rev_id ON reviews(review_id);
CREATE INDEX IF NOT EXISTS idx_reviews_employee ON reviews(employee_id);
CREATE INDEX IF NOT EXISTS idx_reviews_cycle ON reviews(cycle_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id);

-- 9. Review Participants Table
CREATE TABLE IF NOT EXISTS review_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    participant_employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'peer' CHECK (role IN ('self', 'manager', 'peer')),
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_review_participant UNIQUE (review_id, participant_employee_id)
);

-- 10. Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feedback_id VARCHAR(20) UNIQUE NOT NULL,
    subject_employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    author_employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    feedback_type VARCHAR(20) NOT NULL DEFAULT 'peer' CHECK (feedback_type IN ('self', 'manager', 'peer')),
    competency_id UUID REFERENCES competencies(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
    comments TEXT NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted' CHECK (status IN ('draft', 'submitted', 'acknowledged')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_fbk_id ON feedback(feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_subject ON feedback(subject_employee_id);
CREATE INDEX IF NOT EXISTS idx_feedback_author ON feedback(author_employee_id);

-- 11. Evidence Table
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id VARCHAR(20) UNIQUE NOT NULL,
    check_in_id UUID REFERENCES check_ins(id) ON DELETE SET NULL,
    feedback_id UUID REFERENCES feedback(id) ON DELETE SET NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    evidence_type VARCHAR(30) NOT NULL DEFAULT 'note' CHECK (evidence_type IN ('document', 'url', 'screenshot', 'note', 'metric')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_evd_id ON evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_checkin ON evidence(check_in_id);

-- 12. Development Plans Table
CREATE TABLE IF NOT EXISTS development_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id VARCHAR(30) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    objectives TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),
    approver_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    completion_date DATE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dev_plans_plan_id ON development_plans(plan_id);
CREATE INDEX IF NOT EXISTS idx_dev_plans_employee ON development_plans(employee_id);

-- 13. Development Plan Actions Table
CREATE TABLE IF NOT EXISTS development_plan_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES development_plans(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    due_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dev_plan_actions_plan ON development_plan_actions(plan_id);

-- 14. Audit Events Table
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(20) UNIQUE NOT NULL,
    actor_employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    actor_role VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(200) NOT NULL,
    before_state JSONB,
    after_state JSONB,
    reason TEXT,
    correlation_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_event_id ON audit_events(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_employee_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action);

-- 15. Issues Table
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id VARCHAR(20) UNIQUE NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(200) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    rule_id VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    resolution_status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (resolution_status IN ('open', 'investigating', 'resolved', 'dismissed')),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    evidence_refs JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_issues_issue_id ON issues(issue_id);
CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(issue_type);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(resolution_status);
CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity);


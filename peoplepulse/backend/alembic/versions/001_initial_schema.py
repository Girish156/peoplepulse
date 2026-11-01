"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Employees
    op.create_table(
        'employees',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('employee_id', sa.String(20), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('job_title', sa.String(200), nullable=False),
        sa.Column('employment_status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('manager_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Review Cycles
    op.create_table(
        'review_cycles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('cycle_id', sa.String(30), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Competencies
    op.create_table(
        'competencies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('competency_id', sa.String(10), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rating_scale', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. Goals
    op.create_table(
        'goals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('goal_id', sa.String(50), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cycle_id', sa.String(36), sa.ForeignKey('review_cycles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False, server_default='1.00'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Goal Versions
    op.create_table(
        'goal_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('changed_by', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. Key Results
    op.create_table(
        'key_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key_result_id', sa.String(60), nullable=False, unique=True),
        sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('metric_type', sa.String(20), nullable=False, server_default='percentage'),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('baseline', sa.Numeric(15, 4), nullable=False, server_default='0.0000'),
        sa.Column('target', sa.Numeric(15, 4), nullable=False),
        sa.Column('actual', sa.Numeric(15, 4), nullable=True),
        sa.Column('weight', sa.Numeric(5, 4), nullable=False, server_default='1.0000'),
        sa.Column('allowed_progress_scale', sa.Numeric(5, 2), nullable=False, server_default='1.00'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Check-ins
    op.create_table(
        'check_ins',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('check_in_id', sa.String(50), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal_id', sa.String(36), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cycle_id', sa.String(36), sa.ForeignKey('review_cycles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('check_in_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('progress_snapshot', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='submitted'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('review_id', sa.String(30), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cycle_id', sa.String(36), sa.ForeignKey('review_cycles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reviewer_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('goal_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('feedback_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('overall_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. Review Participants
    op.create_table(
        'review_participants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('review_id', sa.String(36), sa.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False),
        sa.Column('participant_employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='peer'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. Feedback
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('feedback_id', sa.String(20), nullable=False, unique=True),
        sa.Column('subject_employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_id', sa.String(36), sa.ForeignKey('reviews.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_type', sa.String(20), nullable=False, server_default='peer'),
        sa.Column('competency_id', sa.String(36), sa.ForeignKey('competencies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='submitted'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evidence_id', sa.String(20), nullable=False, unique=True),
        sa.Column('check_in_id', sa.String(36), sa.ForeignKey('check_ins.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_id', sa.String(36), sa.ForeignKey('feedback.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('evidence_type', sa.String(30), nullable=False, server_default='note'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Development Plans
    op.create_table(
        'development_plans',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('plan_id', sa.String(30), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('review_id', sa.String(36), sa.ForeignKey('reviews.id', ondelete='SET NULL'), nullable=True),
        sa.Column('objectives', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('approver_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Development Plan Actions
    op.create_table(
        'development_plan_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('plan_id', sa.String(36), sa.ForeignKey('development_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 14. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_id', sa.String(20), nullable=False, unique=True),
        sa.Column('actor_employee_id', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_role', sa.String(50), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(200), nullable=False),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Issues
    op.create_table(
        'issues',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('issue_id', sa.String(20), nullable=False, unique=True),
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(200), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('rule_id', sa.String(50), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('expected_value', sa.Text(), nullable=True),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolution_status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(36), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True),
        sa.Column('evidence_refs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('issues')
    op.drop_table('audit_events')
    op.drop_table('development_plan_actions')
    op.drop_table('development_plans')
    op.drop_table('evidence')
    op.drop_table('feedback')
    op.drop_table('review_participants')
    op.drop_table('reviews')
    op.drop_table('check_ins')
    op.drop_table('key_results')
    op.drop_table('goal_versions')
    op.drop_table('goals')
    op.drop_table('competencies')
    op.drop_table('review_cycles')
    op.drop_table('employees')


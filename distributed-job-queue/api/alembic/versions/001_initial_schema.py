"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-12-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.Enum('SEND_EMAIL', 'PROCESS_VIDEO', 'SCRAPE_WEBSITE', name='jobtype'), nullable=False),
        sa.Column('priority', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='jobpriority'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING', name='jobstatus'), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('worker_id', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_created_at'), 'jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_jobs_job_type'), 'jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_jobs_priority'), 'jobs', ['priority'], unique=False)
    op.create_index(op.f('ix_jobs_scheduled_for'), 'jobs', ['scheduled_for'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    
    # Create retry_attempts table
    op.create_table(
        'retry_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_retry_attempts_job_id'), 'retry_attempts', ['job_id'], unique=False)
    
    # Create dead_letters table
    op.create_table(
        'dead_letters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.Enum('SEND_EMAIL', 'PROCESS_VIDEO', 'SCRAPE_WEBSITE', name='jobtype'), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_attempts', sa.Integer(), nullable=False),
        sa.Column('first_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('final_failure_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=False),
        sa.Column('all_error_messages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_dead_letters_job_id'), 'dead_letters', ['job_id'], unique=False)
    op.create_index(op.f('ix_dead_letters_job_type'), 'dead_letters', ['job_type'], unique=False)
    
    # Create scheduled_jobs table
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('job_type', sa.Enum('SEND_EMAIL', 'PROCESS_VIDEO', 'SCRAPE_WEBSITE', name='jobtype'), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('priority', sa.Enum('HIGH', 'MEDIUM', 'LOW', name='jobpriority'), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_scheduled_jobs_next_run_at'), 'scheduled_jobs', ['next_run_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduled_jobs_next_run_at'), table_name='scheduled_jobs')
    op.drop_table('scheduled_jobs')
    op.drop_index(op.f('ix_dead_letters_job_type'), table_name='dead_letters')
    op.drop_index(op.f('ix_dead_letters_job_id'), table_name='dead_letters')
    op.drop_table('dead_letters')
    op.drop_index(op.f('ix_retry_attempts_job_id'), table_name='retry_attempts')
    op.drop_table('retry_attempts')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_scheduled_for'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_priority'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_job_type'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_created_at'), table_name='jobs')
    op.drop_table('jobs')
    
    # Drop enums
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobtype').drop(op.get_bind(), checkfirst=True)

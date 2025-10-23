"""create job_applications table

Revision ID: 20251023_create_job_applications
Revises: 20251008_add_research_content_tables
Create Date: 2025-10-23 10:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251023_create_job_applications'
down_revision = '20251008_add_research_content_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'job_applications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('linkedin', sa.String(), nullable=True),
        sa.Column('portfolio', sa.String(), nullable=True),
        sa.Column('resume_path', sa.String(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='submitted'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_applications_id', 'job_applications', ['id'], unique=False)
    op.create_index('ix_job_applications_email', 'job_applications', ['email'], unique=False)
    op.create_index('ix_job_applications_role', 'job_applications', ['role'], unique=False)


def downgrade():
    op.drop_index('ix_job_applications_role', table_name='job_applications')
    op.drop_index('ix_job_applications_email', table_name='job_applications')
    op.drop_index('ix_job_applications_id', table_name='job_applications')
    op.drop_table('job_applications')

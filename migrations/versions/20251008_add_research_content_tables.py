"""
Add research content tables migration.

Revision ID: 20251008_add_research_content
Revises: 20251006_add_conversation_metadata
Create Date: 2025-10-08 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


# revision identifiers, used by Alembic.
revision = '20251008_add_research_content'
down_revision = '20251006_add_conversation_metadata'
branch_labels = None
depends_on = None


def upgrade():
    # Create generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('section_title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('content_metadata', JSON, nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_content_id'), 'generated_content', ['id'], unique=False)
    
    # Create content_feedback table
    op.create_table(
        'content_feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('feedback_metadata', JSON, nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_feedback_id'), 'content_feedback', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_content_feedback_id'), table_name='content_feedback')
    op.drop_table('content_feedback')
    op.drop_index(op.f('ix_generated_content_id'), table_name='generated_content')
    op.drop_table('generated_content')

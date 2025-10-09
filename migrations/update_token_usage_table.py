"""
Update token_usage table to match the model

This migration updates the token_usage table to match the TokenUsage model.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '2023_10_09_update_token_usage'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to token_usage table
    op.add_column('token_usage', sa.Column('request_type', sa.String(50), nullable=True))
    op.add_column('token_usage', sa.Column('prompt_tokens', sa.Integer(), nullable=True, default=0))
    op.add_column('token_usage', sa.Column('completion_tokens', sa.Integer(), nullable=True, default=0))
    op.add_column('token_usage', sa.Column('request_id', sa.String(), nullable=True))
    op.add_column('token_usage', sa.Column('total_tokens', sa.Integer(), nullable=True, default=0))
    
    # Set default values for new columns
    op.execute("UPDATE token_usage SET request_type = 'chat' WHERE request_type IS NULL")
    op.execute("UPDATE token_usage SET prompt_tokens = 0 WHERE prompt_tokens IS NULL")
    op.execute("UPDATE token_usage SET completion_tokens = 0 WHERE completion_tokens IS NULL")
    op.execute("UPDATE token_usage SET total_tokens = tokens_used WHERE total_tokens IS NULL")
    
    # Make columns non-nullable
    op.alter_column('token_usage', 'request_type', nullable=False)
    op.alter_column('token_usage', 'prompt_tokens', nullable=False)
    op.alter_column('token_usage', 'completion_tokens', nullable=False)
    op.alter_column('token_usage', 'total_tokens', nullable=False)
    
    # Create token_usage_summary table
    op.create_table(
        'token_usage_summary',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('chat_prompt_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('chat_completion_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('chat_total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('plagiarism_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('prompt_generation_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for token_usage_summary
    op.create_index('ix_token_usage_summary_user_id', 'token_usage_summary', ['user_id'])
    op.create_index('ix_token_usage_summary_year_month_day', 'token_usage_summary', ['year', 'month', 'day'])


def downgrade():
    # Drop token_usage_summary table
    op.drop_index('ix_token_usage_summary_year_month_day', table_name='token_usage_summary')
    op.drop_index('ix_token_usage_summary_user_id', table_name='token_usage_summary')
    op.drop_table('token_usage_summary')
    
    # Drop new columns from token_usage
    op.drop_column('token_usage', 'request_type')
    op.drop_column('token_usage', 'prompt_tokens')
    op.drop_column('token_usage', 'completion_tokens')
    op.drop_column('token_usage', 'request_id')
    op.drop_column('token_usage', 'total_tokens')
    
    # Rename timestamp column back to date if it exists
    try:
        op.alter_column('token_usage', 'timestamp', new_column_name='date')
    except:
        pass

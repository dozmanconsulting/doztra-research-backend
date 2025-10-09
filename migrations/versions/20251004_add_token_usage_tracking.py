"""Add token usage tracking

Revision ID: 20251004_token_usage
Revises: previous_revision_id  # Replace with the actual previous revision ID
Create Date: 2025-10-04 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251004_token_usage'
down_revision = 'previous_revision_id'  # Replace with the actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE request_type AS ENUM ('chat', 'plagiarism', 'prompt')")
    op.execute("ALTER TYPE model_tier ADD VALUE 'gpt-4-turbo' AFTER 'gpt-4'")
    
    # Update subscriptions table
    op.add_column('subscriptions', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('subscriptions', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('payment_method_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('token_limit', sa.Integer(), nullable=True))
    op.add_column('subscriptions', sa.Column('max_model_tier', sa.String(), nullable=False, server_default='gpt-3.5-turbo'))
    
    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('theme', sa.String(), nullable=True, server_default='light'),
        sa.Column('notifications', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('default_model', sa.String(), nullable=True, server_default='gpt-4'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=False)
    
    # Create usage_statistics table
    op.create_table(
        'usage_statistics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('chat_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('plagiarism_checks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompts_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_limit', sa.Integer(), nullable=True),
        sa.Column('last_reset_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_statistics_id'), 'usage_statistics', ['id'], unique=False)
    op.create_index(op.f('ix_usage_statistics_user_id'), 'usage_statistics', ['user_id'], unique=False)
    
    # Create token_usage table
    op.create_table(
        'token_usage',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('request_type', sa.Enum('chat', 'plagiarism', 'prompt', name='request_type'), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_token_usage_id'), 'token_usage', ['id'], unique=False)
    op.create_index(op.f('ix_token_usage_user_id'), 'token_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_token_usage_timestamp'), 'token_usage', ['timestamp'], unique=False)
    op.create_index(op.f('ix_token_usage_request_type'), 'token_usage', ['request_type'], unique=False)
    
    # Create token_usage_summary table
    op.create_table(
        'token_usage_summary',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('chat_prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chat_completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chat_total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('plagiarism_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompt_generation_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'month', 'day')
    )
    op.create_index(op.f('ix_token_usage_summary_id'), 'token_usage_summary', ['id'], unique=False)
    op.create_index(op.f('ix_token_usage_summary_user_id'), 'token_usage_summary', ['user_id'], unique=False)
    op.create_index(op.f('ix_token_usage_summary_date'), 'token_usage_summary', ['year', 'month', 'day'], unique=False)
    
    # Set default token limits based on subscription plan
    op.execute("""
    UPDATE subscriptions 
    SET token_limit = CASE 
        WHEN plan = 'free' THEN 100000
        WHEN plan = 'basic' THEN 500000
        ELSE NULL
    END,
    max_model_tier = CASE 
        WHEN plan = 'free' THEN 'gpt-3.5-turbo'
        WHEN plan = 'basic' THEN 'gpt-4'
        WHEN plan = 'professional' THEN 'gpt-4-turbo'
        ELSE 'gpt-3.5-turbo'
    END
    """)
    
    # Create user preferences for existing users
    op.execute("""
    INSERT INTO user_preferences (id, user_id, theme, notifications, default_model)
    SELECT 
        gen_random_uuid()::text, 
        id, 
        'light', 
        true, 
        CASE 
            WHEN EXISTS (SELECT 1 FROM subscriptions WHERE subscriptions.user_id = users.id AND plan = 'professional') THEN 'gpt-4-turbo'
            WHEN EXISTS (SELECT 1 FROM subscriptions WHERE subscriptions.user_id = users.id AND plan = 'basic') THEN 'gpt-4'
            ELSE 'gpt-3.5-turbo'
        END
    FROM users
    """)
    
    # Create usage statistics for existing users
    op.execute("""
    INSERT INTO usage_statistics (id, user_id, tokens_limit)
    SELECT 
        gen_random_uuid()::text, 
        users.id, 
        CASE 
            WHEN EXISTS (SELECT 1 FROM subscriptions WHERE subscriptions.user_id = users.id AND plan = 'free') THEN 100000
            WHEN EXISTS (SELECT 1 FROM subscriptions WHERE subscriptions.user_id = users.id AND plan = 'basic') THEN 500000
            ELSE NULL
        END
    FROM users
    """)


def downgrade():
    # Drop tables
    op.drop_table('token_usage_summary')
    op.drop_table('token_usage')
    op.drop_table('usage_statistics')
    op.drop_table('user_preferences')
    
    # Drop columns from subscriptions
    op.drop_column('subscriptions', 'is_active')
    op.drop_column('subscriptions', 'stripe_customer_id')
    op.drop_column('subscriptions', 'stripe_subscription_id')
    op.drop_column('subscriptions', 'payment_method_id')
    op.drop_column('subscriptions', 'token_limit')
    op.drop_column('subscriptions', 'max_model_tier')
    
    # Drop enum types
    op.execute("DROP TYPE request_type")

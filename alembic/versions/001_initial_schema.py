"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-10-04 15:35:00.000000

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
    # Create enum types if they don't exist
    connection = op.get_bind()
    
    # Check if subscriptionplan enum exists
    result = connection.execute(
        """SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionplan')"""
    )
    if not result.scalar():
        subscription_plan = postgresql.ENUM('FREE', 'BASIC', 'PROFESSIONAL', name='subscriptionplan')
        subscription_plan.create(connection)
    
    # Check if subscriptionstatus enum exists
    result = connection.execute(
        """SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus')"""
    )
    if not result.scalar():
        subscription_status = postgresql.ENUM('ACTIVE', 'CANCELED', 'EXPIRED', 'PENDING', name='subscriptionstatus')
        subscription_status.create(connection)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),  # Add role column
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('plan', sa.Enum('FREE', 'BASIC', 'PROFESSIONAL', name='subscriptionplan'), nullable=False, server_default='FREE'),
        sa.Column('status', sa.Enum('ACTIVE', 'CANCELED', 'EXPIRED', 'PENDING', name='subscriptionstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('start_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_users_email', 'users', ['email'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('refresh_tokens')
    op.drop_table('subscriptions')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='subscriptionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscriptionplan').drop(op.get_bind(), checkfirst=True)

"""Add OAuth fields to user model

Revision ID: add_oauth_fields
Revises: [REPLACE_WITH_LATEST_REVISION_ID]
Create Date: 2025-10-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_oauth_fields'
down_revision = None  # Replace with the actual previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Make hashed_password nullable
    op.alter_column('users', 'hashed_password',
               existing_type=sa.String(),
               nullable=True)
    
    # Add OAuth fields
    op.add_column('users', sa.Column('oauth_provider', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_user_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_refresh_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('oauth_token_expires_at', sa.DateTime(), nullable=True))
    
    # Add index for oauth_user_id and provider combination
    op.create_index('ix_users_oauth_provider_id', 'users', ['oauth_provider', 'oauth_user_id'], unique=True)


def downgrade():
    # Drop OAuth fields
    op.drop_index('ix_users_oauth_provider_id', table_name='users')
    op.drop_column('users', 'oauth_token_expires_at')
    op.drop_column('users', 'oauth_refresh_token')
    op.drop_column('users', 'oauth_access_token')
    op.drop_column('users', 'oauth_user_id')
    op.drop_column('users', 'oauth_provider')
    
    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password',
               existing_type=sa.String(),
               nullable=False)

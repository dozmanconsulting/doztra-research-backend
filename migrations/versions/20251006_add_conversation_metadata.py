"""
Add conversation_metadata column to conversations table.

Revision ID: 20251006_add_conversation_metadata
Revises: 20251004_add_token_usage_tracking
Create Date: 2025-10-06 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '20251006_add_conversation_metadata'
down_revision = '20251004_add_token_usage_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Add conversation_metadata column to conversations table
    op.add_column('conversations', sa.Column('conversation_metadata', JSON, nullable=True))


def downgrade():
    # Remove conversation_metadata column from conversations table
    op.drop_column('conversations', 'conversation_metadata')

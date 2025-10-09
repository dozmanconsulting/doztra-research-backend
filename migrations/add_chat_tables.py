"""
Add chat tables to the database

This migration adds the conversations and messages tables for the chat functionality.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '2023_10_09_add_chat_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('conversation_metadata', JSONB, nullable=True)
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('message_metadata', JSONB, nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('messages')
    op.drop_table('conversations')

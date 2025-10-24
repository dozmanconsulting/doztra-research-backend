"""Add knowledge base tables

Revision ID: 001_add_knowledge_base_tables
Revises: 
Create Date: 2024-10-24 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_knowledge_base_tables'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Create content_items table
    op.create_table('content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=True),
        sa.Column('processing_progress', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('extraction_settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_items_content_id'), 'content_items', ['content_id'], unique=True)
    op.create_index(op.f('ix_content_items_user_id'), 'content_items', ['user_id'], unique=False)

    # Create content_chunks table
    op.create_table('content_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_id', sa.String(length=255), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_chunks_chunk_id'), 'content_chunks', ['chunk_id'], unique=True)

    # Create conversation_sessions table
    op.create_table('conversation_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('zep_session_id', sa.String(length=255), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_sessions_session_id'), 'conversation_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_conversation_sessions_user_id'), 'conversation_sessions', ['user_id'], unique=False)

    # Create podcasts table
    op.create_table('podcasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('podcast_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('knowledge_query', sa.Text(), nullable=True),
        sa.Column('content_ids', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('script_content', sa.Text(), nullable=True),
        sa.Column('audio_file_path', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('audio_format', sa.String(length=20), nullable=True),
        sa.Column('voice_settings', sa.JSON(), nullable=True),
        sa.Column('podcast_settings', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('script_generated_at', sa.DateTime(), nullable=True),
        sa.Column('audio_generated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_podcasts_podcast_id'), 'podcasts', ['podcast_id'], unique=True)
    op.create_index(op.f('ix_podcasts_user_id'), 'podcasts', ['user_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_podcasts_user_id'), table_name='podcasts')
    op.drop_index(op.f('ix_podcasts_podcast_id'), table_name='podcasts')
    op.drop_table('podcasts')
    
    op.drop_index(op.f('ix_conversation_sessions_user_id'), table_name='conversation_sessions')
    op.drop_index(op.f('ix_conversation_sessions_session_id'), table_name='conversation_sessions')
    op.drop_table('conversation_sessions')
    
    op.drop_index(op.f('ix_content_chunks_chunk_id'), table_name='content_chunks')
    op.drop_table('content_chunks')
    
    op.drop_index(op.f('ix_content_items_user_id'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_content_id'), table_name='content_items')
    op.drop_table('content_items')

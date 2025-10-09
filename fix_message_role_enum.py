#!/usr/bin/env python3
"""
Script to fix the MessageRole enum in the database
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_message_role_enum():
    """Fix the MessageRole enum in the database"""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Execute SQL to update the enum type
    with engine.connect() as conn:
        print("Fixing MessageRole enum in database...")
        
        # Create a new enum type with the correct values
        conn.execute(text("CREATE TYPE messageroletypes_new AS ENUM ('user', 'assistant', 'system')"))
        
        # Create a temporary table to hold messages
        conn.execute(text("CREATE TEMP TABLE messages_backup AS SELECT * FROM messages"))
        
        # Drop the original table
        conn.execute(text("DROP TABLE messages"))
        
        # Create the messages table with the new enum type
        conn.execute(text("""
            CREATE TABLE messages (
                id VARCHAR PRIMARY KEY,
                conversation_id VARCHAR NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role messageroletypes_new NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                model VARCHAR,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                message_metadata JSONB
            )
        """))
        
        # Insert data back with lowercase role values
        conn.execute(text("""
            INSERT INTO messages (
                id, conversation_id, role, content, created_at, 
                model, prompt_tokens, completion_tokens, total_tokens, message_metadata
            )
            SELECT 
                id, conversation_id, 
                LOWER(role::text)::messageroletypes_new, 
                content, created_at, 
                model, prompt_tokens, completion_tokens, total_tokens, message_metadata
            FROM messages_backup
        """))
        
        # Drop the temporary table
        conn.execute(text("DROP TABLE messages_backup"))
        
        # Drop the old enum type
        conn.execute(text("DROP TYPE IF EXISTS messageroletypes"))
        
        # Rename the new enum type to the original name
        conn.execute(text("ALTER TYPE messageroletypes_new RENAME TO messageroletypes"))
        
        conn.commit()
        print("MessageRole enum fixed successfully.")

if __name__ == "__main__":
    fix_message_role_enum()

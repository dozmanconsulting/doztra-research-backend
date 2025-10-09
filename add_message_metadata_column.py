#!/usr/bin/env python3
"""
Script to add message_metadata column to the messages table
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def add_message_metadata_column():
    """Add message_metadata column to messages table"""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Execute SQL to add column
    with engine.connect() as conn:
        print("Adding message_metadata column to messages table...")
        conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_metadata JSONB"))
        conn.commit()
        print("Column added successfully.")

if __name__ == "__main__":
    add_message_metadata_column()

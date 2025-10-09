#!/usr/bin/env python3
"""
Script to check the database schema
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def check_db_schema():
    """Check the database schema"""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Execute SQL to check tables
    with engine.connect() as conn:
        print("Checking database schema...")
        
        # Check if messages table exists
        result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages')"))
        exists = result.scalar()
        print(f"Messages table exists: {exists}")
        
        if exists:
            # Check the structure of the messages table
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'messages'"))
            columns = result.fetchall()
            print("\nMessages table structure:")
            for column in columns:
                print(f"  {column[0]}: {column[1]}")
            
            # Check the role column type
            result = conn.execute(text("SELECT pg_catalog.format_type(a.atttypid, a.atttypmod) FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON a.attrelid = c.oid WHERE c.relname = 'messages' AND a.attname = 'role'"))
            role_type = result.scalar()
            print(f"\nRole column type: {role_type}")
            
            # Check the enum type
            result = conn.execute(text("SELECT n.nspname as schema, t.typname as type FROM pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'messageroletypes'"))
            enum_type = result.fetchone()
            print(f"\nEnum type: {enum_type}")
            
            if enum_type:
                # Check the enum values
                result = conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'messageroletypes'"))
                enum_values = result.fetchall()
                print("\nEnum values:")
                for value in enum_values:
                    print(f"  {value[0]}")

if __name__ == "__main__":
    check_db_schema()

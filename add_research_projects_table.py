"""
Migration script to add the research_projects table to the database.
"""
import os
import sys
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
from datetime import datetime
import uuid

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.config import settings
from app.db.base_class import Base

# Define the ProjectStatus enum
class ProjectStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    completed = "completed"

def run_migration():
    """
    Run the migration to add the research_projects table.
    """
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create metadata object
    metadata = MetaData()
    
    # Define the research_projects table
    research_projects = Table(
        "research_projects",
        metadata,
        Column("id", String, primary_key=True, index=True),
        Column("user_id", String, nullable=False),  # We'll add the foreign key constraint later
        Column("title", String, nullable=False),
        Column("description", Text, nullable=True),
        Column("type", String, nullable=False),
        Column("status", String, nullable=False),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
        Column("project_metadata", JSON, nullable=True),
    )
    
    # Create the table
    metadata.create_all(engine, tables=[research_projects])
    
    print("Migration completed: Added research_projects table")

if __name__ == "__main__":
    run_migration()

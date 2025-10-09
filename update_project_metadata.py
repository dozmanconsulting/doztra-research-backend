#!/usr/bin/env python3
"""
Utility script to update project metadata in the database.
"""
import json
import psycopg2
import os
import sys

# Get database URL from app settings
sys.path.append('/Users/shed/Desktop/Doztra-Auth-Service')
from app.core.config import settings

db_url = settings.DATABASE_URL

# Parse the database URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "")
else:
    db_url = db_url.replace("postgres://", "")

# Split the URL into components
user_pass, host_db = db_url.split("@")
user, password = user_pass.split(":") if ":" in user_pass else (user_pass, "")
host_port, db = host_db.split("/")
host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")


def update_project_metadata():
    """Update project metadata in the database."""
    # Connect to the database
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password
    )
    
    try:
        # Create a cursor
        cursor = conn.cursor()
        
        # Get all projects
        cursor.execute(
            """SELECT id, title, type, project_metadata 
               FROM research_projects"""
        )
        projects = cursor.fetchall()
        
        if not projects:
            print("No projects found in the database.")
            return
        
        print(f"Found {len(projects)} projects")
        
        # Update each project with sample metadata
        for project in projects:
            project_id, title, project_type, metadata = project
            
            # Create sample metadata based on project type
            sample_metadata = {
                "academic_level": "doctoral" if "dissertation" in project_type.lower() else "masters",
                "target_audience": "researchers",
                "research_methodology": "mixed_methods",
                "country": "us",
                "keywords": ["research", project_type, title.split()[0].lower()],
                "discipline": "computer_science" if "technology" in title.lower() else "social_sciences"
            }
            
            # Update the project metadata
            cursor.execute(
                """UPDATE research_projects 
                   SET project_metadata = %s,
                       updated_at = NOW()
                   WHERE id = %s""",
                (json.dumps(sample_metadata), project_id)
            )
            
            print(f"Updated project {project_id} with metadata")
        
        # Commit the changes
        conn.commit()
        print("All projects updated successfully")
        
    finally:
        conn.close()


if __name__ == "__main__":
    update_project_metadata()

#!/usr/bin/env python3
"""
Utility script to check project metadata in the database.
"""
import json
import psycopg2
import os

# Get database URL from app settings
import sys
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


def check_project_metadata():
    """Check project metadata in the database using raw SQL."""
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
        
        # Get all projects (limit 5)
        cursor.execute(
            """SELECT id, title, type, project_metadata 
               FROM research_projects 
               LIMIT 5"""
        )
        projects = cursor.fetchall()
        
        print(f"Found {len(projects)} projects")
        print("-" * 50)
        
        for i, project in enumerate(projects):
            project_id, title, project_type, metadata = project
            print(f"Project {i+1}:")
            print(f"  ID: {project_id}")
            print(f"  Title: {title}")
            print(f"  Type: {project_type}")
            print(f"  Metadata: {json.dumps(metadata, indent=2) if metadata else 'None'}")
            print("-" * 50)
        
        # Count projects with metadata
        cursor.execute(
            """SELECT 
                   COUNT(*) FILTER (WHERE project_metadata IS NOT NULL) as with_metadata,
                   COUNT(*) as total
               FROM research_projects"""
        )
        result = cursor.fetchone()
        projects_with_metadata, total_projects = result
        
        if total_projects > 0:
            percentage = (projects_with_metadata / total_projects) * 100
            print(f"Projects with metadata: {projects_with_metadata}/{total_projects} ({percentage:.2f}%)")
        else:
            print("No projects found in the database.")
        
        # Check for specific metadata fields
        if projects:
            print("\nChecking for specific metadata fields:")
            fields = ['academic_level', 'target_audience', 'research_methodology', 'country', 'keywords', 'discipline']
            
            for field in fields:
                count = 0
                for _, _, _, metadata in projects:
                    if metadata and field in metadata:
                        count += 1
                
                print(f"  - {field}: {count}/{len(projects)} projects")
        
    finally:
        conn.close()


if __name__ == "__main__":
    check_project_metadata()

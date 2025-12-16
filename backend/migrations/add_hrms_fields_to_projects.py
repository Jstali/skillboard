"""
Migration to add HRMS fields to the projects table.
Run this script to add hrms_project_id, client_name, manager_name, and status columns.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Add HRMS fields to projects table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'projects'
        """))
        existing_columns = [row[0] for row in result]
        
        # Add hrms_project_id if not exists
        if 'hrms_project_id' not in existing_columns:
            print("Adding hrms_project_id column...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN hrms_project_id VARCHAR(100) UNIQUE
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_projects_hrms_project_id 
                ON projects(hrms_project_id)
            """))
        
        # Add client_name if not exists
        if 'client_name' not in existing_columns:
            print("Adding client_name column...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN client_name VARCHAR(255)
            """))
        
        # Add manager_name if not exists
        if 'manager_name' not in existing_columns:
            print("Adding manager_name column...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN manager_name VARCHAR(255)
            """))
        
        # Add status if not exists
        if 'status' not in existing_columns:
            print("Adding status column...")
            conn.execute(text("""
                ALTER TABLE projects 
                ADD COLUMN status VARCHAR(50) DEFAULT 'Active'
            """))
        
        conn.commit()
        print("Migration completed successfully!")


if __name__ == "__main__":
    run_migration()

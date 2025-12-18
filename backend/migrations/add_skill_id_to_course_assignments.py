"""Migration to add skill_id column to course_assignments table.

This column links course assignments to specific skills for gap analysis tracking.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """Add skill_id column to course_assignments table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'course_assignments' 
            AND column_name = 'skill_id'
        """))
        
        if result.fetchone():
            print("Column 'skill_id' already exists in course_assignments table")
            return
        
        # Add the skill_id column
        print("Adding skill_id column to course_assignments table...")
        conn.execute(text("""
            ALTER TABLE course_assignments 
            ADD COLUMN skill_id INTEGER REFERENCES skills(id)
        """))
        conn.commit()
        print("Successfully added skill_id column to course_assignments table")


if __name__ == "__main__":
    run_migration()

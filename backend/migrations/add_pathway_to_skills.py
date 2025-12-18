"""Migration to add pathway column to skills table.

This supports the 3-level hierarchy: Pathway → Category → Skills
Example: Consulting → Core Legal Skills → Legal Research & Analysis
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """Add pathway column to skills table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'skills' 
            AND column_name = 'pathway'
        """))
        
        if result.fetchone():
            print("Column 'pathway' already exists in skills table")
            return
        
        # Add the pathway column
        print("Adding pathway column to skills table...")
        conn.execute(text("""
            ALTER TABLE skills 
            ADD COLUMN pathway VARCHAR NULL
        """))
        
        # Create index for pathway
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_skills_pathway ON skills(pathway)
        """))
        
        conn.commit()
        print("Successfully added pathway column to skills table")


if __name__ == "__main__":
    run_migration()

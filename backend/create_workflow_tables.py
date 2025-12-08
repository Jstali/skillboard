"""
Script to create new tables for template assignment workflow.
Run this to add employee_template_responses and skill_gap_results tables.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from app.db.models import Base, EmployeeTemplateResponse, SkillGapResult, TemplateAssignment

def create_tables():
    print("Creating new tables for template assignment workflow...")
    
    try:
        # This will create only the tables that don't exist yet
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully!")
        print("  - employee_template_responses")
        print("  - skill_gap_results")
        print("  - Added category_hr column to template_assignments (if not exists)")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()

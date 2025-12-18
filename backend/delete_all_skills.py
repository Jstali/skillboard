"""Script to delete all skills from the database.

WARNING: This will delete ALL skills and related data including:
- All skills
- All employee_skills mappings
- All team_skill_templates
- All role_requirements
- All category_skill_templates
- All courses linked to skills
- All skill_gap_results

Run with: docker exec skillboard-backend python delete_all_skills.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import SessionLocal
from app.db.models import (
    Skill, EmployeeSkill, TeamSkillTemplate, RoleRequirement,
    CategorySkillTemplate, Course, SkillGapResult, EmployeeTemplateResponse
)


def delete_all_skills():
    """Delete all skills and related data."""
    db = SessionLocal()
    
    try:
        # Count before deletion
        skill_count = db.query(Skill).count()
        emp_skill_count = db.query(EmployeeSkill).count()
        
        print(f"Found {skill_count} skills and {emp_skill_count} employee skill mappings")
        print()
        
        # Confirm deletion
        confirm = input("Are you sure you want to delete ALL skills? Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Aborted.")
            return
        
        print("\nDeleting related data...")
        
        # Delete in order of dependencies
        deleted = db.query(EmployeeTemplateResponse).delete()
        print(f"  Deleted {deleted} employee template responses")
        
        deleted = db.query(SkillGapResult).delete()
        print(f"  Deleted {deleted} skill gap results")
        
        deleted = db.query(EmployeeSkill).delete()
        print(f"  Deleted {deleted} employee skills")
        
        deleted = db.query(TeamSkillTemplate).delete()
        print(f"  Deleted {deleted} team skill templates")
        
        deleted = db.query(RoleRequirement).delete()
        print(f"  Deleted {deleted} role requirements")
        
        deleted = db.query(CategorySkillTemplate).delete()
        print(f"  Deleted {deleted} category skill templates")
        
        # Set skill_id to NULL on courses instead of deleting them
        db.execute(text("UPDATE courses SET skill_id = NULL"))
        print("  Cleared skill references from courses")
        
        # Set skill_id to NULL on course_assignments
        db.execute(text("UPDATE course_assignments SET skill_id = NULL"))
        print("  Cleared skill references from course assignments")
        
        # Now delete all skills
        deleted = db.query(Skill).delete()
        print(f"  Deleted {deleted} skills")
        
        db.commit()
        print("\n✓ All skills deleted successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    delete_all_skills()

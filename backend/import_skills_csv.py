"""Script to import skills with band requirements from CSV.

CSV format:
skill_name,category,A,B,C,L1,L2
1. Category Name,,,,,
Skill Name,Category Name,Beginner,Developing,Intermediate,Advanced,Expert

Run with: docker exec skillboard-backend python import_skills_csv.py <csv_file> [--delete-existing]
"""
import os
import sys
import csv
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import Skill, RoleRequirement, RatingEnum


def normalize_rating(rating: str) -> str | None:
    """Normalize rating string to enum value."""
    if not rating:
        return None
    rating = rating.strip().lower()
    mapping = {
        'beginner': 'Beginner',
        'developing': 'Developing',
        'intermediate': 'Intermediate',
        'advanced': 'Advanced',
        'expert': 'Expert',
    }
    return mapping.get(rating)


def is_category_header(skill_name: str) -> bool:
    """Check if row is a category header like '1. Analytical & Problem Solving'"""
    return bool(re.match(r'^\d+\.\s*.+$', skill_name.strip()))


def import_from_csv(csv_path: str, delete_existing: bool = False):
    """Import skills and requirements from CSV file."""
    db = SessionLocal()
    
    try:
        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"Found {len(rows)} rows in CSV")
        
        if delete_existing:
            print("\nDeleting existing skills and requirements...")
            from app.db.models import EmployeeSkill, TeamSkillTemplate, CategorySkillTemplate, SkillGapResult, EmployeeTemplateResponse
            from sqlalchemy import text
            
            db.query(EmployeeTemplateResponse).delete()
            db.query(SkillGapResult).delete()
            db.query(EmployeeSkill).delete()
            db.query(TeamSkillTemplate).delete()
            db.query(RoleRequirement).delete()
            db.query(CategorySkillTemplate).delete()
            db.execute(text("UPDATE courses SET skill_id = NULL"))
            db.execute(text("UPDATE course_assignments SET skill_id = NULL"))
            db.query(Skill).delete()
            db.commit()
            print("✓ Deleted existing data")
        
        skills_created = 0
        requirements_created = 0
        
        for row in rows:
            skill_name = row.get('skill_name', '').strip()
            category = row.get('category', '').strip()
            
            if not skill_name:
                continue
            
            # Skip category header rows
            if is_category_header(skill_name):
                print(f"\n=== {skill_name} ===")
                continue
            
            if not category:
                print(f"  Skipping (no category): {skill_name}")
                continue
            
            print(f"  Skill: {skill_name} ({category})")
            
            # Create or get skill
            existing_skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if existing_skill:
                skill = existing_skill
                skill.category = category
            else:
                skill = Skill(
                    name=skill_name,
                    category=category,
                    description=f"{category} skill"
                )
                db.add(skill)
                db.flush()
                skills_created += 1
            
            # Create role requirements for each band
            for band in ['A', 'B', 'C', 'L1', 'L2']:
                rating_str = row.get(band, '')
                rating = normalize_rating(rating_str)
                
                if rating:
                    existing_req = db.query(RoleRequirement).filter(
                        RoleRequirement.band == band,
                        RoleRequirement.skill_id == skill.id
                    ).first()
                    
                    if existing_req:
                        existing_req.required_rating = RatingEnum(rating)
                    else:
                        req = RoleRequirement(
                            band=band,
                            skill_id=skill.id,
                            required_rating=RatingEnum(rating),
                            is_required=True
                        )
                        db.add(req)
                        requirements_created += 1
        
        db.commit()
        
        print(f"\n✓ Created {skills_created} skills")
        print(f"✓ Created {requirements_created} role requirements")
        
        # Show summary
        print("\n=== Skills by Category ===")
        from collections import defaultdict
        skills = db.query(Skill).order_by(Skill.category, Skill.name).all()
        by_cat = defaultdict(list)
        for s in skills:
            by_cat[s.category or 'No Category'].append(s.name)
        
        for cat, lst in sorted(by_cat.items()):
            print(f"  {cat}: {len(lst)} skills")
        
        print(f"\nTotal skills: {len(skills)}")
        print(f"Total requirements: {db.query(RoleRequirement).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_skills_csv.py <csv_file> [--delete-existing]")
        print("Example: python import_skills_csv.py /app/examples/consulting_skills_template.csv --delete-existing")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    delete_existing = "--delete-existing" in sys.argv
    
    if delete_existing:
        confirm = input("This will DELETE all existing skills. Type 'YES' to confirm: ")
        if confirm != "YES":
            print("Aborted.")
            sys.exit(0)
    
    import_from_csv(csv_path, delete_existing)

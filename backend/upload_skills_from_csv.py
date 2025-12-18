"""Script to upload skills from a CSV file.

CSV format:
skill_name,category,description

Run with: docker exec skillboard-backend python upload_skills_from_csv.py <csv_file>
Example: docker exec skillboard-backend python upload_skills_from_csv.py /app/examples/skills_upload_template.csv
"""
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import Skill


def upload_skills(csv_path: str):
    """Upload skills from CSV file."""
    db = SessionLocal()
    
    try:
        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"Found {len(rows)} skills in CSV file")
        print()
        
        created = 0
        updated = 0
        errors = []
        
        for row in rows:
            skill_name = row.get('skill_name', '').strip()
            category = row.get('category', '').strip() or None
            description = row.get('description', '').strip() or None
            
            if not skill_name:
                errors.append(f"Skipped row with empty skill_name: {row}")
                continue
            
            # Check if skill exists
            existing = db.query(Skill).filter(Skill.name == skill_name).first()
            
            if existing:
                # Update existing skill
                existing.category = category
                existing.description = description
                updated += 1
                print(f"  Updated: {skill_name} ({category})")
            else:
                # Create new skill
                skill = Skill(
                    name=skill_name,
                    category=category,
                    description=description
                )
                db.add(skill)
                created += 1
                print(f"  Created: {skill_name} ({category})")
        
        db.commit()
        
        print()
        print(f"✓ Created {created} new skills")
        print(f"✓ Updated {updated} existing skills")
        
        if errors:
            print(f"\n⚠ {len(errors)} errors:")
            for e in errors:
                print(f"  - {e}")
        
        # Show summary by category
        print("\n=== Skills by Category ===")
        from collections import defaultdict
        skills = db.query(Skill).order_by(Skill.category, Skill.name).all()
        by_cat = defaultdict(list)
        for s in skills:
            by_cat[s.category or 'No Category'].append(s.name)
        
        for cat, lst in sorted(by_cat.items()):
            print(f"  {cat}: {len(lst)} skills")
        
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_skills_from_csv.py <csv_file>")
        print("Example: python upload_skills_from_csv.py /app/examples/skills_upload_template.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    upload_skills(csv_path)

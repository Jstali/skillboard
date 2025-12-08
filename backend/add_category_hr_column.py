"""
Add category_hr column to template_assignments table.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from sqlalchemy import text

def add_category_hr_column():
    print("Adding category_hr column to template_assignments table...")
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='template_assignments' 
                AND column_name='category_hr'
            """))
            
            if result.fetchone():
                print("✓ Column category_hr already exists")
            else:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE template_assignments 
                    ADD COLUMN category_hr VARCHAR
                """))
                conn.commit()
                print("✓ Column category_hr added successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    add_category_hr_column()

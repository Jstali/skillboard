
import sys
import os
from sqlalchemy import text, create_engine

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try connecting as postgres user (superuser)
# Common development passwords for postgres user: postgres, password, or empty
DB_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"
engine = create_engine(DB_URL)

def apply_fix():
    print("Applying migration fix as postgres user...")
    try:
        with engine.begin() as conn:
            # Add learning_status column
            conn.execute(text("""
                ALTER TABLE employee_skills 
                ADD COLUMN IF NOT EXISTS learning_status VARCHAR DEFAULT 'Not Started' NOT NULL;
            """))
            print("Added learning_status column.")

            # Add status_updated_at column
            conn.execute(text("""
                ALTER TABLE employee_skills 
                ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL;
            """))
            print("Added status_updated_at column.")
            
        print("Migration applied successfully!")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    apply_fix()

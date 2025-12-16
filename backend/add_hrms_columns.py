"""
Add role_id and other HRMS fields to existing tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import text

def add_columns():
    print("Adding HRMS columns to existing tables...")
    
    with engine.begin() as conn:
        # Add role_id to users table
        try:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id) DEFAULT 6
            """))
            print("  ✓ Added role_id to users table")
        except Exception as e:
            if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
                print("  - role_id already exists in users table")
            else:
                print(f"  ⚠ Error adding role_id to users: {e}")
        
        # Add HRMS fields to employees table
        new_fields = [
            ("line_manager_id", "INTEGER REFERENCES employees(id)"),
            ("grade", "VARCHAR(50)"),
            ("capability", "VARCHAR(100)"),
            ("capability_owner_id", "INTEGER REFERENCES capability_owners(id)"),
            ("role_id", "INTEGER REFERENCES roles(id) DEFAULT 6")
        ]
        
        for field_name, field_type in new_fields:
            try:
                conn.execute(text(f"""
                    ALTER TABLE employees ADD COLUMN {field_name} {field_type}
                """))
                print(f"  ✓ Added {field_name} to employees table")
            except Exception as e:
                if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
                    print(f"  - {field_name} already exists in employees table")
                else:
                    print(f"  ⚠ Error adding {field_name} to employees: {e}")
        
        # Update existing users to have Employee role
        result = conn.execute(text("""
            UPDATE users SET role_id = 6 WHERE role_id IS NULL
        """))
        print(f"\n  ✓ Updated {result.rowcount} users to Employee role")
        
        # Set admin users to System Admin role
        result = conn.execute(text("""
            UPDATE users SET role_id = 1 
            WHERE is_admin = TRUE OR email = 'admin@skillboard.com'
        """))
        print(f"  ✓ Updated {result.rowcount} users to System Admin role")
        
        # Update existing employees to have Employee role
        result = conn.execute(text("""
            UPDATE employees SET role_id = 6 WHERE role_id IS NULL
        """))
        print(f"  ✓ Updated {result.rowcount} employees to Employee role")
    
    print("\n✅ Columns added successfully!")

if __name__ == "__main__":
    add_columns()

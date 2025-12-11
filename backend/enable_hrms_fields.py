"""
Add HRMS columns to database tables
Run this to enable HRMS features
"""
import psycopg2
from psycopg2 import sql

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"

def add_hrms_columns():
    print("Adding HRMS columns to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Add columns to users table
        print("\n1. Adding role_id to users table...")
        try:
            cur.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role_id INTEGER REFERENCES roles(id) DEFAULT 6
            """)
            print("   ✅ Added role_id to users")
        except Exception as e:
            print(f"   ⚠️  role_id might already exist: {e}")
        
        # Add columns to employees table
        print("\n2. Adding HRMS columns to employees table...")
        
        columns = [
            ("line_manager_id", "INTEGER REFERENCES employees(id)"),
            ("grade", "VARCHAR(50)"),
            ("capability", "VARCHAR(100)"),
            ("capability_owner_id", "INTEGER REFERENCES capability_owners(id)"),
            ("role_id", "INTEGER REFERENCES roles(id) DEFAULT 6"),
        ]
        
        for col_name, col_type in columns:
            try:
                cur.execute(f"""
                    ALTER TABLE employees 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                """)
                print(f"   ✅ Added {col_name}")
            except Exception as e:
                print(f"   ⚠️  {col_name} might already exist: {e}")
        
        # Update existing users to have role_id = 1 (System Admin) for admin users
        print("\n3. Setting role_id for existing users...")
        cur.execute("""
            UPDATE users 
            SET role_id = 1 
            WHERE is_admin = TRUE AND role_id IS NULL
        """)
        print(f"   ✅ Updated {cur.rowcount} admin users to System Admin role")
        
        cur.execute("""
            UPDATE users 
            SET role_id = 6 
            WHERE is_admin = FALSE AND role_id IS NULL
        """)
        print(f"   ✅ Updated {cur.rowcount} regular users to Employee role")
        
        cur.close()
        conn.close()
        
        print("\n✅ All HRMS columns added successfully!")
        print("\nNext steps:")
        print("1. Uncomment HRMS fields in backend/app/db/models.py")
        print("2. Restart the backend")
        print("3. Test HRMS components at http://localhost:5173/test/hrms")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure PostgreSQL is running")
        print("- Check database credentials in the script")
        print("- Ensure you have permission to alter tables")

if __name__ == "__main__":
    add_hrms_columns()

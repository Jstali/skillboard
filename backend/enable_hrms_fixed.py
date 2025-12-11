"""
Add HRMS columns - Fixed version
"""
import psycopg2

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"

def add_hrms_columns_fixed():
    print("Adding HRMS columns to database (fixed version)...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Step 1: Add role_id to users WITHOUT default
        print("\n1. Adding role_id to users table...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INTEGER")
            print("   ✅ Added role_id column")
        except Exception as e:
            print(f"   ℹ️  Column might exist: {e}")
        
        # Step 2: Set role_id values
        print("\n2. Setting role_id values for existing users...")
        cur.execute("UPDATE users SET role_id = 1 WHERE is_admin = TRUE AND role_id IS NULL")
        print(f"   ✅ Set {cur.rowcount} admin users to role 1 (System Admin)")
        
        cur.execute("UPDATE users SET role_id = 6 WHERE is_admin = FALSE AND role_id IS NULL")
        print(f"   ✅ Set {cur.rowcount} regular users to role 6 (Employee)")
        
        # Step 3: Add foreign key constraint
        print("\n3. Adding foreign key constraint...")
        try:
            cur.execute("""
                ALTER TABLE users 
                ADD CONSTRAINT users_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES roles(id)
            """)
            print("   ✅ Added foreign key constraint")
        except Exception as e:
            print(f"   ℹ️  Constraint might exist: {e}")
        
        # Step 4: Add role_id to employees
        print("\n4. Adding role_id to employees table...")
        try:
            cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS role_id INTEGER")
            print("   ✅ Added role_id column")
        except Exception as e:
            print(f"   ℹ️  Column might exist: {e}")
        
        # Step 5: Set default role for employees
        cur.execute("UPDATE employees SET role_id = 6 WHERE role_id IS NULL")
        print(f"   ✅ Set {cur.rowcount} employees to role 6 (Employee)")
        
        # Step 6: Add foreign key for employees
        try:
            cur.execute("""
                ALTER TABLE employees 
                ADD CONSTRAINT employees_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES roles(id)
            """)
            print("   ✅ Added foreign key constraint")
        except Exception as e:
            print(f"   ℹ️  Constraint might exist: {e}")
        
        cur.close()
        conn.close()
        
        print("\n✅ ALL HRMS COLUMNS ADDED SUCCESSFULLY!")
        print("\n" + "="*60)
        print("NEXT STEPS TO ENABLE HRMS FEATURES:")
        print("="*60)
        print("The database is ready. Now you need to:")
        print("1. Uncomment HRMS fields in backend/app/db/models.py")
        print("2. Restart the backend server")
        print("3. Test at: http://localhost:5173/test/hrms")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    add_hrms_columns_fixed()

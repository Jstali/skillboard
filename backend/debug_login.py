import os
import sys

# Set env var explicitly for the script - though now the default should work too
# We set it to ensure we test what we expect
os.environ["DATABASE_URL"] = "postgresql://skillboard:skillboard@localhost:5432/skillboard"

# Import AFTER setting env var (though irrelevant if we rely on default)
from app.db.database import SessionLocal
from app.db import crud
from app.core.security import verify_password

def test_login():
    db = SessionLocal()
    try:
        print("--- Debugging Login (Fixed) ---")
        
        # Check Admin
        print("\nChecking Admin User (admin@skillboard.com)...")
        user = crud.get_user_by_email(db, email="admin@skillboard.com")
        if not user:
            print("ERROR: Admin user not found!")
        else:
            print(f"User found: {user.email}")
            print(f"Hash start: {user.password_hash[:10]}...")
            is_valid = verify_password("admin123", user.password_hash)
            if is_valid:
                print("SUCCESS: Password 'admin123' verified!")
            else:
                print("FAILURE: Password verification failed!")

        # Check Employee
        print("\nChecking Employee User (stalinj4747@gmail.com)...")
        user_emp = crud.get_user_by_email(db, email="stalinj4747@gmail.com")
        if not user_emp:
            print("ERROR: Employee user not found!")
        else:
            print(f"User found: {user_emp.email}")
            is_valid = verify_password("admin123", user_emp.password_hash)
            if is_valid:
                print("SUCCESS: Password 'admin123' verified!")
            else:
                print("FAILURE: Password verification failed!")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_login()

"""Fix Delivery Manager role for deliverymanager@nxzen.com"""
import sys
import os
sys.path.insert(0, '.')

from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

from app.db.database import SessionLocal
from app.db.models import User, Employee

def fix_dm_role():
    db = SessionLocal()
    try:
        email = "deliverymanager@nxzen.com"
        
        # Update User role
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User found: {user.email}, current role_id: {user.role_id}")
            user.role_id = 4  # Delivery Manager
            print(f"Updated user role_id to: 4 (Delivery Manager)")
        else:
            print(f"User not found: {email}")
        
        # Update Employee role
        employee = db.query(Employee).filter(Employee.company_email == email).first()
        if employee:
            print(f"Employee found: {employee.name}, current role_id: {employee.role_id}")
            employee.role_id = 4  # Delivery Manager
            print(f"Updated employee role_id to: 4 (Delivery Manager)")
        else:
            print(f"Employee not found: {email}")
        
        db.commit()
        print("\n✅ Done! Please log out and log back in.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_dm_role()

"""Setup test users for Line Manager and Delivery Manager roles.

This script creates:
1. linemanager@nxzen.com - Line Manager role (role_id=5)
2. deliverymanager@nxzen.com - Delivery Manager role (role_id=4)
3. saivaishnav.thota@nxzen.com - Employee role (role_id=6)

Run with: python setup_test_users.py
"""
import sys
import os

# Set up path
sys.path.insert(0, '.')

# Load environment from .env file
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

from app.db.database import SessionLocal, engine
from app.db.models import User, Employee, Role, Base
from app.core.security import get_password_hash

# Default password for all test users
DEFAULT_PASSWORD = "12345678"

# Test users to create
TEST_USERS = [
    {
        "email": "linemanager@nxzen.com",
        "employee_id": "LM001",
        "name": "Line Manager",
        "first_name": "Line",
        "last_name": "Manager",
        "role_id": 5,  # LINE_MANAGER
        "location_id": "LOC001",
        "capability": "Technical Delivery"
    },
    {
        "email": "deliverymanager@nxzen.com",
        "employee_id": "DM001",
        "name": "Delivery Manager",
        "first_name": "Delivery",
        "last_name": "Manager",
        "role_id": 4,  # DELIVERY_MANAGER
        "location_id": "LOC001",
        "capability": "Delivery"
    },
    {
        "email": "saivaishnav.thota@nxzen.com",
        "employee_id": "EMP001",
        "name": "Sai Vaishnav Thota",
        "first_name": "Sai Vaishnav",
        "last_name": "Thota",
        "role_id": 6,  # EMPLOYEE
        "location_id": "LOC001",
        "capability": "Technical Delivery",
        "line_manager_email": "linemanager@nxzen.com"  # Will be linked to LM
    }
]

def setup_users():
    """Create test users and employees."""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("Setting up test users for SkillBoard")
        print("="*60)
        
        # First pass: Create all employees and users
        employee_map = {}  # email -> Employee object
        
        for user_data in TEST_USERS:
            email = user_data["email"]
            employee_id = user_data["employee_id"]
            
            print(f"\n--- Processing: {email} ---")
            
            # Check if employee exists
            employee = db.query(Employee).filter(
                (Employee.employee_id == employee_id) | 
                (Employee.company_email == email)
            ).first()
            
            if employee:
                print(f"  Employee exists: {employee.name} (ID: {employee.employee_id})")
                # Update fields
                employee.name = user_data["name"]
                employee.first_name = user_data["first_name"]
                employee.last_name = user_data["last_name"]
                employee.company_email = email
                employee.location_id = user_data.get("location_id")
                employee.capability = user_data.get("capability")
                employee.home_capability = user_data.get("capability")
                employee.role_id = user_data["role_id"]
                employee.is_active = True
            else:
                print(f"  Creating employee: {user_data['name']}")
                employee = Employee(
                    employee_id=employee_id,
                    name=user_data["name"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    company_email=email,
                    location_id=user_data.get("location_id"),
                    capability=user_data.get("capability"),
                    home_capability=user_data.get("capability"),
                    role_id=user_data["role_id"],
                    is_active=True
                )
                db.add(employee)
            
            db.flush()  # Get the employee ID
            employee_map[email] = employee
            
            # Check if user exists by email OR employee_id
            user = db.query(User).filter(
                (User.email == email) | (User.employee_id == employee_id)
            ).first()
            
            if user:
                print(f"  User exists: {user.email} (employee_id: {user.employee_id})")
                # Update user
                user.email = email
                user.employee_id = employee_id
                user.role_id = user_data["role_id"]
                user.is_active = True
                user.password_hash = get_password_hash(DEFAULT_PASSWORD)
            else:
                print(f"  Creating user: {email}")
                user = User(
                    email=email,
                    employee_id=employee_id,
                    password_hash=get_password_hash(DEFAULT_PASSWORD),
                    role_id=user_data["role_id"],
                    is_active=True,
                    is_admin=False,
                    must_change_password=False
                )
                db.add(user)
        
        db.flush()
        
        # Second pass: Set up line manager relationships
        print("\n--- Setting up line manager relationships ---")
        for user_data in TEST_USERS:
            if "line_manager_email" in user_data:
                emp_email = user_data["email"]
                lm_email = user_data["line_manager_email"]
                
                employee = employee_map.get(emp_email)
                line_manager = employee_map.get(lm_email)
                
                if employee and line_manager:
                    employee.line_manager_id = line_manager.id
                    print(f"  {employee.name} -> reports to -> {line_manager.name}")
                else:
                    print(f"  WARNING: Could not link {emp_email} to {lm_email}")
        
        db.commit()
        
        print("\n" + "="*60)
        print("Setup complete!")
        print("="*60)
        print(f"\nDefault password for all users: {DEFAULT_PASSWORD}")
        print("\nCreated users:")
        for user_data in TEST_USERS:
            role_name = {1: "Admin", 2: "HR", 3: "CP", 4: "DM", 5: "LM", 6: "Employee"}.get(user_data["role_id"], "Unknown")
            print(f"  - {user_data['email']} ({role_name})")
        
        print("\nYou can now log in with these accounts!")
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    setup_users()

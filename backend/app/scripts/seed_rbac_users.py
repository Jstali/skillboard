"""Seed script for RBAC users - compatible with existing User/Employee models"""
import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.db.models import Base, User, Employee, Role
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Role IDs (must match your roles table)
ROLES = {
    "system_admin": 1,
    "hr": 2,
    "capability_partner": 3,
    "delivery_manager": 4,
    "line_manager": 5,
    "employee": 6,
}

DUMMY_USERS = [
    # System Admin
    {"employee_id": "ADM001", "email": "admin@skillboard.com", "name": "Admin User", "first_name": "Admin", "last_name": "User",
     "role_id": 1, "capability": None, "password": "Admin@123!", "department": "IT", "is_admin": True},
    
    # HR (2)
    {"employee_id": "HR001", "email": "priya.sharma@skillboard.com", "name": "Priya Sharma", "first_name": "Priya", "last_name": "Sharma",
     "role_id": 2, "capability": None, "password": "Priya@123!", "department": "Human Resources", "is_admin": False},
    {"employee_id": "HR002", "email": "rahul.verma@skillboard.com", "name": "Rahul Verma", "first_name": "Rahul", "last_name": "Verma",
     "role_id": 2, "capability": None, "password": "Rahul@123!", "department": "Human Resources", "is_admin": False},
    
    # Capability Partners (2)
    {"employee_id": "CP001", "email": "anita.desai@skillboard.com", "name": "Anita Desai", "first_name": "Anita", "last_name": "Desai",
     "role_id": 3, "capability": "Engineering", "password": "Anita@123!", "department": "Engineering", "is_admin": False},
    {"employee_id": "CP002", "email": "vikram.patel@skillboard.com", "name": "Vikram Patel", "first_name": "Vikram", "last_name": "Patel",
     "role_id": 3, "capability": "Data Science", "password": "Vikram@123!", "department": "Data Science", "is_admin": False},
    
    # Delivery Managers (2)
    {"employee_id": "DM001", "email": "suresh.kumar@skillboard.com", "name": "Suresh Kumar", "first_name": "Suresh", "last_name": "Kumar",
     "role_id": 4, "capability": "Engineering", "password": "Suresh@123!", "department": "Engineering", "is_admin": False},
    {"employee_id": "DM002", "email": "meera.nair@skillboard.com", "name": "Meera Nair", "first_name": "Meera", "last_name": "Nair",
     "role_id": 4, "capability": "Data Science", "password": "Meera@123!", "department": "Data Science", "is_admin": False},
    
    # Line Managers (3)
    {"employee_id": "LM001", "email": "arun.reddy@skillboard.com", "name": "Arun Reddy", "first_name": "Arun", "last_name": "Reddy",
     "role_id": 5, "capability": "Engineering", "password": "Arun@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "DM001"},
    {"employee_id": "LM002", "email": "kavitha.iyer@skillboard.com", "name": "Kavitha Iyer", "first_name": "Kavitha", "last_name": "Iyer",
     "role_id": 5, "capability": "Engineering", "password": "Kavitha@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "DM001"},
    {"employee_id": "LM003", "email": "deepak.joshi@skillboard.com", "name": "Deepak Joshi", "first_name": "Deepak", "last_name": "Joshi",
     "role_id": 5, "capability": "Data Science", "password": "Deepak@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "DM002"},
    
    # Employees (15)
    {"employee_id": "EMP001", "email": "sanjay.gupta@skillboard.com", "name": "Sanjay Gupta", "first_name": "Sanjay", "last_name": "Gupta",
     "role_id": 6, "capability": "Engineering", "password": "Sanjay@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM001"},
    {"employee_id": "EMP002", "email": "neha.singh@skillboard.com", "name": "Neha Singh", "first_name": "Neha", "last_name": "Singh",
     "role_id": 6, "capability": "Engineering", "password": "Neha@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM001"},
    {"employee_id": "EMP003", "email": "amit.sharma@skillboard.com", "name": "Amit Sharma", "first_name": "Amit", "last_name": "Sharma",
     "role_id": 6, "capability": "Engineering", "password": "Amit@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM002"},
    {"employee_id": "EMP004", "email": "pooja.mehta@skillboard.com", "name": "Pooja Mehta", "first_name": "Pooja", "last_name": "Mehta",
     "role_id": 6, "capability": "Engineering", "password": "Pooja@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM002"},
    {"employee_id": "EMP005", "email": "ravi.krishnan@skillboard.com", "name": "Ravi Krishnan", "first_name": "Ravi", "last_name": "Krishnan",
     "role_id": 6, "capability": "Data Science", "password": "Ravi@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
    {"employee_id": "EMP006", "email": "sunita.rao@skillboard.com", "name": "Sunita Rao", "first_name": "Sunita", "last_name": "Rao",
     "role_id": 6, "capability": "Data Science", "password": "Sunita@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
    {"employee_id": "EMP007", "email": "karthik.menon@skillboard.com", "name": "Karthik Menon", "first_name": "Karthik", "last_name": "Menon",
     "role_id": 6, "capability": "Engineering", "password": "Karthik@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM001"},
    {"employee_id": "EMP008", "email": "divya.pillai@skillboard.com", "name": "Divya Pillai", "first_name": "Divya", "last_name": "Pillai",
     "role_id": 6, "capability": "Data Science", "password": "Divya@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
    {"employee_id": "EMP009", "email": "rajesh.nambiar@skillboard.com", "name": "Rajesh Nambiar", "first_name": "Rajesh", "last_name": "Nambiar",
     "role_id": 6, "capability": "Engineering", "password": "Rajesh@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM002"},
    {"employee_id": "EMP010", "email": "lakshmi.venkat@skillboard.com", "name": "Lakshmi Venkat", "first_name": "Lakshmi", "last_name": "Venkat",
     "role_id": 6, "capability": "Data Science", "password": "Lakshmi@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
    {"employee_id": "EMP011", "email": "mohan.das@skillboard.com", "name": "Mohan Das", "first_name": "Mohan", "last_name": "Das",
     "role_id": 6, "capability": "Engineering", "password": "Mohan@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM001"},
    {"employee_id": "EMP012", "email": "anjali.bhat@skillboard.com", "name": "Anjali Bhat", "first_name": "Anjali", "last_name": "Bhat",
     "role_id": 6, "capability": "Engineering", "password": "Anjali@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM002"},
    {"employee_id": "EMP013", "email": "vivek.srinivasan@skillboard.com", "name": "Vivek Srinivasan", "first_name": "Vivek", "last_name": "Srinivasan",
     "role_id": 6, "capability": "Data Science", "password": "Vivek@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
    {"employee_id": "EMP014", "email": "sneha.kulkarni@skillboard.com", "name": "Sneha Kulkarni", "first_name": "Sneha", "last_name": "Kulkarni",
     "role_id": 6, "capability": "Engineering", "password": "Sneha@123!", "department": "Engineering", "is_admin": False,
     "line_manager_emp_id": "LM001"},
    {"employee_id": "EMP015", "email": "arjun.nair@skillboard.com", "name": "Arjun Nair", "first_name": "Arjun", "last_name": "Nair",
     "role_id": 6, "capability": "Data Science", "password": "Arjun@123!", "department": "Data Science", "is_admin": False,
     "line_manager_emp_id": "LM003"},
]


def seed_roles(db: Session):
    """Seed roles if they don't exist"""
    role_names = [
        (1, "system_admin", "Full system access"),
        (2, "hr", "HR full access to employee data"),
        (3, "capability_partner", "View capability employees"),
        (4, "delivery_manager", "View delivery unit employees"),
        (5, "line_manager", "View direct reports"),
        (6, "employee", "Self-view only"),
    ]
    for role_id, name, desc in role_names:
        existing = db.query(Role).filter(Role.id == role_id).first()
        if not existing:
            role = Role(id=role_id, name=name, description=desc)
            db.add(role)
    db.commit()
    print("✓ Roles seeded")


def seed_data():
    """Seed the database with dummy users"""
    db = SessionLocal()
    
    try:
        # Seed roles first
        seed_roles(db)
        
        emp_id_to_db_id = {}
        
        # First pass: Create all employees and users
        for user_data in DUMMY_USERS:
            # Check if employee exists
            existing_emp = db.query(Employee).filter(Employee.employee_id == user_data["employee_id"]).first()
            if existing_emp:
                emp_id_to_db_id[user_data["employee_id"]] = existing_emp.id
                # Update employee with role info
                existing_emp.capability = user_data.get("capability")
                existing_emp.role_id = user_data["role_id"]
            else:
                # Create Employee
                employee = Employee(
                    employee_id=user_data["employee_id"],
                    name=user_data["name"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    company_email=user_data["email"],
                    department=user_data["department"],
                    capability=user_data.get("capability"),
                    role_id=user_data["role_id"],
                )
                db.add(employee)
                db.flush()
                emp_id_to_db_id[user_data["employee_id"]] = employee.id
            
            # Check if user exists by email OR employee_id
            existing_user = db.query(User).filter(
                (User.email == user_data["email"]) | (User.employee_id == user_data["employee_id"])
            ).first()
            if existing_user:
                # Update password and role
                existing_user.password_hash = pwd_context.hash(user_data["password"])
                existing_user.role_id = user_data["role_id"]
                existing_user.is_admin = user_data.get("is_admin", False)
                existing_user.email = user_data["email"]  # Update email if needed
                existing_user.employee_id = user_data["employee_id"]
                print(f"  Updated {user_data['email']}")
            else:
                # Create User
                user = User(
                    employee_id=user_data["employee_id"],
                    email=user_data["email"],
                    password_hash=pwd_context.hash(user_data["password"]),
                    is_active=True,
                    is_admin=user_data.get("is_admin", False),
                    must_change_password=True,
                    role_id=user_data["role_id"],
                )
                db.add(user)
                print(f"  Created {user_data['email']}")
            
            db.flush()  # Flush after each user to avoid batch insert issues
        
        db.commit()
        
        # Second pass: Set line manager relationships
        for user_data in DUMMY_USERS:
            if "line_manager_emp_id" in user_data:
                emp = db.query(Employee).filter(Employee.employee_id == user_data["employee_id"]).first()
                manager_db_id = emp_id_to_db_id.get(user_data["line_manager_emp_id"])
                if emp and manager_db_id:
                    emp.line_manager_id = manager_db_id
        
        db.commit()
        
        print(f"\n✓ Seeded {len(DUMMY_USERS)} users successfully!")
        print("\n" + "="*100)
        print("LOGIN CREDENTIALS")
        print("="*100)
        print(f"{'Email':<45} {'Password':<15} {'Role'}")
        print("-"*100)
        for u in DUMMY_USERS:
            role_name = [k for k, v in ROLES.items() if v == u["role_id"]][0]
            print(f"{u['email']:<45} {u['password']:<15} {role_name}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()

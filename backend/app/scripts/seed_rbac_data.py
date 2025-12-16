"""Seed script for RBAC dummy data"""
import os
import sys
from datetime import datetime, timedelta
import random

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal, Base
from app.models.rbac import UserWithRBAC, Role, Capability
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DUMMY_USERS = [
    # System Admin
    {"employee_id": "ADM001", "email": "admin@skillboard.com", "first_name": "Admin", "last_name": "User", 
     "role": Role.SYSTEM_ADMIN, "capability": None, "password": "Admin@123!", "department": "IT"},
    
    # HR (2)
    {"employee_id": "HR001", "email": "priya.sharma@skillboard.com", "first_name": "Priya", "last_name": "Sharma",
     "role": Role.HR, "capability": None, "password": "Priya@123!", "department": "Human Resources"},
    {"employee_id": "HR002", "email": "rahul.verma@skillboard.com", "first_name": "Rahul", "last_name": "Verma",
     "role": Role.HR, "capability": None, "password": "Rahul@123!", "department": "Human Resources"},
    
    # Capability Partners (2)
    {"employee_id": "CP001", "email": "anita.desai@skillboard.com", "first_name": "Anita", "last_name": "Desai",
     "role": Role.CAPABILITY_PARTNER, "capability": Capability.ENGINEERING, "password": "Anita@123!", "department": "Engineering"},
    {"employee_id": "CP002", "email": "vikram.patel@skillboard.com", "first_name": "Vikram", "last_name": "Patel",
     "role": Role.CAPABILITY_PARTNER, "capability": Capability.DATA_SCIENCE, "password": "Vikram@123!", "department": "Data Science"},
    
    # Delivery Managers (2)
    {"employee_id": "DM001", "email": "suresh.kumar@skillboard.com", "first_name": "Suresh", "last_name": "Kumar",
     "role": Role.DELIVERY_MANAGER, "capability": Capability.ENGINEERING, "password": "Suresh@123!", "department": "Engineering"},
    {"employee_id": "DM002", "email": "meera.nair@skillboard.com", "first_name": "Meera", "last_name": "Nair",
     "role": Role.DELIVERY_MANAGER, "capability": Capability.DATA_SCIENCE, "password": "Meera@123!", "department": "Data Science"},
    
    # Line Managers (3)
    {"employee_id": "LM001", "email": "arun.reddy@skillboard.com", "first_name": "Arun", "last_name": "Reddy",
     "role": Role.LINE_MANAGER, "capability": Capability.ENGINEERING, "password": "Arun@123!", "department": "Engineering",
     "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "LM002", "email": "kavitha.iyer@skillboard.com", "first_name": "Kavitha", "last_name": "Iyer",
     "role": Role.LINE_MANAGER, "capability": Capability.ENGINEERING, "password": "Kavitha@123!", "department": "Engineering",
     "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "LM003", "email": "deepak.joshi@skillboard.com", "first_name": "Deepak", "last_name": "Joshi",
     "role": Role.LINE_MANAGER, "capability": Capability.DATA_SCIENCE, "password": "Deepak@123!", "department": "Data Science",
     "delivery_manager_email": "meera.nair@skillboard.com"},
    
    # Employees (15)
    {"employee_id": "EMP001", "email": "sanjay.gupta@skillboard.com", "first_name": "Sanjay", "last_name": "Gupta",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Sanjay@123!", "department": "Engineering",
     "line_manager_email": "arun.reddy@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP002", "email": "neha.singh@skillboard.com", "first_name": "Neha", "last_name": "Singh",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Neha@123!", "department": "Engineering",
     "line_manager_email": "arun.reddy@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP003", "email": "amit.sharma@skillboard.com", "first_name": "Amit", "last_name": "Sharma",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Amit@123!", "department": "Engineering",
     "line_manager_email": "kavitha.iyer@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP004", "email": "pooja.mehta@skillboard.com", "first_name": "Pooja", "last_name": "Mehta",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Pooja@123!", "department": "Engineering",
     "line_manager_email": "kavitha.iyer@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP005", "email": "ravi.krishnan@skillboard.com", "first_name": "Ravi", "last_name": "Krishnan",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Ravi@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
    {"employee_id": "EMP006", "email": "sunita.rao@skillboard.com", "first_name": "Sunita", "last_name": "Rao",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Sunita@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
    {"employee_id": "EMP007", "email": "karthik.menon@skillboard.com", "first_name": "Karthik", "last_name": "Menon",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Karthik@123!", "department": "Engineering",
     "line_manager_email": "arun.reddy@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP008", "email": "divya.pillai@skillboard.com", "first_name": "Divya", "last_name": "Pillai",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Divya@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
    {"employee_id": "EMP009", "email": "rajesh.nambiar@skillboard.com", "first_name": "Rajesh", "last_name": "Nambiar",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Rajesh@123!", "department": "Engineering",
     "line_manager_email": "kavitha.iyer@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP010", "email": "lakshmi.venkat@skillboard.com", "first_name": "Lakshmi", "last_name": "Venkat",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Lakshmi@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
    {"employee_id": "EMP011", "email": "mohan.das@skillboard.com", "first_name": "Mohan", "last_name": "Das",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Mohan@123!", "department": "Engineering",
     "line_manager_email": "arun.reddy@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP012", "email": "anjali.bhat@skillboard.com", "first_name": "Anjali", "last_name": "Bhat",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Anjali@123!", "department": "Engineering",
     "line_manager_email": "kavitha.iyer@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP013", "email": "vivek.srinivasan@skillboard.com", "first_name": "Vivek", "last_name": "Srinivasan",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Vivek@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
    {"employee_id": "EMP014", "email": "sneha.kulkarni@skillboard.com", "first_name": "Sneha", "last_name": "Kulkarni",
     "role": Role.EMPLOYEE, "capability": Capability.ENGINEERING, "password": "Sneha@123!", "department": "Engineering",
     "line_manager_email": "arun.reddy@skillboard.com", "delivery_manager_email": "suresh.kumar@skillboard.com"},
    {"employee_id": "EMP015", "email": "arjun.nair@skillboard.com", "first_name": "Arjun", "last_name": "Nair",
     "role": Role.EMPLOYEE, "capability": Capability.DATA_SCIENCE, "password": "Arjun@123!", "department": "Data Science",
     "line_manager_email": "deepak.joshi@skillboard.com", "delivery_manager_email": "meera.nair@skillboard.com"},
]

SKILLS = ["Python", "React", "AWS", "Machine Learning", "SQL", "Docker", "Kubernetes", "TypeScript", "FastAPI", "TensorFlow"]
RATINGS = ["Beginner", "Intermediate", "Advanced"]


def seed_data():
    """Seed the database with dummy RBAC data"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data exists
        if db.query(UserWithRBAC).first():
            print("Data already exists. Skipping seed.")
            return
        
        email_to_id = {}
        
        # First pass: Create all users without relationships
        for user_data in DUMMY_USERS:
            user = UserWithRBAC(
                employee_id=user_data["employee_id"],
                email=user_data["email"],
                hashed_password=pwd_context.hash(user_data["password"]),
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                capability=user_data.get("capability"),
                department=user_data.get("department"),
                joining_date=datetime.utcnow() - timedelta(days=random.randint(30, 1000)),
                personal_email=f"{user_data['first_name'].lower()}.personal@gmail.com",
                phone_number=f"+91-{random.randint(7000000000, 9999999999)}",
                salary=random.randint(50000, 200000),
                performance_rating=random.choice(RATINGS),
                must_change_password=True,
                is_active=True
            )
            db.add(user)
            db.flush()
            email_to_id[user_data["email"]] = user.id
        
        # Second pass: Set relationships
        for user_data in DUMMY_USERS:
            if "line_manager_email" in user_data or "delivery_manager_email" in user_data:
                user = db.query(UserWithRBAC).filter(UserWithRBAC.email == user_data["email"]).first()
                if "line_manager_email" in user_data:
                    user.line_manager_id = email_to_id.get(user_data["line_manager_email"])
                if "delivery_manager_email" in user_data:
                    user.delivery_manager_id = email_to_id.get(user_data["delivery_manager_email"])
        
        db.commit()
        print(f"✓ Seeded {len(DUMMY_USERS)} users successfully!")
        
        # Print credentials table
        print("\n" + "="*100)
        print("LOGIN CREDENTIALS (DEV ONLY - DO NOT USE IN PRODUCTION)")
        print("="*100)
        print(f"{'Name':<25} {'Role':<20} {'Email':<40} {'Password':<15}")
        print("-"*100)
        for u in DUMMY_USERS:
            print(f"{u['first_name']} {u['last_name']:<18} {u['role'].value:<20} {u['email']:<40} {u['password']:<15}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()

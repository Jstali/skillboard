
import sys
import os
import random

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import SessionLocal, engine
from app.db.models import Base, User, Employee, Skill, EmployeeSkill
from app.core.security import get_password_hash

def create_test_users():
    db = SessionLocal()
    try:
        # Define test users
        test_users = [
            {
                "employee_id": "EMP001",
                "name": "Alice Engineer",
                "email": "alice@skillboard.com",
                "department": "Engineering",
                "role": "Software Engineer",
                "band": "B",
                "team": "Technical Delivery"
            },
            {
                "employee_id": "EMP002",
                "name": "Bob Lead",
                "email": "bob@skillboard.com",
                "department": "Engineering",
                "role": "Team Lead",
                "band": "C",
                "team": "Technical Delivery"
            },
            {
                "employee_id": "EMP003",
                "name": "Charlie HR",
                "email": "charlie@skillboard.com",
                "department": "HR",
                "role": "HR Manager",
                "band": "C",
                "team": "Corporate Functions - PC"
            },
            {
                "employee_id": "EMP004",
                "name": "David Sales",
                "email": "david@skillboard.com",
                "department": "Sales",
                "role": "Sales Executive",
                "band": "A",
                "team": "Consulting"
            },
            {
                "employee_id": "EMP005",
                "name": "Eve Product",
                "email": "eve@skillboard.com",
                "department": "Product",
                "role": "Product Manager",
                "band": "B",
                "team": "Consulting"
            }
        ]

        print("Creating Test Users and Skills...")
        print("-" * 50)
        
        credentials = []

        # 0. Ensure Skills Exist
        skills_data = [
            "Python", "React", "Docker", "AWS", "Kubernetes", 
            "Leadership", "Project Management", "Agile", "Scrum",
            "Communication", "Excel", "Data Analysis", "Recruiting",
            "Sales", "Negotiation", "Marketing", "CRM",
            "Product Management", "UX Design", "Roadmapping"
        ]
        
        skill_map = {}
        for skill_name in skills_data:
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if not skill:
                skill = Skill(name=skill_name, category="General", description=f"Mastery of {skill_name}")
                db.add(skill)
                db.commit() # Commit to get ID
                db.refresh(skill)
                print(f"Created Skill: {skill_name}")
            skill_map[skill_name] = skill

        for user_data in test_users:
            # 1. Create/Update Employee
            employee = db.query(Employee).filter(Employee.employee_id == user_data["employee_id"]).first()
            if not employee:
                employee = Employee(
                    employee_id=user_data["employee_id"],
                    name=user_data["name"],
                    company_email=user_data["email"],
                    department=user_data["department"],
                    role=user_data["role"],
                    band=user_data["band"],
                    team=user_data["team"],
                    category="Employee"
                )
                db.add(employee)
                db.commit()
                db.refresh(employee)
                print(f"Created Employee: {user_data['name']}")
            else:
                print(f"Employee exists: {user_data['name']}")
            
            # 2. Create/Update User
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if not user:
                user = User(
                    email=user_data["email"],
                    employee_id=user_data["employee_id"],
                    password_hash=get_password_hash("password123"), # Default password
                    is_active=True,
                    is_admin=False # Regular users
                )
                db.add(user)
                print(f"Created User: {user_data['email']}")
            else:
                print(f"User exists: {user_data['email']}")
            
            credentials.append(f"Email: {user_data['email']} | Password: password123")

            # 3. Assign Skills
            # Define skills for each role (mix of current and interested)
            role_skills = []
            if "Engineer" in user_data["role"]:
                role_skills = [
                    ("Python", "Expert", False), ("React", "Intermediate", False), ("Docker", "Beginner", True), ("AWS", None, True)
                ]
            elif "Lead" in user_data["role"]:
                role_skills = [
                    ("Python", "Expert", False), ("Leadership", "Intermediate", False), ("Agile", "Advanced", False), ("Project Management", None, True)
                ]
            elif "HR" in user_data["role"]:
                role_skills = [
                    ("Communication", "Expert", False), ("Recruiting", "Advanced", False), ("Excel", "Intermediate", False), ("Data Analysis", None, True)
                ]
            elif "Sales" in user_data["role"]:
                role_skills = [
                    ("Sales", "Expert", False), ("Negotiation", "Advanced", False), ("CRM", "Intermediate", False), ("Marketing", None, True)
                ]
            elif "Product" in user_data["role"]:
                role_skills = [
                    ("Product Management", "Expert", False), ("Agile", "Advanced", False), ("UX Design", "Beginner", False), ("Data Analysis", None, True)
                ]
            
            for s_name, rating, is_interested in role_skills:
                skill_obj = skill_map.get(s_name)
                if skill_obj:
                    # Check if assignment exists
                    existing = db.query(EmployeeSkill).filter(
                        EmployeeSkill.employee_id == employee.id,
                        EmployeeSkill.skill_id == skill_obj.id
                    ).first()
                    
                    if not existing:
                        emp_skill = EmployeeSkill(
                            employee_id=employee.id,
                            skill_id=skill_obj.id,
                            rating=rating if not is_interested else None,
                            initial_rating=rating if not is_interested else None,
                            years_experience=random.randint(1, 10) if not is_interested else 0,
                            is_interested=is_interested,
                            notes="Auto-assigned by script"
                        )
                        db.add(emp_skill)
                        print(f"  -> Assigned {'Interested ' if is_interested else ''}Skill: {s_name}")

        db.commit()
        print("-" * 50)
        print("SUCCESS! Users and Skills updated.")
        print("\nLogin Credentials:")
        for cred in credentials:
            print(cred)

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()

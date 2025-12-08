import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Employee

def update_stalin_role():
    db = SessionLocal()
    try:
        # Find stalin J employee
        employee = db.query(Employee).filter(
            (Employee.name == "stalin J") | (Employee.employee_id == "E001")
        ).first()
        
        if employee:
            print(f"Found employee: {employee.name} (ID: {employee.employee_id})")
            print(f"Current role: {employee.role}")
            print(f"Current band: {employee.band}")
            
            # Update role to Consultant
            employee.role = "Consultant"
            
            db.commit()
            db.refresh(employee)
            
            print(f"\nUpdated successfully!")
            print(f"New role: {employee.role}")
        else:
            print("Employee 'stalin J' not found in database")
            
            # Show all employees
            print("\nAll employees in database:")
            all_employees = db.query(Employee).all()
            for emp in all_employees:
                print(f"  - {emp.name} ({emp.employee_id}): Role={emp.role}, Band={emp.band}")
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_stalin_role()

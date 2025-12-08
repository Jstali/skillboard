
import sys
import os
import json
import asyncio
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock missing dependency
from unittest.mock import MagicMock
sys.modules["pyexcel_ods3"] = MagicMock()

from app.db.database import get_db
from app.db.models import User, Employee, SkillTemplate, TemplateAssignment
from app.api.templates import assign_template_to_employees, AssignmentRequest

# Mock User
mock_user = User(id=1, email="admin@example.com", is_admin=True)

async def test_bulk_assign():
    print("=" * 60)
    print("Verifying Bulk Assignment Logic (Department/Role) - Direct Function Call")
    print("=" * 60)

    db_gen = get_db()
    db = next(db_gen)

    try:
        print(" > Setting up test data...")
        dept_name = "TestDept_Verification"
        role_name = "TestRole_Verification"
        
        # Cleanup
        db.query(Employee).filter(Employee.department == dept_name).delete()
        db.query(Employee).filter(Employee.role == role_name).delete()
        # Find template if exists and delete
        existing_templates = db.query(SkillTemplate).filter(SkillTemplate.template_name == "Bulk Assign Test Template").all()
        for t in existing_templates:
            db.query(TemplateAssignment).filter(TemplateAssignment.template_id == t.id).delete()
            db.delete(t)
        db.commit()

        # Create Employees
        emp1 = Employee(name="Test Emp 1", company_email="test1@test.com", department=dept_name, role="Other", employee_id="TEST001")
        emp2 = Employee(name="Test Emp 2", company_email="test2@test.com", department=dept_name, role="Other", employee_id="TEST002")
        emp3 = Employee(name="Test Emp 3", company_email="test3@test.com", department="Other", role=role_name, employee_id="TEST003")
        
        db.add_all([emp1, emp2, emp3])
        db.commit()
        
        # Create Template
        template = SkillTemplate(
            template_name="Bulk Assign Test Template",
            file_name="test.csv",
            content=json.dumps([["Skill", "Rating"], ["Python", "Expert"]]),
            uploaded_by=1
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        
        print(f" > Created Template ID: {template.id}")

        # 1. Test Bulk Assign by Department
        print("\n[TEST 1] Assigning by Department...")
        req = AssignmentRequest(
            template_id=template.id,
            department=dept_name
        )
        
        resp = await assign_template_to_employees(req, db, mock_user)
        print(f" > Response: {resp['message']}")
        
        # Verify
        assigns_dept = db.query(TemplateAssignment).filter(
            TemplateAssignment.template_id == template.id,
            TemplateAssignment.employee_id.in_([emp1.id, emp2.id])
        ).all()
        
        if len(assigns_dept) == 2:
            print(" ✅ Success: Both department employees assigned.")
        else:
            print(f" ❌ Failure: Expected 2 assignments, found {len(assigns_dept)}")

        # 2. Test Bulk Assign by Role
        print("\n[TEST 2] Assigning by Role...")
        req_role = AssignmentRequest(
            template_id=template.id,
            role=role_name
        )
        resp = await assign_template_to_employees(req_role, db, mock_user)
        print(f" > Response: {resp['message']}")
        
        # Verify
        assigns_role = db.query(TemplateAssignment).filter(
            TemplateAssignment.template_id == template.id,
            TemplateAssignment.employee_id == emp3.id
        ).first()
        
        if assigns_role:
            print(" ✅ Success: Role employee assigned.")
        else:
            print(" ❌ Failure: Role employee NOT assigned.")
            
        # Cleanup
        print("\n > Cleaning up test data...")
        db.query(TemplateAssignment).filter(TemplateAssignment.template_id == template.id).delete()
        db.query(SkillTemplate).filter(SkillTemplate.id == template.id).delete()
        db.query(Employee).filter(Employee.id.in_([emp1.id, emp2.id, emp3.id])).delete()
        db.commit()
        print(" > Cleanup complete.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_bulk_assign())

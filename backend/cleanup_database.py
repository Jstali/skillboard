"""
Script to delete all employee data except admin@skillboard.com
This will remove:
- All employee records
- All user accounts (except admin@skillboard.com)
- All related data (employee_skills, template_assignments, etc.)
"""

from app.db.database import SessionLocal
from app.db.models import (
    User, Employee, EmployeeSkill, TemplateAssignment,
    EmployeeTemplateResponse, SkillGapResult, CourseAssignment, Course
)

def cleanup_database():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("DATABASE CLEANUP - Keeping only admin@skillboard.com")
        print("=" * 60)
        
        # Get admin user
        admin_user = db.query(User).filter(User.email == "admin@skillboard.com").first()
        if not admin_user:
            print("ERROR: admin@skillboard.com not found!")
            return
        
        print(f"\n✅ Found admin user: {admin_user.email} (ID: {admin_user.id})")
        
        # Get all users except admin
        users_to_delete = db.query(User).filter(User.email != "admin@skillboard.com").all()
        print(f"\n📋 Users to delete: {len(users_to_delete)}")
        for user in users_to_delete:
            print(f"   - {user.email} (Employee ID: {user.employee_id})")
        
        # Get all employees
        all_employees = db.query(Employee).all()
        print(f"\n📋 Employees to delete: {len(all_employees)}")
        for emp in all_employees:
            print(f"   - {emp.name} ({emp.employee_id})")
        
        # Confirm deletion
        print("\n" + "=" * 60)
        print("⚠️  WARNING: This will delete ALL the above data!")
        print("=" * 60)
        confirm = input("\nType 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("\n❌ Deletion cancelled.")
            return
        
        print("\n🗑️  Starting deletion...")
        
        # Delete related data first (due to foreign key constraints)
        
        # 1. Delete course assignments
        course_assignments = db.query(CourseAssignment).all()
        count = len(course_assignments)
        for ca in course_assignments:
            db.delete(ca)
        print(f"   ✓ Deleted {count} course assignments")
        
        # 2. Delete skill gap results
        gap_results = db.query(SkillGapResult).all()
        count = len(gap_results)
        for gr in gap_results:
            db.delete(gr)
        print(f"   ✓ Deleted {count} skill gap results")
        
        # 3. Delete employee template responses
        template_responses = db.query(EmployeeTemplateResponse).all()
        count = len(template_responses)
        for tr in template_responses:
            db.delete(tr)
        print(f"   ✓ Deleted {count} template responses")
        
        # 4. Delete template assignments
        assignments = db.query(TemplateAssignment).all()
        count = len(assignments)
        for assignment in assignments:
            db.delete(assignment)
        print(f"   ✓ Deleted {count} template assignments")
        
        # 5. Delete employee skills
        employee_skills = db.query(EmployeeSkill).all()
        count = len(employee_skills)
        for es in employee_skills:
            db.delete(es)
        print(f"   ✓ Deleted {count} employee skills")
        
        # 6. Delete all employees
        count = len(all_employees)
        for emp in all_employees:
            db.delete(emp)
        print(f"   ✓ Deleted {count} employees")
        
        # 7. Handle courses created by users we're deleting
        # Option 1: Delete all courses (if you want to start fresh)
        # Option 2: Update created_by to admin's ID (if you want to keep courses)
        
        user_ids_to_delete = [user.id for user in users_to_delete]
        courses_to_update = db.query(Course).filter(Course.created_by.in_(user_ids_to_delete)).all()
        
        if courses_to_update:
            print(f"\n   ⚠️  Found {len(courses_to_update)} courses created by users being deleted")
            print(f"   → Reassigning to admin user (ID: {admin_user.id})")
            for course in courses_to_update:
                course.created_by = admin_user.id
        
        # 8. Delete all users except admin
        count = len(users_to_delete)
        for user in users_to_delete:
            db.delete(user)
        print(f"   ✓ Deleted {count} users")
        
        # Commit all deletions
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE CLEANUP COMPLETED!")
        print("=" * 60)
        
        # Verify what's left
        remaining_users = db.query(User).all()
        remaining_employees = db.query(Employee).all()
        
        print(f"\n📊 Remaining data:")
        print(f"   - Users: {len(remaining_users)}")
        for user in remaining_users:
            print(f"     • {user.email}")
        print(f"   - Employees: {len(remaining_employees)}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_database()

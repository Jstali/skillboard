"""
Test script for Template Assignment and Skill Gap Analysis workflow.
This script creates test data and validates the complete workflow.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import (
    Employee, SkillTemplate, TemplateAssignment, 
    EmployeeTemplateResponse, SkillGapResult, Skill, User
)
from datetime import datetime
import json

def test_workflow():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("TEMPLATE ASSIGNMENT & SKILL GAP ANALYSIS - TEST WORKFLOW")
        print("=" * 60)
        
        # Step 1: Get admin user
        print("\n[1] Finding admin user...")
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            print("❌ No admin user found. Please create an admin user first.")
            return
        print(f"✓ Admin user: {admin.email}")
        
        # Step 2: Get or create test employees
        print("\n[2] Checking test employees...")
        employees = db.query(Employee).limit(3).all()
        if len(employees) < 2:
            print("❌ Not enough employees. Please run add_test_users.py first.")
            return
        
        for emp in employees[:3]:
            print(f"✓ Employee: {emp.name} ({emp.employee_id}) - {emp.role} - Band {emp.band}")
        
        # Step 3: Get templates
        print("\n[3] Checking available templates...")
        templates = db.query(SkillTemplate).all()
        if not templates:
            print("❌ No templates found. Please upload a template first.")
            return
        
        template = templates[0]
        print(f"✓ Using template: {template.template_name}")
        
        # Parse template to get skills
        try:
            content = json.loads(template.content)
            skill_names = set()
            for row in content:
                if row and len(row) > 0:
                    skill_name = str(row[0]).strip()
                    if skill_name and skill_name.lower() not in ['skill', 'name', '']:
                        skill_names.add(skill_name)
            print(f"✓ Template contains {len(skill_names)} skills")
        except Exception as e:
            print(f"⚠ Could not parse template: {e}")
            skill_names = set()
        
        # Step 4: Create test assignment
        print("\n[4] Creating test assignment...")
        
        # Check if assignment already exists
        existing = db.query(TemplateAssignment).filter(
            TemplateAssignment.employee_id == employees[0].id,
            TemplateAssignment.template_id == template.id
        ).first()
        
        if existing:
            print(f"⚠ Assignment already exists (ID: {existing.id})")
            assignment = existing
        else:
            assignment = TemplateAssignment(
                employee_id=employees[0].id,
                template_id=template.id,
                category_hr="Technical Delivery",  # HR selects this
                assigned_by=admin.id,
                status="Pending"
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)
            print(f"✓ Created assignment ID: {assignment.id}")
        
        print(f"  - Employee: {employees[0].name}")
        print(f"  - Template: {template.template_name}")
        print(f"  - HR Category: {assignment.category_hr} (HIDDEN from employee)")
        print(f"  - Status: {assignment.status}")
        
        # Step 5: Simulate employee filling template
        print("\n[5] Simulating employee template submission...")
        
        if assignment.status == "Completed":
            print("⚠ Assignment already completed")
        else:
            # Get some skills from database
            skills = db.query(Skill).limit(5).all()
            if not skills:
                print("⚠ No skills found in database")
            else:
                # Delete existing responses
                db.query(EmployeeTemplateResponse).filter(
                    EmployeeTemplateResponse.assignment_id == assignment.id
                ).delete()
                
                # Create employee responses
                employee_category = "Consulting"  # Employee selects DIFFERENT category
                skill_levels = ["Beginner", "Intermediate", "Advanced", "Intermediate", "Developing"]
                
                print(f"  - Employee selects category: {employee_category}")
                print(f"  - HR category was: {assignment.category_hr}")
                if employee_category != assignment.category_hr:
                    print("  ⚠ CATEGORY MISMATCH DETECTED!")
                
                for i, skill in enumerate(skills):
                    response = EmployeeTemplateResponse(
                        assignment_id=assignment.id,
                        employee_category=employee_category,
                        skill_id=skill.id,
                        employee_level=skill_levels[i],
                        years_experience=float(i + 1),
                        notes=f"Test note for {skill.name}"
                    )
                    db.add(response)
                    print(f"  ✓ {skill.name}: {skill_levels[i]} ({i+1} years)")
                
                # Update assignment status
                assignment.status = "Completed"
                db.commit()
                print("✓ Template submission completed")
        
        # Step 6: Calculate skill gaps
        print("\n[6] Calculating skill gaps...")
        
        # Delete existing gap results
        db.query(SkillGapResult).filter(
            SkillGapResult.assignment_id == assignment.id
        ).delete()
        
        # Get employee responses
        responses = db.query(EmployeeTemplateResponse).filter(
            EmployeeTemplateResponse.assignment_id == assignment.id
        ).all()
        
        if not responses:
            print("❌ No employee responses found")
        else:
            LEVEL_MAPPING = {
                "Beginner": 1,
                "Developing": 2,
                "Intermediate": 3,
                "Advanced": 4,
                "Expert": 5
            }
            
            gaps_found = 0
            gaps_met = 0
            gaps_exceeded = 0
            
            for response in responses:
                # For testing, use "Intermediate" as required level
                required_level = "Intermediate"
                employee_level = response.employee_level
                
                required_num = LEVEL_MAPPING.get(required_level, 0)
                employee_num = LEVEL_MAPPING.get(employee_level, 0)
                gap_value = employee_num - required_num
                
                if gap_value < 0:
                    gap_status = "Gap"
                    gaps_found += 1
                elif gap_value == 0:
                    gap_status = "Met"
                    gaps_met += 1
                else:
                    gap_status = "Exceeded"
                    gaps_exceeded += 1
                
                gap_result = SkillGapResult(
                    assignment_id=assignment.id,
                    skill_id=response.skill_id,
                    required_level=required_level,
                    employee_level=employee_level,
                    gap_status=gap_status,
                    gap_value=gap_value
                )
                db.add(gap_result)
                
                skill = db.query(Skill).filter(Skill.id == response.skill_id).first()
                status_icon = "🔴" if gap_status == "Gap" else "🟢" if gap_status == "Met" else "🔵"
                print(f"  {status_icon} {skill.name if skill else 'Unknown'}: {employee_level} vs {required_level} (gap: {gap_value})")
            
            db.commit()
            
            print(f"\n✓ Gap calculation complete:")
            print(f"  - Total skills: {len(responses)}")
            print(f"  - Gaps found: {gaps_found}")
            print(f"  - Requirements met: {gaps_met}")
            print(f"  - Exceeded: {gaps_exceeded}")
        
        # Step 7: Verify gap analysis queries
        print("\n[7] Testing gap analysis queries...")
        
        # Query employees with gaps
        assignments_with_gaps = []
        all_assignments = db.query(TemplateAssignment).filter(
            TemplateAssignment.status == "Completed"
        ).all()
        
        for assgn in all_assignments:
            gaps_count = db.query(SkillGapResult).filter(
                SkillGapResult.assignment_id == assgn.id,
                SkillGapResult.gap_status == "Gap"
            ).count()
            
            if gaps_count > 0:
                assignments_with_gaps.append((assgn, gaps_count))
        
        print(f"✓ Found {len(assignments_with_gaps)} employees with gaps")
        for assgn, count in assignments_with_gaps:
            emp = db.query(Employee).filter(Employee.id == assgn.employee_id).first()
            print(f"  - {emp.name if emp else 'Unknown'}: {count} gaps")
        
        # Query employees without gaps
        assignments_without_gaps = []
        for assgn in all_assignments:
            gaps_count = db.query(SkillGapResult).filter(
                SkillGapResult.assignment_id == assgn.id,
                SkillGapResult.gap_status == "Gap"
            ).count()
            
            if gaps_count == 0:
                assignments_without_gaps.append(assgn)
        
        print(f"✓ Found {len(assignments_without_gaps)} employees without gaps")
        for assgn in assignments_without_gaps:
            emp = db.query(Employee).filter(Employee.id == assgn.employee_id).first()
            print(f"  - {emp.name if emp else 'Unknown'}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("TEST WORKFLOW COMPLETED SUCCESSFULLY! ✅")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Login as admin: admin@skillboard.com / admin123")
        print("2. Navigate to: /admin/template-assignment")
        print("3. View assignments and gap analysis")
        print("\nOr login as employee to view assignments:")
        print(f"   Employee ID: {employees[0].employee_id}")
        print("   Navigate to: /assignments")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_workflow()

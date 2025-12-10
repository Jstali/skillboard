"""API routes for employees to view and fill assigned templates."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from app.db import database
from app.db.models import (
    TemplateAssignment, Employee, SkillTemplate, User,
    EmployeeTemplateResponse, Skill, SkillGapResult, EmployeeSkill
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/employee/assignments", tags=["employee-assignments"])


# Skill level mapping for gap calculation
LEVEL_MAPPING = {
    "Beginner": 1,
    "Developing": 2,
    "Intermediate": 3,
    "Advanced": 4,
    "Expert": 5
}


def calculate_gap(required_level: str, employee_level: Optional[str]) -> tuple[str, int]:
    """Calculate skill gap between required and employee level."""
    if not employee_level:
        return ("Gap", -LEVEL_MAPPING.get(required_level, 0))
    
    required_num = LEVEL_MAPPING.get(required_level, 0)
    employee_num = LEVEL_MAPPING.get(employee_level, 0)
    gap_value = employee_num - required_num
    
    if gap_value < 0:
        return ("Gap", gap_value)
    elif gap_value == 0:
        return ("Met", gap_value)
    else:
        return ("Exceeded", gap_value)


# Pydantic Schemas
class SkillInfo(BaseModel):
    id: int
    name: str
    category: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class TemplateInfo(BaseModel):
    id: int
    name: str
    skills: List[SkillInfo]


class AssignmentSummary(BaseModel):
    id: int
    template_name: str
    assigned_at: datetime
    status: str


class AssignmentDetail(BaseModel):
    id: int
    template: TemplateInfo
    status: str
    assigned_at: datetime


class SkillResponse(BaseModel):
    skill_id: int
    level: Optional[str]
    years_experience: Optional[float]
    notes: Optional[str]


class SubmitTemplateRequest(BaseModel):
    employee_category: str
    responses: List[SkillResponse]


@router.get("/my-assignments")
async def get_my_assignments(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get employee's pending and completed assignments.
    HR category is HIDDEN from employee.
    """
    print(f"DEBUG: get_my_assignments called for user {current_user.email}")
    
    # Get employee record
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    print(f"DEBUG: Found employee: {employee.name} (id={employee.id})")
    
    # Get all assignments for this employee
    assignments = db.query(TemplateAssignment).filter(
        TemplateAssignment.employee_id == employee.id
    ).order_by(TemplateAssignment.assigned_at.desc()).all()
    
    print(f"DEBUG: Found {len(assignments)} total assignments")
    
    pending = []
    completed = []
    
    for assignment in assignments:
        template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
        
        summary = AssignmentSummary(
            id=assignment.id,
            template_id=assignment.template_id,
            template_name=template.template_name if template else "Unknown",
            assigned_at=assignment.assigned_at,
            status=assignment.status
        )
        
        if assignment.status == "Completed":
            completed.append(summary)
        else:
            pending.append(summary)
    
    print(f"DEBUG: Returning {len(pending)} pending, {len(completed)} completed")
    
    return {
        "pending": pending,
        "completed": completed
    }


@router.get("/{assignment_id}")
async def get_assignment_details(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get assignment details for filling.
    HR category is HIDDEN - employee only sees template skills.
    """
    # Get employee record
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Get assignment
    assignment = db.query(TemplateAssignment).filter(
        TemplateAssignment.id == assignment_id,
        TemplateAssignment.employee_id == employee.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Get template
    template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    
    # Parse template content to extract skills
    try:
        content = json.loads(template.content)
        skills = []
        
        # Skip header rows and extract skills
        # Row structure: [skill_name, level_A, level_B, level_C, level_L1, level_L2]
        for i, row in enumerate(content):
            if not row or len(row) == 0:
                continue
            
            skill_name = str(row[0]).strip() if row[0] else ""
            
            # Skip empty rows, headers, and category headers
            if not skill_name or skill_name.lower() in ['skill', 'name', ''] or skill_name.startswith('1.') or skill_name.startswith('2.') or skill_name.startswith('3.'):
                continue
            
            # Extract skill description (everything after the colon)
            description = ""
            if ':' in skill_name:
                parts = skill_name.split(':', 1)
                skill_name = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
            
            # Determine category from context (look back for category header)
            category = "General"
            for j in range(i-1, -1, -1):
                if content[j] and len(content[j]) > 0:
                    potential_category = str(content[j][0]).strip()
                    if potential_category and (potential_category.startswith('1.') or potential_category.startswith('2.') or potential_category.startswith('3.')):
                        category = potential_category.split('.', 1)[1].strip() if '.' in potential_category else potential_category
                        break
            
            # Create skill object with unique ID based on row index
            skills.append(SkillInfo(
                id=1000 + i,  # Use row index as ID to ensure uniqueness
                name=skill_name,
                category=category,
                description=description
            ))
        
        template_info = TemplateInfo(
            id=template.id,
            name=template.template_name,
            skills=skills
        )
        
        return AssignmentDetail(
            id=assignment.id,
            template=template_info,
            status=assignment.status,
            assigned_at=assignment.assigned_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing template: {str(e)}")


@router.post("/{assignment_id}/submit")
async def submit_template(
    assignment_id: int,
    submission: SubmitTemplateRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit filled template with employee's category selection and skill levels.
    This triggers automatic skill gap calculation.
    """
    print(f"DEBUG: submit_template called for assignment_id={assignment_id}")
    print(f"DEBUG: submission.employee_category={submission.employee_category}")
    print(f"DEBUG: submission.responses count={len(submission.responses)}")
    
    try:
        # Get employee record
        employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee record not found")
        
        print(f"DEBUG: Found employee: {employee.name}")
        
        # Get assignment
        assignment = db.query(TemplateAssignment).filter(
            TemplateAssignment.id == assignment_id,
            TemplateAssignment.employee_id == employee.id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        print(f"DEBUG: Found assignment status: {assignment.status}")
        
        # Allow re-submission even if already completed (for updates)
        # if assignment.status == "Completed":
        #     raise HTTPException(status_code=400, detail="Assignment already completed")
        
        # Delete existing responses (in case of resubmission)
        db.query(EmployeeTemplateResponse).filter(
            EmployeeTemplateResponse.assignment_id == assignment_id
        ).delete()
        db.flush()  # Ensure deletion is committed before inserting new records
        
        # Get template to extract skill information
        template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        print(f"DEBUG: Found template: {template.template_name}")
        
        # Parse template content to get skill names
        content = json.loads(template.content)
        skill_id_to_name = {}
        for i, row in enumerate(content):
            if not row or len(row) == 0:
                continue
            skill_name = str(row[0]).strip() if row[0] else ""
            if not skill_name or skill_name.lower() in ['skill', 'name', ''] or skill_name.startswith('1.') or skill_name.startswith('2.') or skill_name.startswith('3.') or skill_name.startswith('4.'):
                continue
            # Extract skill name (before colon)
            if ':' in skill_name:
                skill_name = skill_name.split(':', 1)[0].strip()
            skill_id_to_name[1000 + i] = skill_name
        
        print(f"DEBUG: Parsed {len(skill_id_to_name)} skills from template")
        
        # Save employee responses and track skill ID mapping
        template_id_to_db_id = {}  # Map template skill IDs to database skill IDs
        for response in submission.responses:
            # Get or create skill record
            skill_name = skill_id_to_name.get(response.skill_id, f"Template Skill {response.skill_id}")
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if not skill:
                # Create skill record for template skill
                skill = Skill(
                    name=skill_name,
                    category="Template Skills",
                    description=f"Skill from template: {template.template_name}"
                )
                db.add(skill)
                db.flush()  # Get the skill ID
            
            # Track the mapping
            template_id_to_db_id[response.skill_id] = skill.id
            
            db_response = EmployeeTemplateResponse(
                assignment_id=assignment_id,
                employee_category=submission.employee_category,
                skill_id=skill.id,
                employee_level=response.level,
                years_experience=response.years_experience or 0,
                notes=response.notes
            )
            db.add(db_response)
        
        # Update assignment status
        assignment.status = "Completed"
        
        db.commit()
        
        print(f"DEBUG: Assignment status updated to Completed")
        
        # ============================================================
        # AUTO-IMPORT SKILLS TO EMPLOYEE_SKILLS TABLE
        # ============================================================
        print(f"DEBUG: Starting auto-import of skills to employee_skills")
        
        # Get all responses for this assignment
        template_responses = db.query(EmployeeTemplateResponse).filter(
            EmployeeTemplateResponse.assignment_id == assignment_id
        ).all()
        
        print(f"DEBUG: Found {len(template_responses)} skills to import")
        
        imported_count = 0
        updated_count = 0
        
        for response in template_responses:
            # Check if skill already exists for this employee
            existing_skill = db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee.id,
                EmployeeSkill.skill_id == response.skill_id
            ).first()
            
            if existing_skill:
                # Update existing skill with latest level (if level was provided)
                if response.employee_level:
                    # Only update rating if employee selected a level
                    existing_skill.rating = response.employee_level
                    existing_skill.years_experience = response.years_experience or existing_skill.years_experience
                    if response.notes:
                        existing_skill.notes = response.notes
                    print(f"DEBUG: Updated existing skill '{response.skill.name}' to level {response.employee_level}")
                    updated_count += 1
                else:
                    # Employee didn't select a level, but skill exists - don't overwrite
                    print(f"DEBUG: Skipped updating '{response.skill.name}' - no level provided and skill exists")
            else:
                # Create new employee_skill entry
                # Note: rating can be None if employee didn't select a level
                new_employee_skill = EmployeeSkill(
                    employee_id=employee.id,
                    skill_id=response.skill_id,
                    rating=response.employee_level,  # Can be None
                    initial_rating=response.employee_level,  # Track initial for improvements
                    years_experience=response.years_experience or 0,
                    notes=response.notes,
                    is_interested=False,  # From template, not interested
                    is_custom=False  # From template, not custom
                )
                db.add(new_employee_skill)
                level_str = response.employee_level if response.employee_level else "no level"
                print(f"DEBUG: Created new skill '{response.skill.name}' with {level_str}")
                imported_count += 1
        
        # Commit the imported skills
        db.commit()
        
        print(f"DEBUG: Auto-import completed - {imported_count} new skills, {updated_count} updated")
        
        # ============================================================
        # END AUTO-IMPORT
        # ============================================================
        
        # Automatic gap calculation
        # Delete existing gap results
        db.query(SkillGapResult).filter(SkillGapResult.assignment_id == assignment_id).delete()
        
        gaps_found = 0
        for response in submission.responses:
            # Default required level (in production, parse from template)
            required_level = "Intermediate"
            
            gap_status, gap_value = calculate_gap(required_level, response.level)
            
            # Use the database skill ID, not the template ID
            db_skill_id = template_id_to_db_id.get(response.skill_id)
            if not db_skill_id:
                print(f"WARNING: No database skill ID found for template skill {response.skill_id}")
                continue
            
            gap_result = SkillGapResult(
                assignment_id=assignment_id,
                skill_id=db_skill_id,  # Use database skill ID
                required_level=required_level,
                employee_level=response.level,
                gap_status=gap_status,
                gap_value=gap_value
            )
            db.add(gap_result)
            
            if gap_status == "Gap":
                gaps_found += 1
        
        db.commit()
        
        print(f"DEBUG: Calculated {gaps_found} gaps")
        
        return {
            "message": "Template submitted successfully",
            "assignment_id": assignment_id,
            "status": "Completed",
            "gaps_detected": gaps_found
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in submit_template: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


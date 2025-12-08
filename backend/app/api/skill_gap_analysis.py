"""API routes for skill gap analysis and calculation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from app.db import database
from app.db.models import (
    TemplateAssignment, Employee, SkillTemplate, User,
    EmployeeTemplateResponse, SkillGapResult, Skill
)
from app.api.dependencies import get_admin_user

router = APIRouter(prefix="/api/admin/skill-gaps", tags=["skill-gap-analysis"])


# Skill level mapping for comparison
LEVEL_MAPPING = {
    "Beginner": 1,
    "Developing": 2,
    "Intermediate": 3,
    "Advanced": 4,
    "Expert": 5
}


def calculate_gap(required_level: str, employee_level: Optional[str]) -> tuple[str, int]:
    """
    Calculate skill gap between required and employee level.
    Returns (gap_status, gap_value)
    gap_value: negative = gap, 0 = met, positive = exceeded
    """
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
class GapCalculationResult(BaseModel):
    assignment_id: int
    total_skills: int
    gaps_found: int
    gaps_met: int
    gaps_exceeded: int


class SkillGapDetail(BaseModel):
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    required_level: str
    employee_level: Optional[str]
    gap_status: str
    gap_value: int


class EmployeeWithGaps(BaseModel):
    assignment_id: int
    employee_id: int
    employee_name: str
    template_id: int
    template_name: str
    category_hr: Optional[str]
    employee_category: Optional[str]
    total_gaps: int
    submitted_at: datetime


class EmployeeWithoutGaps(BaseModel):
    assignment_id: int
    employee_id: int
    employee_name: str
    template_id: int
    template_name: str
    category_hr: Optional[str]
    employee_category: Optional[str]
    submitted_at: datetime


class GapDetailsResponse(BaseModel):
    assignment_id: int
    employee_id: int
    employee_name: str
    template_id: int
    template_name: str
    category_hr: Optional[str]
    employee_category: Optional[str]
    gaps: List[SkillGapDetail]


@router.post("/calculate/{assignment_id}", response_model=GapCalculationResult)
async def calculate_gaps(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Calculate skill gaps for a completed assignment.
    Compares employee responses against template requirements.
    """
    # Get assignment
    assignment = db.query(TemplateAssignment).filter(TemplateAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status != "Completed":
        raise HTTPException(status_code=400, detail="Assignment not completed yet")
    
    # Get employee responses
    responses = db.query(EmployeeTemplateResponse).filter(
        EmployeeTemplateResponse.assignment_id == assignment_id
    ).all()
    
    if not responses:
        raise HTTPException(status_code=400, detail="No employee responses found")
    
    # Get template to extract required levels
    # For now, we'll use a simplified approach - assume template has required levels
    # In a real implementation, you'd parse the template content
    
    # Delete existing gap results
    db.query(SkillGapResult).filter(SkillGapResult.assignment_id == assignment_id).delete()
    
    gaps_found = 0
    gaps_met = 0
    gaps_exceeded = 0
    
    # Calculate gaps for each skill
    for response in responses:
        # For this implementation, we'll assume a default required level
        # In production, this should come from the template content
        required_level = "Intermediate"  # Default requirement
        
        gap_status, gap_value = calculate_gap(required_level, response.employee_level)
        
        # Create gap result
        gap_result = SkillGapResult(
            assignment_id=assignment_id,
            skill_id=response.skill_id,
            required_level=required_level,
            employee_level=response.employee_level,
            gap_status=gap_status,
            gap_value=gap_value
        )
        db.add(gap_result)
        
        if gap_status == "Gap":
            gaps_found += 1
        elif gap_status == "Met":
            gaps_met += 1
        else:
            gaps_exceeded += 1
    
    db.commit()
    
    return GapCalculationResult(
        assignment_id=assignment_id,
        total_skills=len(responses),
        gaps_found=gaps_found,
        gaps_met=gaps_met,
        gaps_exceeded=gaps_exceeded
    )


@router.get("/with-gaps", response_model=List[EmployeeWithGaps])
async def get_employees_with_gaps(
    template_id: Optional[int] = None,
    category: Optional[str] = None,
    min_gaps: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get list of employees who have skill gaps.
    """
    print(f"DEBUG: get_employees_with_gaps called - template_id={template_id}, category={category}, min_gaps={min_gaps}")
    
    # Get all completed assignments
    query = db.query(TemplateAssignment).filter(TemplateAssignment.status == "Completed")
    
    if template_id:
        query = query.filter(TemplateAssignment.template_id == template_id)
    if category:
        query = query.filter(TemplateAssignment.category_hr == category)
    
    assignments = query.all()
    print(f"DEBUG: Found {len(assignments)} completed assignments")
    
    result = []
    for assignment in assignments:
        # Count gaps for this assignment
        gaps_count = db.query(SkillGapResult).filter(
            SkillGapResult.assignment_id == assignment.id,
            SkillGapResult.gap_status == "Gap"
        ).count()
        
        print(f"DEBUG: Assignment {assignment.id} has {gaps_count} gaps")
        
        if gaps_count > 0:
            if min_gaps and gaps_count < min_gaps:
                continue
            
            employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
            template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
            
            # Get employee category from responses
            response = db.query(EmployeeTemplateResponse).filter(
                EmployeeTemplateResponse.assignment_id == assignment.id
            ).first()
            
            result.append(EmployeeWithGaps(
                assignment_id=assignment.id,
                employee_id=assignment.employee_id,
                employee_name=employee.name if employee else "Unknown",
                template_id=assignment.template_id,
                template_name=template.template_name if template else "Unknown",
                category_hr=assignment.category_hr,
                employee_category=response.employee_category if response else None,
                total_gaps=gaps_count,
                submitted_at=assignment.assigned_at
            ))
    
    print(f"DEBUG: Returning {len(result)} employees with gaps")
    return result


@router.get("/without-gaps", response_model=List[EmployeeWithoutGaps])
async def get_employees_without_gaps(
    template_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get list of employees who have NO skill gaps.
    """
    # Get all completed assignments
    query = db.query(TemplateAssignment).filter(TemplateAssignment.status == "Completed")
    
    if template_id:
        query = query.filter(TemplateAssignment.template_id == template_id)
    if category:
        query = query.filter(TemplateAssignment.category_hr == category)
    
    assignments = query.all()
    
    result = []
    for assignment in assignments:
        # Count gaps for this assignment
        gaps_count = db.query(SkillGapResult).filter(
            SkillGapResult.assignment_id == assignment.id,
            SkillGapResult.gap_status == "Gap"
        ).count()
        
        if gaps_count == 0:
            employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
            template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
            
            # Get employee category from responses
            response = db.query(EmployeeTemplateResponse).filter(
                EmployeeTemplateResponse.assignment_id == assignment.id
            ).first()
            
            result.append(EmployeeWithoutGaps(
                assignment_id=assignment.id,
                employee_id=assignment.employee_id,
                employee_name=employee.name if employee else "Unknown",
                template_id=assignment.template_id,
                template_name=template.template_name if template else "Unknown",
                category_hr=assignment.category_hr,
                employee_category=response.employee_category if response else None,
                submitted_at=assignment.assigned_at
            ))
    
    return result


@router.get("/{assignment_id}/details", response_model=GapDetailsResponse)
async def get_gap_details(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get detailed skill gap report for a specific assignment.
    """
    assignment = db.query(TemplateAssignment).filter(TemplateAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
    
    # Get employee category
    response = db.query(EmployeeTemplateResponse).filter(
        EmployeeTemplateResponse.assignment_id == assignment_id
    ).first()
    
    # Get all gap results
    gap_results = db.query(SkillGapResult).filter(
        SkillGapResult.assignment_id == assignment_id
    ).all()
    
    gaps = []
    for gap in gap_results:
        skill = db.query(Skill).filter(Skill.id == gap.skill_id).first()
        gaps.append(SkillGapDetail(
            skill_id=gap.skill_id,
            skill_name=skill.name if skill else "Unknown",
            skill_category=skill.category if skill else None,
            required_level=gap.required_level,
            employee_level=gap.employee_level,
            gap_status=gap.gap_status,
            gap_value=gap.gap_value
        ))
    
    return GapDetailsResponse(
        assignment_id=assignment.id,
        employee_id=assignment.employee_id,
        employee_name=employee.name if employee else "Unknown",
        template_id=assignment.template_id,
        template_name=template.template_name if template else "Unknown",
        category_hr=assignment.category_hr,
        employee_category=response.employee_category if response else None,
        gaps=gaps
    )

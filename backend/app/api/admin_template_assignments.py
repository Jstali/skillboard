"""API routes for HR/Admin template assignment to employees."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db import database
from app.db.models import TemplateAssignment, Employee, SkillTemplate, User
from app.api.dependencies import get_admin_user

router = APIRouter(prefix="/api/admin/template-assignments", tags=["admin-template-assignments"])


# Pydantic Schemas
class TemplateAssignmentCreate(BaseModel):
    employee_id: int
    template_id: int
    category_hr: str


class TemplateAssignmentResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    template_id: int
    template_name: str
    category_hr: Optional[str]
    status: str
    assigned_at: datetime
    assigned_by: Optional[int]

    class Config:
        from_attributes = True


@router.post("", response_model=TemplateAssignmentResponse)
async def assign_template(
    assignment: TemplateAssignmentCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Assign a skill template to an employee with HR-selected category.
    The category_hr is hidden from the employee.
    """
    # Validate employee exists
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate template exists
    template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if assignment already exists
    existing = db.query(TemplateAssignment).filter(
        TemplateAssignment.employee_id == assignment.employee_id,
        TemplateAssignment.template_id == assignment.template_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Template '{template.template_name}' is already assigned to {employee.name}"
        )
    
    # Create assignment
    db_assignment = TemplateAssignment(
        employee_id=assignment.employee_id,
        template_id=assignment.template_id,
        category_hr=assignment.category_hr,
        assigned_by=current_user.id,
        status="Pending"
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    return TemplateAssignmentResponse(
        id=db_assignment.id,
        employee_id=db_assignment.employee_id,
        employee_name=employee.name,
        template_id=db_assignment.template_id,
        template_name=template.template_name,
        category_hr=db_assignment.category_hr,
        status=db_assignment.status,
        assigned_at=db_assignment.assigned_at,
        assigned_by=db_assignment.assigned_by
    )


@router.get("", response_model=List[TemplateAssignmentResponse])
async def list_assignments(
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    template_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    List all template assignments with optional filters.
    """
    query = db.query(TemplateAssignment)
    
    if status:
        query = query.filter(TemplateAssignment.status == status)
    if employee_id:
        query = query.filter(TemplateAssignment.employee_id == employee_id)
    if template_id:
        query = query.filter(TemplateAssignment.template_id == template_id)
    
    assignments = query.order_by(TemplateAssignment.assigned_at.desc()).all()
    
    result = []
    for assignment in assignments:
        employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
        template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
        
        result.append(TemplateAssignmentResponse(
            id=assignment.id,
            employee_id=assignment.employee_id,
            employee_name=employee.name if employee else "Unknown",
            template_id=assignment.template_id,
            template_name=template.template_name if template else "Unknown",
            category_hr=assignment.category_hr,
            status=assignment.status,
            assigned_at=assignment.assigned_at,
            assigned_by=assignment.assigned_by
        ))
    
    return result


@router.get("/{assignment_id}", response_model=TemplateAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get details of a specific template assignment.
    """
    assignment = db.query(TemplateAssignment).filter(TemplateAssignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    template = db.query(SkillTemplate).filter(SkillTemplate.id == assignment.template_id).first()
    
    return TemplateAssignmentResponse(
        id=assignment.id,
        employee_id=assignment.employee_id,
        employee_name=employee.name if employee else "Unknown",
        template_id=assignment.template_id,
        template_name=template.template_name if template else "Unknown",
        category_hr=assignment.category_hr,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by
    )


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a template assignment (only if status is Pending).
    """
    assignment = db.query(TemplateAssignment).filter(TemplateAssignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete assignment that has been started or completed"
        )
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Assignment deleted successfully"}

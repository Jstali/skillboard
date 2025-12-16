"""API endpoints for Skill Board views.

Provides endpoints for employee skill boards, capability alignment,
and skill gap analysis with role-based access control.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.db.models import User, Employee
from app.services.skill_board import (
    SkillBoardService, EmployeeSkillBoard, SkillWithProficiency,
    SkillGap, CapabilityAlignment, get_skill_board_service
)
from app.services.financial_filter import financial_filter
from app.api.dependencies import get_current_user
from app.core.permissions import RoleID

router = APIRouter(prefix="/api/skill-board", tags=["Skill Board"])


def _can_view_employee(current_user: User, employee_id: str, db: Session) -> bool:
    """Check if current user can view the specified employee's data."""
    # Admins and HR can view all
    if current_user.is_admin or current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        return True
    
    # Employees can view their own data
    if current_user.employee_id == employee_id:
        return True
    
    # CPs can view employees in their capability
    if current_user.role_id == RoleID.CAPABILITY_PARTNER:
        # Get current user's employee record
        user_emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
        target_emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if user_emp and target_emp:
            if user_emp.home_capability == target_emp.home_capability:
                return True
    
    # Managers can view their team members
    if current_user.role_id in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
        target_emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if target_emp and target_emp.line_manager_id:
            user_emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
            if user_emp and str(target_emp.line_manager_id) == str(user_emp.id):
                return True
    
    return False


@router.get("/{employee_id}", response_model=EmployeeSkillBoard)
async def get_employee_skill_board(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete skill board for an employee.
    
    Returns all skills, proficiency levels, capability alignment,
    and skill gaps for the specified employee.
    
    Access control:
    - Employees can view their own data
    - CPs can view employees in their capability
    - Managers can view their team members
    - HR and Admins can view all
    """
    if not _can_view_employee(current_user, employee_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's skill board"
        )
    
    service = get_skill_board_service(db)
    skill_board = service.get_employee_skill_board(employee_id)
    
    if not skill_board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )
    
    return skill_board


@router.get("/{employee_id}/skills", response_model=List[SkillWithProficiency])
async def get_employee_skills(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all skills for an employee with proficiency information.
    """
    if not _can_view_employee(current_user, employee_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's skills"
        )
    
    service = get_skill_board_service(db)
    skills = service.get_employee_skills(employee_id)
    
    if not skills:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No skills found for employee {employee_id}"
        )
    
    return skills


@router.get("/{employee_id}/gaps", response_model=List[SkillGap])
async def get_employee_skill_gaps(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill gaps for an employee.
    
    Returns skills where proficiency is below requirements.
    """
    if not _can_view_employee(current_user, employee_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's skill gaps"
        )
    
    service = get_skill_board_service(db)
    gaps = service.get_skill_gaps(employee_id)
    
    return gaps


@router.get("/{employee_id}/alignment", response_model=Optional[CapabilityAlignment])
async def get_employee_alignment(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get capability alignment for an employee.
    
    Returns alignment score and details for the employee's capability.
    """
    if not _can_view_employee(current_user, employee_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's alignment"
        )
    
    service = get_skill_board_service(db)
    alignment = service.get_capability_alignment(employee_id)
    
    return alignment

"""API routes for Project Assignment Management.

Provides endpoints for managing employee-project relationships,
viewing assignments, and reconciliation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db import database
from app.db.models import (
    User, Employee, EmployeeProjectAssignment, Project
)
from app.api.dependencies import get_current_active_user, get_admin_user
from app.services.project_assignment import (
    ProjectAssignmentService, AssignmentCreate, AllocationError
)
from app.services.access_control import (
    PermissionEngine, UserRole, Permission, get_permission_engine
)

router = APIRouter(prefix="/api/assignments", tags=["project-assignments"])


class AssignmentResponse(BaseModel):
    """Response model for project assignment."""
    id: int
    employee_id: int
    project_id: int
    project_name: Optional[str] = None
    is_primary: bool
    percentage_allocation: Optional[int] = None
    line_manager_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AssignmentCreateRequest(BaseModel):
    """Request model for creating assignment."""
    employee_id: int
    project_id: int
    is_primary: bool = False
    percentage_allocation: Optional[int] = None
    line_manager_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ConflictResponse(BaseModel):
    """Response model for assignment conflict."""
    employee_id: int
    conflict_type: str
    details: str
    affected_projects: List[int]


# Employee endpoints - view own assignments
@router.get("/my-assignments", response_model=List[AssignmentResponse])
async def get_my_assignments(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's project assignments."""
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record linked to user"
        )
    
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    assignments = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.employee_id == employee.id
    ).all()
    
    result = []
    for a in assignments:
        project = db.query(Project).filter(Project.id == a.project_id).first()
        result.append(AssignmentResponse(
            id=a.id,
            employee_id=a.employee_id,
            project_id=a.project_id,
            project_name=project.name if project else None,
            is_primary=a.is_primary,
            percentage_allocation=a.percentage_allocation,
            line_manager_id=a.line_manager_id,
            start_date=a.start_date,
            end_date=a.end_date
        ))
    
    return result


@router.get("/employee/{employee_id}", response_model=List[AssignmentResponse])
async def get_employee_assignments(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get assignments for a specific employee (with access control)."""
    permission_engine = get_permission_engine(db)
    
    has_access, reason = permission_engine.check_access(
        user_id=current_user.id,
        resource_type="Assignment",
        resource_id=str(employee_id),
        action="view"
    )
    
    # Check if user can view this employee's data
    accessible_employees = permission_engine.get_accessible_employees(current_user.id)
    if employee_id not in accessible_employees and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this employee's assignments"
        )
    
    assignments = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.employee_id == employee_id
    ).all()
    
    result = []
    for a in assignments:
        project = db.query(Project).filter(Project.id == a.project_id).first()
        result.append(AssignmentResponse(
            id=a.id,
            employee_id=a.employee_id,
            project_id=a.project_id,
            project_name=project.name if project else None,
            is_primary=a.is_primary,
            percentage_allocation=a.percentage_allocation,
            line_manager_id=a.line_manager_id,
            start_date=a.start_date,
            end_date=a.end_date
        ))
    
    return result


# HR endpoints - manage assignments
@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    request: AssignmentCreateRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new project assignment (HR/Admin only)."""
    service = ProjectAssignmentService(db)
    
    try:
        assignment = service.create_assignment(AssignmentCreate(
            employee_id=request.employee_id,
            project_id=request.project_id,
            is_primary=request.is_primary,
            percentage_allocation=request.percentage_allocation,
            line_manager_id=request.line_manager_id,
            start_date=request.start_date,
            end_date=request.end_date
        ))
        
        project = db.query(Project).filter(Project.id == assignment.project_id).first()
        
        return AssignmentResponse(
            id=assignment.id,
            employee_id=assignment.employee_id,
            project_id=assignment.project_id,
            project_name=project.name if project else None,
            is_primary=assignment.is_primary,
            percentage_allocation=assignment.percentage_allocation,
            line_manager_id=assignment.line_manager_id,
            start_date=assignment.start_date,
            end_date=assignment.end_date
        )
    except AllocationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/conflicts/{employee_id}", response_model=List[ConflictResponse])
async def get_assignment_conflicts(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get assignment conflicts for an employee (HR/Admin only)."""
    service = ProjectAssignmentService(db)
    
    conflicts = service.detect_conflicts(employee_id)
    
    return [
        ConflictResponse(
            employee_id=c.employee_id,
            conflict_type=c.conflict_type,
            details=c.details,
            affected_projects=c.affected_projects
        )
        for c in conflicts
    ]


@router.get("/all", response_model=List[AssignmentResponse])
async def get_all_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all project assignments (HR/Admin only)."""
    assignments = db.query(EmployeeProjectAssignment).offset(skip).limit(limit).all()
    
    result = []
    for a in assignments:
        project = db.query(Project).filter(Project.id == a.project_id).first()
        result.append(AssignmentResponse(
            id=a.id,
            employee_id=a.employee_id,
            project_id=a.project_id,
            project_name=project.name if project else None,
            is_primary=a.is_primary,
            percentage_allocation=a.percentage_allocation,
            line_manager_id=a.line_manager_id,
            start_date=a.start_date,
            end_date=a.end_date
        ))
    
    return result


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a project assignment (HR/Admin only)."""
    assignment = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db.delete(assignment)
    db.commit()
    
    return {"status": "deleted", "id": assignment_id}

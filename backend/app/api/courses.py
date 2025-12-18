"""API endpoints for Course Assignment by Managers.

Provides endpoints for:
- Listing courses with filtering
- Assigning courses to employees
- Managing course assignments
- Tracking course completion status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, Employee, CourseAssignment
from app.api.dependencies import get_current_user, get_current_active_user
from app.services.course_assignment import (
    CourseAssignmentService, get_course_assignment_service,
    CourseWithDetails, CourseAssignmentWithDetails
)
from app.services.authority_validator import AuthorityValidator, get_authority_validator
from app.core.permissions import RoleID

router = APIRouter(prefix="/api/courses", tags=["Course Assignment"])


# Request/Response Models
class CourseAssignRequest(BaseModel):
    """Request body for assigning a course."""
    course_id: int
    employee_id: int
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    skill_id: Optional[int] = None  # For gap analysis linkage


class CourseAssignmentResponse(BaseModel):
    """Response for a course assignment."""
    id: int
    course_id: int
    course_title: str
    course_description: Optional[str]
    course_url: Optional[str]
    employee_id: int
    employee_name: str
    assigned_by: Optional[int]
    assigner_name: Optional[str]
    assigned_at: datetime
    due_date: Optional[datetime]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    certificate_url: Optional[str]
    notes: Optional[str]
    skill_id: Optional[int]
    skill_name: Optional[str]
    
    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    """Request body for updating assignment status."""
    status: str  # NOT_STARTED, IN_PROGRESS, COMPLETED
    certificate_url: Optional[str] = None


def _get_manager_employee_id(user: User, db: Session) -> int:
    """Get the employee ID for the current user (manager)."""
    if not user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to an employee record"
        )
    
    emp = db.query(Employee).filter(Employee.employee_id == user.employee_id).first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found for user"
        )
    
    return emp.id


def _validate_manager_role(user: User):
    """Validate that user has manager role."""
    if user.role_id not in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Line Managers and Delivery Managers can assign courses"
        )


# ============================================================================
# Course Listing Endpoints
# ============================================================================

@router.get("", response_model=List[CourseWithDetails])
async def get_courses(
    skill_id: Optional[int] = None,
    mandatory: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all courses with optional filtering.
    
    Query Parameters:
    - skill_id: Filter by skill ID
    - mandatory: Filter by mandatory status (true/false)
    - search: Search term for title/description
    
    Requirements: 2.1, 2.2, 2.4
    """
    service = get_course_assignment_service(db)
    return service.get_all_courses(
        skill_id=skill_id,
        is_mandatory=mandatory,
        search=search
    )


@router.get("/skill/{skill_id}", response_model=List[CourseWithDetails])
async def get_courses_for_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get courses for a specific skill.
    
    Returns all courses associated with the given skill ID.
    
    Requirements: 2.1, 4.2
    """
    service = get_course_assignment_service(db)
    return service.get_courses_for_skill(skill_id)


# ============================================================================
# Course Assignment Endpoints
# ============================================================================

@router.post("/assign", response_model=CourseAssignmentResponse)
async def assign_course(
    request: CourseAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a course to an employee.
    
    Only Line Managers and Delivery Managers can assign courses.
    Manager must have authority over the target employee.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    """
    _validate_manager_role(current_user)
    
    manager_emp_id = _get_manager_employee_id(current_user, db)
    
    service = get_course_assignment_service(db)
    
    try:
        assignment = service.assign_course(
            course_id=request.course_id,
            employee_id=request.employee_id,
            assigned_by=manager_emp_id,
            assigned_by_role_id=current_user.role_id,
            due_date=request.due_date,
            notes=request.notes,
            skill_id=request.skill_id
        )
        
        # Get full details for response
        assignments = service.get_manager_assignments(manager_emp_id)
        for a in assignments:
            if a.id == assignment.id:
                return a
        
        # Fallback - return basic info
        return CourseAssignmentResponse(
            id=assignment.id,
            course_id=assignment.course_id,
            course_title="",
            course_description=None,
            course_url=None,
            employee_id=assignment.employee_id,
            employee_name="",
            assigned_by=assignment.assigned_by,
            assigner_name=None,
            assigned_at=assignment.assigned_at,
            due_date=assignment.due_date,
            status=assignment.status.value,
            started_at=assignment.started_at,
            completed_at=assignment.completed_at,
            certificate_url=assignment.certificate_url,
            notes=assignment.notes,
            skill_id=assignment.skill_id,
            skill_name=None
        )
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        error_msg = str(e)
        if "already assigned" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )


@router.get("/assignments/manager", response_model=List[CourseAssignmentResponse])
async def get_manager_assignments(
    status_filter: Optional[str] = None,
    employee_id: Optional[int] = None,
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all course assignments made by the current manager.
    
    Query Parameters:
    - status_filter: Filter by status (Not Started, In Progress, Completed)
    - employee_id: Filter by employee
    - course_id: Filter by course
    
    Only available to Line Managers and Delivery Managers.
    
    Requirements: 5.1, 5.2, 5.3
    """
    _validate_manager_role(current_user)
    
    manager_emp_id = _get_manager_employee_id(current_user, db)
    
    service = get_course_assignment_service(db)
    assignments = service.get_manager_assignments(
        manager_id=manager_emp_id,
        status_filter=status_filter,
        employee_id=employee_id,
        course_id=course_id
    )
    
    return [
        CourseAssignmentResponse(
            id=a.id,
            course_id=a.course_id,
            course_title=a.course_title,
            course_description=a.course_description,
            course_url=a.course_url,
            employee_id=a.employee_id,
            employee_name=a.employee_name,
            assigned_by=a.assigned_by,
            assigner_name=a.assigner_name,
            assigned_at=a.assigned_at,
            due_date=a.due_date,
            status=a.status,
            started_at=a.started_at,
            completed_at=a.completed_at,
            certificate_url=a.certificate_url,
            notes=a.notes,
            skill_id=a.skill_id,
            skill_name=a.skill_name
        )
        for a in assignments
    ]


@router.get("/assignments/me", response_model=List[CourseAssignmentResponse])
async def get_my_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get courses assigned to the current user.
    
    Returns all course assignments for the current employee.
    
    Requirements: 6.1, 6.2
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to an employee record"
        )
    
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    service = get_course_assignment_service(db)
    assignments = service.get_employee_assignments(employee.id)
    
    return [
        CourseAssignmentResponse(
            id=a.id,
            course_id=a.course_id,
            course_title=a.course_title,
            course_description=a.course_description,
            course_url=a.course_url,
            employee_id=a.employee_id,
            employee_name=a.employee_name,
            assigned_by=a.assigned_by,
            assigner_name=a.assigner_name,
            assigned_at=a.assigned_at,
            due_date=a.due_date,
            status=a.status,
            started_at=a.started_at,
            completed_at=a.completed_at,
            certificate_url=a.certificate_url,
            notes=a.notes,
            skill_id=a.skill_id,
            skill_name=a.skill_name
        )
        for a in assignments
    ]


@router.put("/assignments/{assignment_id}/status", response_model=CourseAssignmentResponse)
async def update_assignment_status(
    assignment_id: int,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update course assignment status.
    
    Valid transitions:
    - NOT_STARTED -> IN_PROGRESS
    - IN_PROGRESS -> COMPLETED
    
    User can update their own assignments.
    Managers can update assignments they made.
    
    Requirements: 6.3, 6.4
    """
    # Get the assignment
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with ID {assignment_id} not found"
        )
    
    # Check authorization
    is_own_assignment = False
    is_manager_assignment = False
    
    if current_user.employee_id:
        employee = db.query(Employee).filter(
            Employee.employee_id == current_user.employee_id
        ).first()
        
        if employee:
            # Check if it's the employee's own assignment
            is_own_assignment = assignment.employee_id == employee.id
            
            # Check if current user is the manager who assigned it
            is_manager_assignment = assignment.assigned_by == employee.id
    
    if not (is_own_assignment or is_manager_assignment):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own assignments or assignments you made"
        )
    
    service = get_course_assignment_service(db)
    
    try:
        updated = service.update_assignment_status(
            assignment_id=assignment_id,
            new_status=request.status,
            certificate_url=request.certificate_url
        )
        
        # Get full details for response
        if is_own_assignment:
            employee = db.query(Employee).filter(
                Employee.employee_id == current_user.employee_id
            ).first()
            assignments = service.get_employee_assignments(employee.id)
        else:
            manager_emp_id = _get_manager_employee_id(current_user, db)
            assignments = service.get_manager_assignments(manager_emp_id)
        
        for a in assignments:
            if a.id == assignment_id:
                return CourseAssignmentResponse(
                    id=a.id,
                    course_id=a.course_id,
                    course_title=a.course_title,
                    course_description=a.course_description,
                    course_url=a.course_url,
                    employee_id=a.employee_id,
                    employee_name=a.employee_name,
                    assigned_by=a.assigned_by,
                    assigner_name=a.assigner_name,
                    assigned_at=a.assigned_at,
                    due_date=a.due_date,
                    status=a.status,
                    started_at=a.started_at,
                    completed_at=a.completed_at,
                    certificate_url=a.certificate_url,
                    notes=a.notes,
                    skill_id=a.skill_id,
                    skill_name=a.skill_name
                )
        
        # Fallback
        return CourseAssignmentResponse(
            id=updated.id,
            course_id=updated.course_id,
            course_title="",
            course_description=None,
            course_url=None,
            employee_id=updated.employee_id,
            employee_name="",
            assigned_by=updated.assigned_by,
            assigner_name=None,
            assigned_at=updated.assigned_at,
            due_date=updated.due_date,
            status=updated.status.value,
            started_at=updated.started_at,
            completed_at=updated.completed_at,
            certificate_url=updated.certificate_url,
            notes=updated.notes,
            skill_id=updated.skill_id,
            skill_name=None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

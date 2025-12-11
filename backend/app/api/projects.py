"""
Project Management API endpoints for HRMS pre-integration.
Handles projects and employee-project assignments.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import database
from app.db.models import Project, EmployeeProjectAssignment, Employee, User
from app.schemas import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    EmployeeProjectAssignment as EmployeeProjectAssignmentSchema,
    EmployeeProjectAssignmentCreate,
    EmployeeProjectAssignmentUpdate
)
from app.api.rbac import require_role, require_hr, get_user_role
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectSchema)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Create a new project.
    Requires: HR or System Admin role
    """
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("", response_model=List[ProjectSchema])
async def list_projects(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all projects.
    Access filtered by role:
    - System Admin, HR: All projects
    - Delivery Manager: Projects they manage
    - Others: Projects they're assigned to
    """
    role_name = get_user_role(current_user, db)
    
    if role_name in ["System Admin", "HR"]:
        # Return all projects
        projects = db.query(Project).all()
    else:
        # Return projects user is assigned to
        employee = db.query(Employee).filter(
            Employee.employee_id == current_user.employee_id
        ).first()
        
        if not employee:
            return []
        
        # Get projects through assignments
        assignments = db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == employee.id
        ).all()
        
        project_ids = [a.project_id for a in assignments]
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Update project details.
    Requires: HR or System Admin role
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin"))
):
    """
    Delete a project.
    Requires: System Admin role
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


# ============================================================================
# EMPLOYEE PROJECT ASSIGNMENTS
# ============================================================================

@router.post("/{project_id}/assign-employee", response_model=EmployeeProjectAssignmentSchema)
async def assign_employee_to_project(
    project_id: int,
    assignment: EmployeeProjectAssignmentCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR", "Delivery Manager"))
):
    """
    Assign an employee to a project.
    Requires: System Admin, HR, or Delivery Manager role
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if assignment already exists
    existing = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.employee_id == assignment.employee_id,
        EmployeeProjectAssignment.project_id == project_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Employee already assigned to this project")
    
    # If this is primary, unset other primary assignments for this employee
    if assignment.is_primary:
        db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == assignment.employee_id,
            EmployeeProjectAssignment.is_primary == True
        ).update({"is_primary": False})
    
    # Create assignment
    db_assignment = EmployeeProjectAssignment(**assignment.dict())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.get("/employee/{employee_id}/projects", response_model=List[EmployeeProjectAssignmentSchema])
async def get_employee_projects(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects for an employee.
    Access controlled by RBAC.
    """
    # Check if user can view this employee's data
    from app.api.rbac import can_view_employee
    can_view_employee(employee_id, current_user, db)
    
    assignments = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.employee_id == employee_id
    ).all()
    
    return assignments


@router.put("/assignments/{assignment_id}", response_model=EmployeeProjectAssignmentSchema)
async def update_project_assignment(
    assignment_id: int,
    assignment_update: EmployeeProjectAssignmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR", "Delivery Manager"))
):
    """
    Update an employee's project assignment.
    Requires: System Admin, HR, or Delivery Manager role
    """
    assignment = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # If setting as primary, unset other primary assignments
    if assignment_update.is_primary:
        db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == assignment.employee_id,
            EmployeeProjectAssignment.is_primary == True,
            EmployeeProjectAssignment.id != assignment_id
        ).update({"is_primary": False})
    
    # Update fields
    for field, value in assignment_update.dict(exclude_unset=True).items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}")
async def delete_project_assignment(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR", "Delivery Manager"))
):
    """
    Remove an employee from a project.
    Requires: System Admin, HR, or Delivery Manager role
    """
    assignment = db.query(EmployeeProjectAssignment).filter(
        EmployeeProjectAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully"}

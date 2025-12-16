"""
Level Movement Workflow API endpoints for HRMS pre-integration.
Handles promotion requests and multi-stage approval workflow.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import database
from app.db.models import (
    LevelMovementRequest,
    LevelMovementApprovalAudit,
    Employee,
    User,
    EmployeeSkill,
    RoleRequirement
)
from app.schemas import (
    LevelMovementRequest as LevelMovementRequestSchema,
    LevelMovementRequestCreate,
    LevelMovementApprovalAudit as LevelMovementApprovalAuditSchema,
    ApprovalRequest
)
from app.api.rbac import require_role, get_user_role
from app.api.dependencies import get_current_user
from app.services.audit_logger import AuditLogger


router = APIRouter(prefix="/api/level-movement", tags=["level-movement"])


def calculate_readiness_score(employee_id: int, target_level: str, db: Session) -> float:
    """
    Calculate readiness score for level movement.
    
    Formula:
    - Skill gaps: 70% weight
    - Certifications: 20% weight (placeholder for now)
    - Experience: 10% weight (placeholder for HRMS data)
    
    Returns:
        Readiness score from 0-100
    """
    # Get employee's skills
    employee_skills = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == employee_id
    ).all()
    
    # Get required skills for target level
    role_requirements = db.query(RoleRequirement).filter(
        RoleRequirement.band == target_level
    ).all()
    
    if not role_requirements:
        # No requirements defined for this level
        return 100.0
    
    # Map rating levels to numeric values
    rating_values = {
        "Beginner": 1,
        "Developing": 2,
        "Intermediate": 3,
        "Advanced": 4,
        "Expert": 5
    }
    
    # Calculate skill score
    total_required = len(role_requirements)
    skills_met = 0
    
    # Create a map of employee skills by skill_id
    emp_skill_map = {es.skill_id: es for es in employee_skills}
    
    for requirement in role_requirements:
        emp_skill = emp_skill_map.get(requirement.skill_id)
        
        if emp_skill and emp_skill.rating:
            emp_rating_value = rating_values.get(emp_skill.rating.value, 0)
            req_rating_value = rating_values.get(requirement.required_rating, 0)
            
            if emp_rating_value >= req_rating_value:
                skills_met += 1
    
    skill_score = (skills_met / total_required * 100) if total_required > 0 else 100
    
    # Placeholder scores (will be populated from HRMS later)
    cert_score = 0  # Certifications score
    exp_score = 0   # Experience score
    
    # Weighted average
    readiness = (skill_score * 0.7) + (cert_score * 0.2) + (exp_score * 0.1)
    
    return round(readiness, 2)


@router.post("/request", response_model=LevelMovementRequestSchema)
async def create_level_movement_request(
    request_data: LevelMovementRequestCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Employee submits a level movement request.
    Automatically calculates readiness score.
    """
    # Get employee record
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Check if employee already has a pending request
    existing_request = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.employee_id == employee.id,
        LevelMovementRequest.status.in_(["pending", "manager_approved", "cp_approved"])
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="You already have a pending level movement request"
        )
    
    # Calculate readiness score
    readiness_score = calculate_readiness_score(
        employee.id,
        request_data.requested_level,
        db
    )
    
    # Create request
    movement_request = LevelMovementRequest(
        employee_id=employee.id,
        current_level=employee.grade or employee.band,
        requested_level=request_data.requested_level,
        readiness_score=readiness_score,
        status="pending"
    )
    
    db.add(movement_request)
    db.commit()
    db.refresh(movement_request)
    
    return movement_request


@router.get("/requests", response_model=List[LevelMovementRequestSchema])
async def list_all_level_movement_requests(
    status_filter: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    List all level movement requests.
    Requires: HR or System Admin role
    Optional filter by status.
    """
    query = db.query(LevelMovementRequest)
    
    if status_filter:
        query = query.filter(LevelMovementRequest.status == status_filter)
    
    requests = query.order_by(LevelMovementRequest.submission_date.desc()).all()
    return requests


@router.get("/requests/{request_id}", response_model=LevelMovementRequestSchema)
async def get_level_movement_request(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific level movement request"""
    movement_request = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.id == request_id
    ).first()
    
    if not movement_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    role_name = get_user_role(current_user, db)
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    # Allow if: HR/Admin, the employee themselves, or their manager/CP
    if role_name not in ["System Admin", "HR"]:
        if not employee or movement_request.employee_id != employee.id:
            # Check if user is the employee's manager
            request_employee = db.query(Employee).filter(
                Employee.id == movement_request.employee_id
            ).first()
            
            if not request_employee or request_employee.line_manager_id != employee.id:
                raise HTTPException(status_code=403, detail="Access denied")
    
    return movement_request


@router.get("/my-requests", response_model=List[LevelMovementRequestSchema])
async def get_my_level_movement_requests(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current employee's level movement requests"""
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        return []
    
    requests = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.employee_id == employee.id
    ).order_by(LevelMovementRequest.submission_date.desc()).all()
    
    return requests


@router.get("/pending-approvals", response_model=List[LevelMovementRequestSchema])
async def get_pending_approvals(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get level movement requests pending approval by current user.
    Based on user's role:
    - Line Manager: Requests from direct reports in 'pending' status
    - Capability Partner: Requests in 'manager_approved' status from their capability
    - HR: Requests in 'cp_approved' status
    """
    role_name = get_user_role(current_user, db)
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not employee:
        return []
    
    if role_name == "Line Manager":
        # Get requests from direct reports
        requests = db.query(LevelMovementRequest).join(
            Employee, LevelMovementRequest.employee_id == Employee.id
        ).filter(
            Employee.line_manager_id == employee.id,
            LevelMovementRequest.status == "pending"
        ).all()
        
    elif role_name == "Capability Partner":
        # Get requests from capability group
        requests = db.query(LevelMovementRequest).join(
            Employee, LevelMovementRequest.employee_id == Employee.id
        ).filter(
            Employee.capability_owner_id == employee.capability_owner_id,
            LevelMovementRequest.status == "manager_approved"
        ).all()
        
    elif role_name in ["HR", "System Admin"]:
        # Get requests needing final approval
        requests = db.query(LevelMovementRequest).filter(
            LevelMovementRequest.status == "cp_approved"
        ).all()
        
    else:
        requests = []
    
    return requests


@router.post("/requests/{request_id}/approve", response_model=LevelMovementRequestSchema)
async def approve_level_movement_request(
    request_id: int,
    approval: ApprovalRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("Line Manager", "Capability Partner", "HR", "System Admin"))
):
    """
    Approve a level movement request.
    Workflow: Manager → CP → HR
    """
    movement_request = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.id == request_id
    ).first()
    
    if not movement_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    role_name = get_user_role(current_user, db)
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    # Determine approval stage based on role and current status
    if role_name == "Line Manager" and movement_request.status == "pending":
        movement_request.status = "manager_approved"
        movement_request.manager_approval_date = datetime.utcnow()
        approver_role = "Line Manager"
        
    elif role_name == "Capability Partner" and movement_request.status == "manager_approved":
        movement_request.status = "cp_approved"
        movement_request.cp_approval_date = datetime.utcnow()
        approver_role = "Capability Partner"
        
    elif role_name in ["HR", "System Admin"] and movement_request.status == "cp_approved":
        movement_request.status = "hr_approved"
        movement_request.hr_approval_date = datetime.utcnow()
        approver_role = "HR"
        
        # Update employee's grade
        request_employee = db.query(Employee).filter(
            Employee.id == movement_request.employee_id
        ).first()
        if request_employee:
            request_employee.grade = movement_request.requested_level
        
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve request in status '{movement_request.status}' with role '{role_name}'"
        )
    
    # Create audit record
    audit = LevelMovementApprovalAudit(
        request_id=request_id,
        approver_id=employee.id if employee else None,
        approver_role=approver_role,
        approval_status="approved",
        comments=approval.comments
    )
    
    db.add(audit)
    db.commit()
    db.refresh(movement_request)
    
    return movement_request


@router.post("/requests/{request_id}/reject", response_model=LevelMovementRequestSchema)
async def reject_level_movement_request(
    request_id: int,
    approval: ApprovalRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("Line Manager", "Capability Partner", "HR", "System Admin"))
):
    """
    Reject a level movement request.
    Can be rejected at any stage.
    """
    movement_request = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.id == request_id
    ).first()
    
    if not movement_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if movement_request.status in ["rejected", "hr_approved"]:
        raise HTTPException(
            status_code=400,
            detail="Request has already been finalized"
        )
    
    role_name = get_user_role(current_user, db)
    employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    # Update request status
    movement_request.status = "rejected"
    movement_request.rejection_reason = approval.comments
    
    # Create audit record
    audit = LevelMovementApprovalAudit(
        request_id=request_id,
        approver_id=employee.id if employee else None,
        approver_role=role_name,
        approval_status="rejected",
        comments=approval.comments
    )
    
    db.add(audit)
    db.commit()
    db.refresh(movement_request)
    
    return movement_request


@router.get("/requests/{request_id}/approvals", response_model=List[LevelMovementApprovalAuditSchema])
async def get_request_approval_history(
    request_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get approval history for a level movement request"""
    movement_request = db.query(LevelMovementRequest).filter(
        LevelMovementRequest.id == request_id
    ).first()
    
    if not movement_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    approvals = db.query(LevelMovementApprovalAudit).filter(
        LevelMovementApprovalAudit.request_id == request_id
    ).order_by(LevelMovementApprovalAudit.timestamp).all()
    
    return approvals

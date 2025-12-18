"""API endpoints for Manager-Driven Skill Assessment.

Only Line Managers (role_id=5) and Delivery Managers (role_id=4) can assess skills.
Role IDs: 1=Admin, 2=HR, 3=Capability Partner, 4=Delivery Manager, 5=Line Manager, 6=Employee
Employees can only view their own assessments (read-only).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, Employee, RatingEnum, SkillTemplate
from app.api.dependencies import get_current_user, get_current_active_user
from app.services.assessment_service import (
    AssessmentService, get_assessment_service,
    AssessmentWithDetails, AssessmentHistoryItem
)
from app.services.authority_validator import AuthorityValidator, get_authority_validator
from app.services.readiness_calculator import ReadinessCalculator, get_readiness_calculator
from app.services.template_assessment import (
    TemplateAssessmentService, get_template_assessment_service,
    TemplateAssessmentView, SkillAssessmentInput, TemplateAssessmentResult, AssessmentProgress
)
from app.core.permissions import RoleID
import json

router = APIRouter(prefix="/api/assessments", tags=["Skill Assessments"])


# Request/Response Models
class AssessmentCreate(BaseModel):
    """Request body for creating/updating an assessment."""
    level: str  # Beginner, Developing, Intermediate, Advanced, Expert
    comments: Optional[str] = None


class AssessmentResponse(BaseModel):
    """Response for a single assessment."""
    id: int
    employee_id: int
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    level: str
    assessment_type: str
    assessor_id: Optional[int]
    assessor_name: Optional[str]
    assessor_role: str
    comments: Optional[str]
    assessed_at: datetime
    
    class Config:
        from_attributes = True


class AssessableEmployeeResponse(BaseModel):
    """Response for an assessable employee."""
    id: int
    employee_id: str
    name: str
    band: Optional[str]
    pathway: Optional[str]
    department: Optional[str]
    
    class Config:
        from_attributes = True


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
            detail="Only Line Managers and Delivery Managers can assess skills"
        )


def _parse_rating(level_str: str) -> RatingEnum:
    """Parse rating string to enum."""
    level_map = {
        "beginner": RatingEnum.BEGINNER,
        "developing": RatingEnum.DEVELOPING,
        "intermediate": RatingEnum.INTERMEDIATE,
        "advanced": RatingEnum.ADVANCED,
        "expert": RatingEnum.EXPERT,
    }
    
    rating = level_map.get(level_str.lower())
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid level: {level_str}. Must be one of: Beginner, Developing, Intermediate, Advanced, Expert"
        )
    return rating


@router.post("/employee/{employee_id}/skill/{skill_id}", response_model=AssessmentResponse)
async def create_assessment(
    employee_id: int,
    skill_id: int,
    assessment: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create or update a skill assessment for an employee.
    
    Only Line Managers and Delivery Managers can assess skills.
    Manager must have authority over the employee (direct report or project assignment).
    """
    _validate_manager_role(current_user)
    
    manager_emp_id = _get_manager_employee_id(current_user, db)
    level = _parse_rating(assessment.level)
    
    service = get_assessment_service(db)
    
    try:
        result, is_new = service.create_assessment(
            employee_id=employee_id,
            skill_id=skill_id,
            level=level,
            assessor_id=manager_emp_id,
            assessor_role_id=current_user.role_id,
            comments=assessment.comments
        )
        
        # Get full details for response
        assessments = service.get_employee_assessments(employee_id)
        for a in assessments:
            if a.skill_id == skill_id:
                return a
        
        # Fallback
        return AssessmentResponse(
            id=result.id,
            employee_id=result.employee_id,
            skill_id=result.skill_id,
            skill_name="",
            skill_category=None,
            level=result.level.value,
            assessment_type=result.assessment_type.value,
            assessor_id=result.assessor_id,
            assessor_name=None,
            assessor_role=result.assessor_role.value,
            comments=result.comments,
            assessed_at=result.assessed_at
        )
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/employee/{employee_id}", response_model=List[AssessmentResponse])
async def get_employee_assessments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all skill assessments for an employee.
    
    Access control:
    - Employees can view their own assessments
    - Managers can view their direct reports' assessments
    - HR and Admins can view all
    """
    # Check access
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    # Check if user is viewing their own data
    is_own_data = current_user.employee_id == employee.employee_id
    
    # Check if user has elevated access
    has_elevated_access = (
        current_user.is_admin or
        current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]
    )
    
    # Check if manager has authority
    has_manager_authority = False
    if current_user.role_id in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
        try:
            manager_emp_id = _get_manager_employee_id(current_user, db)
            validator = get_authority_validator(db)
            has_manager_authority, _ = validator.can_assess(
                manager_emp_id, current_user.role_id, employee_id
            )
        except:
            pass
    
    if not (is_own_data or has_elevated_access or has_manager_authority):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's assessments"
        )
    
    service = get_assessment_service(db)
    return service.get_employee_assessments(employee_id)


@router.get("/employee/{employee_id}/history", response_model=List[AssessmentHistoryItem])
async def get_assessment_history(
    employee_id: int,
    skill_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get assessment history for an employee.
    
    Same access control as get_employee_assessments.
    """
    # Check access (same logic as get_employee_assessments)
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )
    
    is_own_data = current_user.employee_id == employee.employee_id
    has_elevated_access = (
        current_user.is_admin or
        current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]
    )
    
    has_manager_authority = False
    if current_user.role_id in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
        try:
            manager_emp_id = _get_manager_employee_id(current_user, db)
            validator = get_authority_validator(db)
            has_manager_authority, _ = validator.can_assess(
                manager_emp_id, current_user.role_id, employee_id
            )
        except:
            pass
    
    if not (is_own_data or has_elevated_access or has_manager_authority):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this employee's assessment history"
        )
    
    service = get_assessment_service(db)
    return service.get_assessment_history(employee_id, skill_id)


@router.get("/assessable-employees", response_model=List[AssessableEmployeeResponse])
async def get_assessable_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of employees the current manager can assess.
    
    Only available to Line Managers and Delivery Managers.
    """
    _validate_manager_role(current_user)
    
    manager_emp_id = _get_manager_employee_id(current_user, db)
    
    validator = get_authority_validator(db)
    employees = validator.get_assessable_employees(manager_emp_id, current_user.role_id)
    
    return [
        AssessableEmployeeResponse(
            id=emp.id,
            employee_id=emp.employee_id,
            name=emp.name,
            band=emp.band,
            pathway=emp.pathway,
            department=emp.department
        )
        for emp in employees
    ]


# ============================================================================
# Template Assessment API Endpoints
# ============================================================================

class TemplateListItem(BaseModel):
    """Response for a template in the list."""
    id: int
    template_name: str
    file_name: str
    created_at: datetime
    skill_count: int
    
    class Config:
        from_attributes = True


class TemplateSkillAssessmentInput(BaseModel):
    """Input for a single skill assessment in template submission."""
    skill_id: int
    level: str
    comments: Optional[str] = None


class TemplateAssessmentSubmit(BaseModel):
    """Request body for submitting template assessments."""
    assessments: List[TemplateSkillAssessmentInput]


@router.get("/templates", response_model=List[TemplateListItem])
async def get_available_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available skill templates for assessment.
    
    Only available to Line Managers and Delivery Managers.
    Returns templates with metadata (without full content).
    
    Requirements: 1.1
    """
    _validate_manager_role(current_user)
    
    templates = db.query(SkillTemplate).order_by(SkillTemplate.created_at.desc()).all()
    
    result = []
    for t in templates:
        # Parse content to count skills
        try:
            content = json.loads(t.content) if t.content else []
            # Count rows that have skill data (excluding header rows)
            skill_count = max(0, len(content) - 1) if content else 0
        except (json.JSONDecodeError, TypeError):
            skill_count = 0
        
        result.append(TemplateListItem(
            id=t.id,
            template_name=t.template_name,
            file_name=t.file_name,
            created_at=t.created_at,
            skill_count=skill_count
        ))
    
    return result


@router.get("/template/{template_id}/employee/{employee_id}", response_model=TemplateAssessmentView)
async def get_template_for_assessment(
    template_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get template skills with employee's current levels for assessment.
    
    Only available to Line Managers and Delivery Managers with authority over the employee.
    Returns all skills from the template with the employee's current assessment levels.
    
    Requirements: 1.2
    """
    _validate_manager_role(current_user)
    
    # Validate manager authority
    manager_emp_id = _get_manager_employee_id(current_user, db)
    validator = get_authority_validator(db)
    is_authorized, reason = validator.can_assess(manager_emp_id, current_user.role_id, employee_id)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have authority over this employee: {reason}"
        )
    
    service = get_template_assessment_service(db)
    
    try:
        return service.get_template_for_assessment(template_id, employee_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/template/{template_id}/employee/{employee_id}", response_model=TemplateAssessmentResult)
async def submit_template_assessment(
    template_id: int,
    employee_id: int,
    submission: TemplateAssessmentSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit assessments for all skills in a template.
    
    Only available to Line Managers and Delivery Managers with authority over the employee.
    Creates or updates skill assessments for each skill in the submission.
    Records the assessment in template_assessment_logs for audit purposes.
    
    Requirements: 1.3, 1.4
    """
    _validate_manager_role(current_user)
    
    # Validate manager authority
    manager_emp_id = _get_manager_employee_id(current_user, db)
    validator = get_authority_validator(db)
    is_authorized, reason = validator.can_assess(manager_emp_id, current_user.role_id, employee_id)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have authority over this employee: {reason}"
        )
    
    # Convert input to service format
    assessments = [
        SkillAssessmentInput(
            skill_id=a.skill_id,
            level=a.level,
            comments=a.comments
        )
        for a in submission.assessments
    ]
    
    service = get_template_assessment_service(db)
    
    try:
        return service.submit_template_assessment(
            template_id=template_id,
            employee_id=employee_id,
            assessor_id=manager_emp_id,
            assessor_role_id=current_user.role_id,
            assessments=assessments
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/template/{template_id}/employee/{employee_id}/progress", response_model=AssessmentProgress)
async def get_template_assessment_progress(
    template_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get completion percentage for template assessment.
    
    Only available to Line Managers and Delivery Managers with authority over the employee.
    Returns the number of assessed skills vs total skills and completion percentage.
    
    Requirements: 1.5
    """
    _validate_manager_role(current_user)
    
    # Validate manager authority
    manager_emp_id = _get_manager_employee_id(current_user, db)
    validator = get_authority_validator(db)
    is_authorized, reason = validator.can_assess(manager_emp_id, current_user.role_id, employee_id)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have authority over this employee: {reason}"
        )
    
    service = get_template_assessment_service(db)
    
    try:
        return service.get_assessment_progress(template_id, employee_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

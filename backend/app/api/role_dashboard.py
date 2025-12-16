"""Role-Based Dashboard API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.models import User, Employee, EmployeeSkill, Skill
from app.api.dependencies import get_current_user, get_hr_or_admin_user, get_manager_user, get_cp_user
from app.core.permissions import RoleID, get_accessible_fields, can_view_employee, mask_fields, SENSITIVE_FIELDS

router = APIRouter(prefix="/api/dashboard", tags=["role-dashboard"])


class DashboardConfig(BaseModel):
    role: str
    role_id: int
    accessible_features: List[str]
    can_view_sensitive: bool
    can_edit_skills: bool
    can_manage_users: bool


class EmployeeListItem(BaseModel):
    id: int
    employee_id: str
    name: str
    department: Optional[str]
    capability: Optional[str]
    band: Optional[str]
    company_email: Optional[str]


class TeamMember(BaseModel):
    id: int
    employee_id: str
    name: str
    capability: Optional[str]
    skills_count: int
    skill_gaps: int


# ============ DASHBOARD CONFIG ============

@router.get("/config", response_model=DashboardConfig)
def get_dashboard_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get dashboard configuration based on user role"""
    role_id = current_user.role_id or RoleID.EMPLOYEE
    
    role_names = {
        RoleID.SYSTEM_ADMIN: "System Admin",
        RoleID.HR: "HR",
        RoleID.CAPABILITY_PARTNER: "Capability Partner",
        RoleID.DELIVERY_MANAGER: "Delivery Manager",
        RoleID.LINE_MANAGER: "Line Manager",
        RoleID.EMPLOYEE: "Employee"
    }
    
    features = {
        RoleID.SYSTEM_ADMIN: ["employee_directory", "sensitive_data", "user_management", "audit_logs", "system_settings", "all_metrics", "skill_templates"],
        RoleID.HR: ["employee_directory", "sensitive_data", "skill_templates", "hr_analytics", "onboarding", "capability_management", "hr_reports"],
        RoleID.CAPABILITY_PARTNER: ["capability_members", "skill_matrix", "capability_metrics", "skill_gaps", "certifications", "learning_paths"],
        RoleID.DELIVERY_MANAGER: ["team_overview", "project_staffing", "skill_gaps", "resource_allocation", "availability"],
        RoleID.LINE_MANAGER: ["direct_reports", "team_skills", "performance_inputs", "appraisals", "career_tracking"],
        RoleID.EMPLOYEE: ["my_profile", "my_skills", "my_assignments", "career_path", "my_manager"]
    }
    
    return DashboardConfig(
        role=role_names.get(role_id, "Employee"),
        role_id=role_id,
        accessible_features=features.get(role_id, features[RoleID.EMPLOYEE]),
        can_view_sensitive=role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR],
        can_edit_skills=role_id != RoleID.SYSTEM_ADMIN,  # Admin shouldn't modify skills
        can_manage_users=role_id == RoleID.SYSTEM_ADMIN
    )


# ============ HR DASHBOARD ============

@router.get("/hr/employees")
def hr_get_all_employees(
    skip: int = 0, limit: int = 100,
    department: Optional[str] = None,
    capability: Optional[str] = None,
    current_user: User = Depends(get_hr_or_admin_user),
    db: Session = Depends(get_db)
):
    """HR: Get all employees with full access"""
    query = db.query(Employee)
    if department:
        query = query.filter(Employee.department == department)
    if capability:
        query = query.filter(Employee.capability == capability)
    
    employees = query.offset(skip).limit(limit).all()
    allowed_fields = get_accessible_fields(current_user.role_id)
    
    return [mask_fields({
        "id": e.id, "employee_id": e.employee_id, "name": e.name,
        "first_name": e.first_name, "last_name": e.last_name,
        "company_email": e.company_email, "department": e.department,
        "capability": e.capability, "band": e.band, "grade": e.grade,
        "joining_date": str(e.joining_date) if hasattr(e, 'joining_date') else None
    }, allowed_fields) for e in employees]


@router.get("/hr/stats")
def hr_get_stats(current_user: User = Depends(get_hr_or_admin_user), db: Session = Depends(get_db)):
    """HR: Get HR analytics stats"""
    total = db.query(Employee).count()
    by_capability = db.query(Employee.capability, func.count(Employee.id)).group_by(Employee.capability).all()
    by_department = db.query(Employee.department, func.count(Employee.id)).group_by(Employee.department).all()
    by_band = db.query(Employee.band, func.count(Employee.id)).group_by(Employee.band).all()
    
    return {
        "total_employees": total,
        "by_capability": {c or "Unassigned": cnt for c, cnt in by_capability},
        "by_department": {d or "Unassigned": cnt for d, cnt in by_department},
        "by_band": {b or "Unassigned": cnt for b, cnt in by_band}
    }


# ============ CAPABILITY PARTNER DASHBOARD ============

@router.get("/cp/members")
def cp_get_capability_members(
    current_user: User = Depends(get_cp_user),
    db: Session = Depends(get_db)
):
    """CP: Get employees in their capability only"""
    # Get CP's capability from their employee record
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp or not emp.capability:
        raise HTTPException(status_code=400, detail="Capability not assigned")
    
    # HR/Admin can see all, CP sees only their capability
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        employees = db.query(Employee).all()
    else:
        employees = db.query(Employee).filter(Employee.capability == emp.capability).all()
    
    allowed_fields = get_accessible_fields(current_user.role_id)
    return [mask_fields({
        "id": e.id, "employee_id": e.employee_id, "name": e.name,
        "capability": e.capability, "band": e.band,
        "company_email": e.company_email
    }, allowed_fields) for e in employees]


@router.get("/cp/skill-matrix")
def cp_get_skill_matrix(
    current_user: User = Depends(get_cp_user),
    db: Session = Depends(get_db)
):
    """CP: Get skill matrix for capability"""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    capability = emp.capability if emp else None
    
    query = db.query(Employee).join(EmployeeSkill).join(Skill)
    if current_user.role_id == RoleID.CAPABILITY_PARTNER and capability:
        query = query.filter(Employee.capability == capability)
    
    employees = query.distinct().all()
    
    result = []
    for e in employees:
        skills = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == e.id).all()
        result.append({
            "employee_id": e.employee_id,
            "name": e.name,
            "skills": [{"skill_id": s.skill_id, "rating": s.rating.value if s.rating else None} for s in skills]
        })
    return result


# ============ LINE MANAGER DASHBOARD ============

@router.get("/lm/direct-reports")
def lm_get_direct_reports(
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """LM: Get direct reports only"""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        return []
    
    # HR/Admin see all, LM sees only direct reports
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        reports = db.query(Employee).all()
    else:
        reports = db.query(Employee).filter(Employee.line_manager_id == emp.id).all()
    
    allowed_fields = get_accessible_fields(current_user.role_id)
    result = []
    for r in reports:
        skills_count = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == r.id, EmployeeSkill.is_interested == False).count()
        result.append(mask_fields({
            "id": r.id, "employee_id": r.employee_id, "name": r.name,
            "capability": r.capability, "band": r.band,
            "skills_count": skills_count
        }, allowed_fields))
    return result


@router.get("/lm/team-skills")
def lm_get_team_skills(
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """LM: Get skills overview for direct reports"""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        return []
    
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        reports = db.query(Employee).all()
    else:
        reports = db.query(Employee).filter(Employee.line_manager_id == emp.id).all()
    
    result = []
    for r in reports:
        skills = db.query(EmployeeSkill).join(Skill).filter(EmployeeSkill.employee_id == r.id).all()
        result.append({
            "employee_id": r.employee_id,
            "name": r.name,
            "skills": [{"name": s.skill.name, "rating": s.rating.value if s.rating else None} for s in skills]
        })
    return result


# ============ DELIVERY MANAGER DASHBOARD ============

@router.get("/dm/team-overview")
def dm_get_team_overview(
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """DM: Get delivery team overview"""
    # For now, DM sees employees they manage (via project assignments or direct)
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        return []
    
    if current_user.role_id in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        team = db.query(Employee).all()
    elif current_user.role_id == RoleID.DELIVERY_MANAGER:
        # DM sees employees in their projects (simplified: same capability for now)
        team = db.query(Employee).filter(Employee.capability == emp.capability).all()
    else:
        team = db.query(Employee).filter(Employee.line_manager_id == emp.id).all()
    
    allowed_fields = get_accessible_fields(current_user.role_id)
    return [mask_fields({
        "id": e.id, "employee_id": e.employee_id, "name": e.name,
        "capability": e.capability, "band": e.band
    }, allowed_fields) for e in team]


# ============ EMPLOYEE SELF-SERVICE ============

@router.get("/employee/my-profile")
def employee_get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Employee: Get own profile with extended access"""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Self-access gets more fields
    allowed_fields = get_accessible_fields(current_user.role_id, is_self=True)
    
    manager = None
    if emp.line_manager_id:
        mgr = db.query(Employee).filter(Employee.id == emp.line_manager_id).first()
        if mgr:
            manager = {"name": mgr.name, "email": mgr.company_email}
    
    return mask_fields({
        "id": emp.id, "employee_id": emp.employee_id, "name": emp.name,
        "first_name": emp.first_name, "last_name": emp.last_name,
        "company_email": emp.company_email, "department": emp.department,
        "capability": emp.capability, "band": emp.band, "grade": emp.grade,
        "team": emp.team, "category": emp.category,
        "line_manager": manager
    }, allowed_fields)


@router.get("/employee/my-skills")
def employee_get_my_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Employee: Get own skills"""
    emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not emp:
        return []
    
    skills = db.query(EmployeeSkill).join(Skill).filter(EmployeeSkill.employee_id == emp.id).all()
    return [{
        "id": s.id,
        "skill_name": s.skill.name,
        "skill_category": s.skill.category,
        "rating": s.rating.value if s.rating else None,
        "years_experience": s.years_experience,
        "is_interested": s.is_interested,
        "learning_status": s.learning_status
    } for s in skills]

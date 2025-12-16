"""RBAC-Protected Employee API Endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.core.security import get_current_user
from app.core.rbac import (
    Role, require_roles, DataAccessController, log_sensitive_access,
    get_capability_employees, get_direct_reports, get_delivery_unit
)
from app.models.rbac import UserWithRBAC, Capability, AuditLog

router = APIRouter(prefix="/api/v2/employees", tags=["RBAC Employees"])


# Schemas
class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: Optional[str]
    capability: Optional[str]
    role: str
    joining_date: Optional[datetime]
    skill_rating: Optional[str] = None
    # Sensitive - may be masked
    personal_email: Optional[str] = None
    phone_number: Optional[str] = None
    salary: Optional[int] = None
    performance_rating: Optional[str] = None

    class Config:
        from_attributes = True


class CapabilityMetrics(BaseModel):
    capability: str
    total_employees: int
    skill_distribution: dict
    avg_tenure_months: float


# Endpoints
@router.get("/me", response_model=EmployeeResponse)
async def get_my_profile(
    request: Request,
    current_user: UserWithRBAC = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's own profile - all users can access"""
    allowed_fields = DataAccessController.get_accessible_fields(current_user, current_user.id, db)
    data = {c.name: getattr(current_user, c.name) for c in current_user.__table__.columns}
    return DataAccessController.mask_sensitive_data(data, allowed_fields)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee_profile(
    employee_id: int,
    request: Request,
    current_user: UserWithRBAC = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get employee profile with RBAC filtering"""
    if not DataAccessController.can_view_employee(current_user, employee_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this employee")
    
    employee = db.query(UserWithRBAC).filter(UserWithRBAC.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    allowed_fields = DataAccessController.get_accessible_fields(current_user, employee_id, db)
    data = {c.name: getattr(employee, c.name) for c in employee.__table__.columns}
    
    # Log sensitive access
    log_sensitive_access(db, current_user, "VIEW", "employee_profile", str(employee_id), list(allowed_fields), request)
    
    return DataAccessController.mask_sensitive_data(data, allowed_fields)


@router.get("/capability/{capability}", response_model=List[EmployeeResponse])
async def get_capability_employees_endpoint(
    capability: Capability,
    request: Request,
    current_user: UserWithRBAC = Depends(require_roles(Role.SYSTEM_ADMIN, Role.HR, Role.CAPABILITY_PARTNER)),
    db: Session = Depends(get_db)
):
    """Get employees by capability - CP only sees own capability"""
    if current_user.role == Role.CAPABILITY_PARTNER and current_user.capability != capability:
        raise HTTPException(status_code=403, detail="Can only view your own capability")
    
    employees = get_capability_employees(db, capability.value)
    result = []
    for emp in employees:
        allowed_fields = DataAccessController.get_accessible_fields(current_user, emp.id, db)
        data = {c.name: getattr(emp, c.name) for c in emp.__table__.columns}
        result.append(DataAccessController.mask_sensitive_data(data, allowed_fields))
    
    log_sensitive_access(db, current_user, "VIEW", "capability_list", capability.value, [], request)
    return result


@router.get("/reports/direct", response_model=List[EmployeeResponse])
async def get_my_direct_reports(
    request: Request,
    current_user: UserWithRBAC = Depends(require_roles(Role.SYSTEM_ADMIN, Role.HR, Role.LINE_MANAGER, Role.DELIVERY_MANAGER)),
    db: Session = Depends(get_db)
):
    """Get direct reports for line manager"""
    if current_user.role == Role.LINE_MANAGER:
        employees = get_direct_reports(db, current_user.id)
    elif current_user.role == Role.DELIVERY_MANAGER:
        employees = get_delivery_unit(db, current_user.id)
    else:
        employees = db.query(UserWithRBAC).filter(UserWithRBAC.is_active == True).all()
    
    result = []
    for emp in employees:
        allowed_fields = DataAccessController.get_accessible_fields(current_user, emp.id, db)
        data = {c.name: getattr(emp, c.name) for c in emp.__table__.columns}
        result.append(DataAccessController.mask_sensitive_data(data, allowed_fields))
    return result


@router.get("/metrics/capability/{capability}", response_model=CapabilityMetrics)
async def get_capability_metrics(
    capability: Capability,
    current_user: UserWithRBAC = Depends(require_roles(Role.SYSTEM_ADMIN, Role.HR, Role.CAPABILITY_PARTNER, Role.DELIVERY_MANAGER)),
    db: Session = Depends(get_db)
):
    """Get aggregate metrics for capability - no individual sensitive data exposed"""
    if current_user.role == Role.CAPABILITY_PARTNER and current_user.capability != capability:
        raise HTTPException(status_code=403, detail="Can only view your own capability metrics")
    
    employees = get_capability_employees(db, capability.value)
    
    # Aggregate only - no individual data
    skill_dist = {}
    total_tenure = 0
    for emp in employees:
        rating = emp.performance_rating or "Unrated"
        skill_dist[rating] = skill_dist.get(rating, 0) + 1
        if emp.joining_date:
            tenure = (datetime.utcnow() - emp.joining_date).days / 30
            total_tenure += tenure
    
    return CapabilityMetrics(
        capability=capability.value,
        total_employees=len(employees),
        skill_distribution=skill_dist,
        avg_tenure_months=round(total_tenure / len(employees), 1) if employees else 0
    )


@router.get("/audit/logs", response_model=List[dict])
async def get_audit_logs(
    limit: int = Query(100, le=1000),
    current_user: UserWithRBAC = Depends(require_roles(Role.SYSTEM_ADMIN, Role.HR)),
    db: Session = Depends(get_db)
):
    """Get audit logs - Admin/HR only"""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "user_role": log.user_role.value,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "fields_accessed": log.fields_accessed,
            "gdpr_basis": log.gdpr_basis
        }
        for log in logs
    ]

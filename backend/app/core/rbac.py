"""RBAC Authorization Logic for Skillboard"""
from functools import wraps
from typing import List, Optional, Set
from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from app.models.rbac import Role, DataSensitivity, FIELD_CLASSIFICATION, UserWithRBAC, AuditLog
from app.db.database import get_db
from app.core.security import get_current_user

# Role hierarchy for permission inheritance
ROLE_HIERARCHY = {
    Role.SYSTEM_ADMIN: 100,
    Role.HR: 90,
    Role.CAPABILITY_PARTNER: 70,
    Role.DELIVERY_MANAGER: 60,
    Role.LINE_MANAGER: 50,
    Role.EMPLOYEE: 10,
}

# Sensitive fields by role access
SENSITIVE_FIELD_ACCESS = {
    Role.SYSTEM_ADMIN: {"personal_email", "phone_number", "address", "salary", "date_of_birth", "national_id", "performance_rating", "medical_info"},
    Role.HR: {"personal_email", "phone_number", "address", "salary", "date_of_birth", "national_id", "performance_rating", "medical_info"},
    Role.CAPABILITY_PARTNER: set(),  # No sensitive fields
    Role.DELIVERY_MANAGER: set(),
    Role.LINE_MANAGER: {"performance_rating"},  # Only for direct reports
    Role.EMPLOYEE: set(),  # Only own data via self-access
}


class RBACChecker:
    """RBAC permission checker"""
    
    def __init__(self, allowed_roles: List[Role] = None, min_role_level: int = None):
        self.allowed_roles = allowed_roles or []
        self.min_role_level = min_role_level

    def __call__(self, current_user: UserWithRBAC = Depends(get_current_user)):
        if self.allowed_roles and current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        if self.min_role_level and ROLE_HIERARCHY.get(current_user.role, 0) < self.min_role_level:
            raise HTTPException(status_code=403, detail="Insufficient role level")
        return current_user


def require_roles(*roles: Role):
    """Decorator to require specific roles"""
    return RBACChecker(allowed_roles=list(roles))


def require_min_level(level: int):
    """Decorator to require minimum role level"""
    return RBACChecker(min_role_level=level)


class DataAccessController:
    """Controls data access based on role and relationship"""
    
    @staticmethod
    def can_view_employee(viewer: UserWithRBAC, target_employee_id: int, db: Session) -> bool:
        """Check if viewer can access target employee data"""
        if viewer.role in [Role.SYSTEM_ADMIN, Role.HR]:
            return True
        if viewer.id == target_employee_id:
            return True  # Self-access
        
        target = db.query(UserWithRBAC).filter(UserWithRBAC.id == target_employee_id).first()
        if not target:
            return False
            
        # CP can view same capability
        if viewer.role == Role.CAPABILITY_PARTNER and viewer.capability == target.capability:
            return True
        # Line Manager can view direct reports
        if viewer.role == Role.LINE_MANAGER and target.line_manager_id == viewer.id:
            return True
        # Delivery Manager can view their delivery unit
        if viewer.role == Role.DELIVERY_MANAGER and target.delivery_manager_id == viewer.id:
            return True
        return False

    @staticmethod
    def get_accessible_fields(viewer: UserWithRBAC, target_id: int, db: Session) -> Set[str]:
        """Get fields the viewer can access for target employee"""
        is_self = viewer.id == target_id
        base_fields = {"employee_id", "first_name", "last_name", "company_email", "department", "capability", "skills"}
        
        if viewer.role in [Role.SYSTEM_ADMIN, Role.HR]:
            return base_fields | SENSITIVE_FIELD_ACCESS[viewer.role] | {"joining_date", "skill_rating"}
        
        if is_self:
            # Self can see own sensitive data except national_id (HR only)
            return base_fields | {"personal_email", "phone_number", "address", "salary", "date_of_birth", "performance_rating", "joining_date", "skill_rating"}
        
        target = db.query(UserWithRBAC).filter(UserWithRBAC.id == target_id).first()
        
        # CP sees capability employees' skills
        if viewer.role == Role.CAPABILITY_PARTNER and target and viewer.capability == target.capability:
            return base_fields | {"skill_rating", "joining_date"}
        
        # Line Manager sees direct reports
        if viewer.role == Role.LINE_MANAGER and target and target.line_manager_id == viewer.id:
            return base_fields | {"skill_rating", "joining_date", "performance_rating"}
        
        # Delivery Manager
        if viewer.role == Role.DELIVERY_MANAGER and target and target.delivery_manager_id == viewer.id:
            return base_fields | {"skill_rating", "joining_date"}
        
        return base_fields

    @staticmethod
    def mask_sensitive_data(data: dict, allowed_fields: Set[str]) -> dict:
        """Mask fields not in allowed set"""
        masked = {}
        for key, value in data.items():
            if key in allowed_fields:
                masked[key] = value
            elif FIELD_CLASSIFICATION.get(key) == DataSensitivity.SENSITIVE:
                masked[key] = "***REDACTED***"
            else:
                masked[key] = value
        return masked


def log_sensitive_access(
    db: Session,
    user: UserWithRBAC,
    action: str,
    resource_type: str,
    resource_id: str = None,
    fields: List[str] = None,
    request: Request = None,
    gdpr_basis: str = None
):
    """Log access to sensitive data - GDPR compliance"""
    sensitive_fields = [f for f in (fields or []) if FIELD_CLASSIFICATION.get(f) == DataSensitivity.SENSITIVE]
    if not sensitive_fields and action != "EXPORT":
        return  # Only log sensitive access
    
    log = AuditLog(
        user_id=user.id,
        user_role=user.role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        fields_accessed=sensitive_fields,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        gdpr_basis=gdpr_basis or "Legitimate interest"
    )
    db.add(log)
    db.commit()


def get_capability_employees(db: Session, capability: str) -> List[UserWithRBAC]:
    """Get all employees in a capability"""
    return db.query(UserWithRBAC).filter(UserWithRBAC.capability == capability, UserWithRBAC.is_active == True).all()


def get_direct_reports(db: Session, manager_id: int) -> List[UserWithRBAC]:
    """Get direct reports for a line manager"""
    return db.query(UserWithRBAC).filter(UserWithRBAC.line_manager_id == manager_id, UserWithRBAC.is_active == True).all()


def get_delivery_unit(db: Session, dm_id: int) -> List[UserWithRBAC]:
    """Get employees under a delivery manager"""
    return db.query(UserWithRBAC).filter(UserWithRBAC.delivery_manager_id == dm_id, UserWithRBAC.is_active == True).all()

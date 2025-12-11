"""
RBAC (Role-Based Access Control) dependencies for API endpoints.
Provides role-based authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import database
from app.db.models import User, Role
from app.api.dependencies import get_current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles for an endpoint.
    
    Usage:
        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_role("System Admin"))):
            pass
    
    Args:
        *allowed_roles: Variable number of role names that are allowed
    
    Returns:
        Dependency function that checks user's role
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
    ):
        # Get user's role
        if current_user.role_id:
            role = db.query(Role).filter(Role.id == current_user.role_id).first()
            if role and role.name in allowed_roles:
                return current_user
        
        # Check legacy is_admin flag as fallback
        if "System Admin" in allowed_roles and current_user.is_admin:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
        )
    
    return role_checker


def get_user_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
) -> str:
    """
    Get the current user's role name.
    
    Returns:
        Role name string (e.g., "Employee", "System Admin")
    """
    if current_user.role_id:
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if role:
            return role.name
    
    # Fallback to legacy admin check
    if current_user.is_admin:
        return "System Admin"
    
    return "Employee"


def can_view_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
) -> bool:
    """
    Check if current user can view a specific employee's data.
    
    Rules:
    - System Admin, HR: Can view all employees
    - Capability Partner: Can view employees in their capability
    - Line Manager: Can view direct reports
    - Employee: Can view only themselves
    
    Args:
        employee_id: The employee ID to check access for
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        True if user can view the employee, raises HTTPException otherwise
    """
    from app.db.models import Employee
    
    role_name = get_user_role(current_user, db)
    
    # System Admin and HR can view all
    if role_name in ["System Admin", "HR"]:
        return True
    
    # Get the target employee
    target_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not target_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get current user's employee record
    current_employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    if not current_employee:
        raise HTTPException(status_code=403, detail="No employee record found")
    
    # Employee can view themselves
    if current_employee.id == employee_id:
        return True
    
    # Line Manager can view direct reports
    if role_name == "Line Manager":
        if target_employee.line_manager_id == current_employee.id:
            return True
    
    # Capability Partner can view employees in their capability
    if role_name == "Capability Partner":
        if (current_employee.capability_owner_id and 
            target_employee.capability_owner_id == current_employee.capability_owner_id):
            return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to view this employee's data"
    )


# Convenience role check functions
def require_admin(user: User = Depends(require_role("System Admin"))):
    """Require System Admin role"""
    return user


def require_hr(user: User = Depends(require_role("System Admin", "HR"))):
    """Require HR or System Admin role"""
    return user


def require_manager(user: User = Depends(require_role("System Admin", "HR", "Line Manager"))):
    """Require Line Manager, HR, or System Admin role"""
    return user


def require_cp(user: User = Depends(require_role("System Admin", "HR", "Capability Partner"))):
    """Require Capability Partner, HR, or System Admin role"""
    return user

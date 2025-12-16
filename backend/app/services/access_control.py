"""Enhanced Access Control and GDPR Compliance Service.

This service implements role-based access control with five distinct user roles,
comprehensive audit logging, and data sensitivity classification.
"""
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import User, Employee, AccessLog, Role


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    HR = "hr"
    CAPABILITY_PARTNER = "capability_partner"
    LINE_MANAGER = "line_manager"
    EMPLOYEE = "employee"


class DataSensitivity(str, Enum):
    """Data sensitivity classification levels."""
    PUBLIC = "Public"
    INTERNAL = "Internal"
    SENSITIVE = "Sensitive"
    RESTRICTED = "Restricted"


class Permission(str, Enum):
    """Available permissions."""
    VIEW_OWN_DATA = "view_own_data"
    VIEW_TEAM_DATA = "view_team_data"
    VIEW_CAPABILITY_DATA = "view_capability_data"
    VIEW_ALL_DATA = "view_all_data"
    EDIT_OWN_DATA = "edit_own_data"
    EDIT_TEAM_DATA = "edit_team_data"
    EDIT_ALL_DATA = "edit_all_data"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    MANAGE_HRMS = "manage_hrms"
    APPROVE_LEVEL_MOVEMENT = "approve_level_movement"


# Permission matrix for each role
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.VIEW_CAPABILITY_DATA,
        Permission.VIEW_ALL_DATA,
        Permission.EDIT_OWN_DATA,
        Permission.EDIT_TEAM_DATA,
        Permission.EDIT_ALL_DATA,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_DATA,
        Permission.MANAGE_HRMS,
        Permission.APPROVE_LEVEL_MOVEMENT,
    },
    UserRole.HR: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.VIEW_CAPABILITY_DATA,
        Permission.VIEW_ALL_DATA,
        Permission.EDIT_OWN_DATA,
        Permission.EDIT_ALL_DATA,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_DATA,
        Permission.APPROVE_LEVEL_MOVEMENT,
    },
    UserRole.CAPABILITY_PARTNER: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_CAPABILITY_DATA,
        Permission.EDIT_OWN_DATA,
        Permission.VIEW_REPORTS,
        Permission.APPROVE_LEVEL_MOVEMENT,
    },
    UserRole.LINE_MANAGER: {
        Permission.VIEW_OWN_DATA,
        Permission.VIEW_TEAM_DATA,
        Permission.EDIT_OWN_DATA,
        Permission.EDIT_TEAM_DATA,
        Permission.VIEW_REPORTS,
        Permission.APPROVE_LEVEL_MOVEMENT,
    },
    UserRole.EMPLOYEE: {
        Permission.VIEW_OWN_DATA,
        Permission.EDIT_OWN_DATA,
    },
}


class AccessDeniedError(Exception):
    """Exception raised when access is denied."""
    pass


class AccessLogEntry(BaseModel):
    """Model for access log entries."""
    user_id: int
    resource_type: str
    resource_id: str
    action: str
    data_sensitivity: DataSensitivity
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None


class RoleManager:
    """Manages user roles and permissions."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def get_user_role(self, user_id: int) -> UserRole:
        """Get the role for a user."""
        if not self.db:
            return UserRole.EMPLOYEE
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return UserRole.EMPLOYEE
        
        if user.is_admin:
            return UserRole.ADMIN
        
        if user.role:
            role_name = user.role.name.lower()
            if role_name == "hr":
                return UserRole.HR
            elif role_name == "capability_partner":
                return UserRole.CAPABILITY_PARTNER
            elif role_name == "line_manager":
                return UserRole.LINE_MANAGER
        
        return UserRole.EMPLOYEE
    
    def get_permissions(self, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, set())
    
    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in self.get_permissions(role)
    
    def assign_role(self, user_id: int, role: UserRole) -> bool:
        """Assign a role to a user."""
        if not self.db:
            return False
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Find or create the role
        db_role = self.db.query(Role).filter(Role.name == role.value).first()
        if not db_role:
            db_role = Role(name=role.value, description=f"{role.value} role")
            self.db.add(db_role)
            self.db.flush()
        
        user.role_id = db_role.id
        self.db.commit()
        return True


class DataClassifier:
    """Classifies data sensitivity levels."""
    
    # Field sensitivity mappings
    FIELD_SENSITIVITY: Dict[str, DataSensitivity] = {
        # Public fields
        "name": DataSensitivity.PUBLIC,
        "department": DataSensitivity.PUBLIC,
        "team": DataSensitivity.PUBLIC,
        "skills": DataSensitivity.PUBLIC,
        
        # Internal fields
        "employee_id": DataSensitivity.INTERNAL,
        "band": DataSensitivity.INTERNAL,
        "capability": DataSensitivity.INTERNAL,
        "project_assignments": DataSensitivity.INTERNAL,
        
        # Sensitive fields
        "email": DataSensitivity.SENSITIVE,
        "line_manager_id": DataSensitivity.SENSITIVE,
        "grade": DataSensitivity.SENSITIVE,
        "hire_date": DataSensitivity.SENSITIVE,
        
        # Restricted fields
        "salary": DataSensitivity.RESTRICTED,
        "performance_rating": DataSensitivity.RESTRICTED,
        "personal_address": DataSensitivity.RESTRICTED,
        "phone_number": DataSensitivity.RESTRICTED,
    }
    
    def classify_field(self, field_name: str) -> DataSensitivity:
        """Classify the sensitivity of a field."""
        return self.FIELD_SENSITIVITY.get(field_name, DataSensitivity.INTERNAL)
    
    def classify_resource(self, resource_type: str) -> DataSensitivity:
        """Classify the sensitivity of a resource type."""
        resource_sensitivity = {
            "Employee": DataSensitivity.SENSITIVE,
            "Project": DataSensitivity.INTERNAL,
            "Assignment": DataSensitivity.INTERNAL,
            "Report": DataSensitivity.SENSITIVE,
            "AuditLog": DataSensitivity.RESTRICTED,
            "User": DataSensitivity.RESTRICTED,
        }
        return resource_sensitivity.get(resource_type, DataSensitivity.INTERNAL)
    
    def get_accessible_fields(
        self,
        role: UserRole,
        resource_type: str
    ) -> List[str]:
        """Get list of fields accessible to a role for a resource type."""
        max_sensitivity = self._get_max_sensitivity_for_role(role)
        
        accessible = []
        for field, sensitivity in self.FIELD_SENSITIVITY.items():
            if self._sensitivity_level(sensitivity) <= self._sensitivity_level(max_sensitivity):
                accessible.append(field)
        
        return accessible
    
    def _get_max_sensitivity_for_role(self, role: UserRole) -> DataSensitivity:
        """Get maximum data sensitivity level accessible to a role."""
        role_max_sensitivity = {
            UserRole.ADMIN: DataSensitivity.RESTRICTED,
            UserRole.HR: DataSensitivity.RESTRICTED,
            UserRole.CAPABILITY_PARTNER: DataSensitivity.SENSITIVE,
            UserRole.LINE_MANAGER: DataSensitivity.SENSITIVE,
            UserRole.EMPLOYEE: DataSensitivity.INTERNAL,
        }
        return role_max_sensitivity.get(role, DataSensitivity.PUBLIC)
    
    def _sensitivity_level(self, sensitivity: DataSensitivity) -> int:
        """Convert sensitivity to numeric level for comparison."""
        levels = {
            DataSensitivity.PUBLIC: 0,
            DataSensitivity.INTERNAL: 1,
            DataSensitivity.SENSITIVE: 2,
            DataSensitivity.RESTRICTED: 3,
        }
        return levels.get(sensitivity, 0)


class AccessLogger:
    """Logs sensitive data access for audit trails."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
        self._log_buffer: List[AccessLogEntry] = []
    
    def log_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: str,
        action: str,
        data_sensitivity: DataSensitivity,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> bool:
        """Log an access event."""
        entry = AccessLogEntry(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            data_sensitivity=data_sensitivity,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint
        )
        
        if self.db:
            log = AccessLog(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                data_sensitivity=data_sensitivity.value,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                accessed_at=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()
        else:
            self._log_buffer.append(entry)
        
        return True
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccessLogEntry]:
        """Retrieve access logs with optional filters."""
        if not self.db:
            return self._log_buffer
        
        query = self.db.query(AccessLog)
        
        if user_id:
            query = query.filter(AccessLog.user_id == user_id)
        if resource_type:
            query = query.filter(AccessLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AccessLog.accessed_at >= start_date)
        if end_date:
            query = query.filter(AccessLog.accessed_at <= end_date)
        
        logs = query.all()
        return [
            AccessLogEntry(
                user_id=log.user_id,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                data_sensitivity=DataSensitivity(log.data_sensitivity),
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                endpoint=log.endpoint
            )
            for log in logs
        ]


class PermissionEngine:
    """Enforces access permissions in real-time."""
    
    def __init__(
        self,
        db: Optional[Session] = None,
        role_manager: Optional[RoleManager] = None,
        data_classifier: Optional[DataClassifier] = None,
        access_logger: Optional[AccessLogger] = None
    ):
        """Initialize with dependencies."""
        self.db = db
        self.role_manager = role_manager or RoleManager(db)
        self.data_classifier = data_classifier or DataClassifier()
        self.access_logger = access_logger or AccessLogger(db)
    
    def check_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if a user has access to a resource.
        
        Returns:
            Tuple of (has_access, reason)
        """
        role = self.role_manager.get_user_role(user_id)
        
        # Map action to permission
        permission = self._action_to_permission(action, resource_type)
        
        # Check permission
        has_permission = self.role_manager.has_permission(role, permission)
        
        # Get data sensitivity
        sensitivity = self.data_classifier.classify_resource(resource_type)
        
        # Log the access attempt
        self.access_logger.log_access(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            data_sensitivity=sensitivity,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not has_permission:
            return False, f"Role {role.value} does not have permission {permission.value}"
        
        return True, "Access granted"
    
    def get_accessible_employees(
        self,
        user_id: int,
        capability: Optional[str] = None
    ) -> List[int]:
        """Get list of employee IDs accessible to a user."""
        if not self.db:
            return []
        
        role = self.role_manager.get_user_role(user_id)
        
        # Admin and HR can see all
        if role in [UserRole.ADMIN, UserRole.HR]:
            query = self.db.query(Employee.id)
            if capability:
                query = query.filter(Employee.capability == capability)
            return [e.id for e in query.all()]
        
        # Capability partner can see their capability
        if role == UserRole.CAPABILITY_PARTNER:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.employee_id:
                employee = self.db.query(Employee).filter(
                    Employee.employee_id == user.employee_id
                ).first()
                if employee and employee.capability:
                    return [
                        e.id for e in self.db.query(Employee.id).filter(
                            Employee.capability == employee.capability
                        ).all()
                    ]
            return []
        
        # Line manager can see their team
        if role == UserRole.LINE_MANAGER:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.employee_id:
                employee = self.db.query(Employee).filter(
                    Employee.employee_id == user.employee_id
                ).first()
                if employee:
                    return [
                        e.id for e in self.db.query(Employee.id).filter(
                            Employee.line_manager_id == employee.id
                        ).all()
                    ] + [employee.id]
            return []
        
        # Employee can only see themselves
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.employee_id:
            employee = self.db.query(Employee).filter(
                Employee.employee_id == user.employee_id
            ).first()
            if employee:
                return [employee.id]
        
        return []
    
    def _action_to_permission(self, action: str, resource_type: str) -> Permission:
        """Map an action to a permission."""
        action_lower = action.lower()
        
        if action_lower in ["view", "read", "get"]:
            return Permission.VIEW_OWN_DATA
        elif action_lower in ["edit", "update", "patch"]:
            return Permission.EDIT_OWN_DATA
        elif action_lower in ["delete", "remove"]:
            return Permission.EDIT_ALL_DATA
        elif action_lower in ["export"]:
            return Permission.EXPORT_DATA
        elif action_lower in ["approve"]:
            return Permission.APPROVE_LEVEL_MOVEMENT
        
        return Permission.VIEW_OWN_DATA


# Factory functions
def get_role_manager(db: Session) -> RoleManager:
    """Create a RoleManager instance."""
    return RoleManager(db)


def get_permission_engine(db: Session) -> PermissionEngine:
    """Create a PermissionEngine instance."""
    return PermissionEngine(db)

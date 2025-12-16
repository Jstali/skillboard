"""
Audit Logging Service for GDPR compliance and sensitive operations tracking.
Logs all sensitive data access and critical operations.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
import json
from app.db.models import AuditLog, User


class AuditLogger:
    """Service for logging audit events"""
    
    @staticmethod
    def log(
        db: Session,
        user_id: Optional[int],
        action: str,
        target_id: Optional[int] = None,
        target_type: Optional[str] = None,
        accessed_fields: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log an audit event.
        
        Args:
            db: Database session
            user_id: ID of user performing the action
            action: Description of the action (e.g., "view_employee_data", "update_role")
            target_id: ID of the target entity
            target_type: Type of target entity (e.g., "employee", "user", "project")
            accessed_fields: Dictionary of fields accessed/modified
            ip_address: IP address of the request
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            target_id=target_id,
            target_type=target_type,
            accessed_fields=json.dumps(accessed_fields) if accessed_fields else None,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_log)
        db.commit()
    
    @staticmethod
    def log_employee_access(
        db: Session,
        user_id: int,
        employee_id: int,
        fields_accessed: list,
        ip_address: Optional[str] = None
    ):
        """Log access to employee data (GDPR sensitive)"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action="view_employee_data",
            target_id=employee_id,
            target_type="employee",
            accessed_fields={"fields": fields_accessed},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_role_change(
        db: Session,
        user_id: int,
        target_user_id: int,
        old_role: Optional[str],
        new_role: str,
        ip_address: Optional[str] = None
    ):
        """Log role changes for security tracking"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action="change_user_role",
            target_id=target_user_id,
            target_type="user",
            accessed_fields={
                "old_role": old_role,
                "new_role": new_role
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_level_movement_approval(
        db: Session,
        user_id: int,
        request_id: int,
        action: str,  # "approve" or "reject"
        stage: str,   # "manager", "cp", "hr"
        ip_address: Optional[str] = None
    ):
        """Log level movement approvals"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action=f"level_movement_{action}",
            target_id=request_id,
            target_type="level_movement_request",
            accessed_fields={
                "approval_stage": stage,
                "action": action
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_project_assignment(
        db: Session,
        user_id: int,
        employee_id: int,
        project_id: int,
        action: str,  # "assign" or "unassign"
        ip_address: Optional[str] = None
    ):
        """Log project assignments"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action=f"project_{action}",
            target_id=employee_id,
            target_type="employee_project_assignment",
            accessed_fields={
                "project_id": project_id,
                "action": action
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_manager_assignment(
        db: Session,
        user_id: int,
        employee_id: int,
        manager_id: int,
        ip_address: Optional[str] = None
    ):
        """Log line manager assignments"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action="assign_line_manager",
            target_id=employee_id,
            target_type="employee",
            accessed_fields={
                "manager_id": manager_id
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_capability_owner_assignment(
        db: Session,
        user_id: int,
        employee_id: int,
        capability_owner_id: int,
        ip_address: Optional[str] = None
    ):
        """Log capability owner assignments"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action="assign_capability_owner",
            target_id=employee_id,
            target_type="employee",
            accessed_fields={
                "capability_owner_id": capability_owner_id
            },
            ip_address=ip_address
        )
    
    @staticmethod
    def log_skill_gap_access(
        db: Session,
        user_id: int,
        employee_id: int,
        ip_address: Optional[str] = None
    ):
        """Log access to skill gap analysis (sensitive performance data)"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action="view_skill_gaps",
            target_id=employee_id,
            target_type="employee",
            accessed_fields={"data_type": "skill_gap_analysis"},
            ip_address=ip_address
        )
    
    @staticmethod
    def log_bulk_upload(
        db: Session,
        user_id: int,
        upload_type: str,  # "employees", "org_structure", "skills"
        rows_processed: int,
        ip_address: Optional[str] = None
    ):
        """Log bulk data uploads"""
        AuditLogger.log(
            db=db,
            user_id=user_id,
            action=f"bulk_upload_{upload_type}",
            target_type="bulk_operation",
            accessed_fields={
                "upload_type": upload_type,
                "rows_processed": rows_processed
            },
            ip_address=ip_address
        )


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request.
    Handles proxy headers (X-Forwarded-For, X-Real-IP).
    """
    # Check for proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return None

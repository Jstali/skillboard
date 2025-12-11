"""
Audit Logs API endpoints for viewing and querying audit logs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db import database
from app.db.models import AuditLog, User
from app.schemas import AuditLog as AuditLogSchema
from app.api.rbac import require_role
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=List[AuditLogSchema])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    target_id: Optional[int] = Query(None, description="Filter by target ID"),
    days: Optional[int] = Query(7, description="Number of days to look back"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    Query audit logs.
    Requires: System Admin or HR role
    
    Filters:
    - user_id: Filter by user who performed the action
    - action: Filter by action type (e.g., "view_employee_data")
    - target_type: Filter by target entity type (e.g., "employee")
    - target_id: Filter by specific target entity ID
    - days: Number of days to look back (default: 7)
    - limit: Maximum results (default: 100, max: 1000)
    """
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = db.query(AuditLog).filter(AuditLog.timestamp >= date_threshold)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    
    if target_id:
        query = query.filter(AuditLog.target_id == target_id)
    
    # Order by most recent first
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Apply limit
    audit_logs = query.limit(limit).all()
    
    return audit_logs


@router.get("/employee/{employee_id}", response_model=List[AuditLogSchema])
async def get_employee_audit_logs(
    employee_id: int,
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    Get all audit logs related to a specific employee.
    Includes: data access, role changes, project assignments, etc.
    Requires: System Admin or HR role
    """
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    audit_logs = db.query(AuditLog).filter(
        AuditLog.target_type == "employee",
        AuditLog.target_id == employee_id,
        AuditLog.timestamp >= date_threshold
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return audit_logs


@router.get("/actions", response_model=List[str])
async def get_available_actions(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    Get list of all available action types in audit logs.
    Useful for filtering.
    Requires: System Admin or HR role
    """
    actions = db.query(AuditLog.action).distinct().all()
    return [action[0] for action in actions if action[0]]


@router.get("/target-types", response_model=List[str])
async def get_available_target_types(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    Get list of all available target types in audit logs.
    Useful for filtering.
    Requires: System Admin or HR role
    """
    target_types = db.query(AuditLog.target_type).distinct().all()
    return [tt[0] for tt in target_types if tt[0]]


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin", "HR"))
):
    """
    Get audit log statistics.
    Requires: System Admin or HR role
    """
    from sqlalchemy import func
    
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Total logs
    total_logs = db.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= date_threshold
    ).scalar()
    
    # Logs by action
    logs_by_action = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= date_threshold
    ).group_by(AuditLog.action).all()
    
    # Logs by user
    logs_by_user = db.query(
        AuditLog.user_id,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= date_threshold
    ).group_by(AuditLog.user_id).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    
    # Sensitive data access count
    sensitive_access = db.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= date_threshold,
        AuditLog.action.in_([
            'view_employee_data',
            'view_skill_gaps',
            'change_user_role'
        ])
    ).scalar()
    
    return {
        "period_days": days,
        "total_logs": total_logs,
        "sensitive_access_count": sensitive_access,
        "logs_by_action": [
            {"action": action, "count": count}
            for action, count in logs_by_action
        ],
        "top_users": [
            {"user_id": user_id, "log_count": count}
            for user_id, count in logs_by_user
        ]
    }

"""API routes for HRMS integration."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

from app.db import database, crud
from app.db.models import Employee, User, HRMSImportLog
from app.api.dependencies import get_current_active_user, get_admin_user
from app.services.hrms_client import hrms_client, HRMSClientError
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/hrms", tags=["hrms"])


@router.get("/health")
async def check_hrms_health(
    current_user: User = Depends(get_admin_user),
):
    """Check if HRMS API is accessible."""
    try:
        is_healthy = await hrms_client.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "hrms_url": hrms_client.base_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "hrms_url": hrms_client.base_url,
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/employees")
async def fetch_hrms_employees(
    current_user: User = Depends(get_admin_user),
):
    """Fetch all employees from HRMS (preview only, no import)."""
    try:
        employees = await hrms_client.get_all_employees()
        return {
            "count": len(employees),
            "employees": employees,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.post("/sync/employees")
async def sync_employees_from_hrms(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Sync employees from HRMS to Skillboard database."""
    try:
        # Fetch employees from HRMS
        hrms_employees = await hrms_client.get_all_employees()
        
        stats = {
            "total": len(hrms_employees),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }
        
        for hrms_emp in hrms_employees:
            try:
                # Map HRMS fields to Skillboard Employee model
                employee_id = hrms_emp.get("company_employee_id") or str(hrms_emp.get("employeeId"))
                email = hrms_emp.get("email")
                name = hrms_emp.get("name", "")
                
                if not employee_id:
                    stats["skipped"] += 1
                    continue
                
                # Split name into first/last
                name_parts = name.split(" ", 1) if name else ["", ""]
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Check if employee exists
                existing = crud.get_employee_by_id(db, employee_id)
                
                employee_data = {
                    "employee_id": employee_id,
                    "name": name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "company_email": email,
                    "role": hrms_emp.get("role", "Employee"),
                    "hrms_employee_id": str(hrms_emp.get("employeeId")),
                    "hrms_last_sync": datetime.utcnow(),
                    "is_active": True,
                }
                
                if existing:
                    # Update existing employee
                    for key, value in employee_data.items():
                        if value is not None:
                            setattr(existing, key, value)
                    db.commit()
                    stats["updated"] += 1
                else:
                    # Create new employee
                    new_employee = Employee(**employee_data)
                    db.add(new_employee)
                    db.commit()
                    stats["created"] += 1
                    
            except Exception as e:
                stats["errors"].append(f"{employee_id}: {str(e)}")
                db.rollback()
        
        # Log the import
        import_log = HRMSImportLog(
            import_type="employees",
            import_timestamp=datetime.utcnow(),
            status="completed",
            records_processed=stats["total"],
            records_created=stats["created"],
            records_updated=stats["updated"],
            records_failed=len(stats["errors"]),
            error_details="\n".join(stats["errors"]) if stats["errors"] else None
        )
        db.add(import_log)
        db.commit()
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.post("/sync/employees-with-users")
async def sync_employees_and_create_users(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Sync employees from HRMS and create user accounts with temporary passwords."""
    try:
        # Fetch employees from HRMS
        hrms_employees = await hrms_client.get_all_employees()
        
        stats = {
            "total": len(hrms_employees),
            "employees_created": 0,
            "employees_updated": 0,
            "users_created": 0,
            "skipped": 0,
            "errors": []
        }
        
        created_users = []
        
        for hrms_emp in hrms_employees:
            try:
                employee_id = hrms_emp.get("company_employee_id") or str(hrms_emp.get("employeeId"))
                email = hrms_emp.get("email")
                name = hrms_emp.get("name", "")
                
                if not employee_id or not email:
                    stats["skipped"] += 1
                    continue
                
                # Split name
                name_parts = name.split(" ", 1) if name else ["", ""]
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Upsert employee
                existing_emp = crud.get_employee_by_id(db, employee_id)
                
                employee_data = {
                    "employee_id": employee_id,
                    "name": name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "company_email": email,
                    "role": hrms_emp.get("role", "Employee"),
                    "hrms_employee_id": str(hrms_emp.get("employeeId")),
                    "hrms_last_sync": datetime.utcnow(),
                    "is_active": True,
                }
                
                if existing_emp:
                    for key, value in employee_data.items():
                        if value is not None:
                            setattr(existing_emp, key, value)
                    db.commit()
                    stats["employees_updated"] += 1
                else:
                    new_employee = Employee(**employee_data)
                    db.add(new_employee)
                    db.commit()
                    stats["employees_created"] += 1
                
                # Check if user exists
                existing_user = crud.get_user_by_email(db, email)
                if not existing_user:
                    # Create user with default password (employee_id)
                    temp_password = employee_id  # Use employee_id as temp password
                    password_hash = get_password_hash(temp_password)
                    
                    user_dict = {
                        "email": email,
                        "password_hash": password_hash,
                        "employee_id": employee_id,
                        "is_active": True,
                        "is_admin": False,
                        "must_change_password": True,
                    }
                    
                    new_user = crud.create_user(db, user_dict)
                    stats["users_created"] += 1
                    created_users.append({
                        "email": email,
                        "employee_id": employee_id,
                        "name": name,
                        "temp_password": temp_password
                    })
                    
            except Exception as e:
                stats["errors"].append(f"{employee_id}: {str(e)}")
                db.rollback()
        
        return {
            "status": "success",
            "stats": stats,
            "created_users": created_users,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.get("/projects")
async def fetch_hrms_projects(
    current_user: User = Depends(get_admin_user),
):
    """Fetch all projects from HRMS."""
    try:
        projects = await hrms_client.get_all_projects()
        return {
            "count": len(projects),
            "projects": projects,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.get("/managers")
async def fetch_hrms_managers(
    current_user: User = Depends(get_admin_user),
):
    """Fetch all managers from HRMS."""
    try:
        managers = await hrms_client.get_managers_list()
        return {
            "count": len(managers),
            "managers": managers,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


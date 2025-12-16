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


@router.get("/test-manager-employees/{manager_email}")
async def test_manager_employees(
    manager_email: str,
    current_user: User = Depends(get_current_active_user),
):
    """Test endpoint to fetch employees for a manager by email."""
    try:
        print(f"[HRMS_TEST] Testing manager employees for: {manager_email}", flush=True)
        print(f"[HRMS_TEST] HRMS base URL: {hrms_client.base_url}", flush=True)
        
        employees = await hrms_client.get_employees_by_manager_email(manager_email)
        
        return {
            "manager_email": manager_email,
            "hrms_url": hrms_client.base_url,
            "employee_count": len(employees),
            "employees": employees,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        return {
            "status": "error",
            "error": str(e),
            "manager_email": manager_email,
            "hrms_url": hrms_client.base_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "manager_email": manager_email,
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


@router.get("/locations")
async def fetch_hrms_locations(
    current_user: User = Depends(get_admin_user),
):
    """Fetch all locations from HRMS."""
    try:
        locations = await hrms_client.get_all_locations()
        return {
            "count": len(locations),
            "locations": locations,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.get("/delivery-managers")
async def fetch_hrms_delivery_managers(
    current_user: User = Depends(get_admin_user),
):
    """Fetch all delivery managers from HRMS (managers assigned by location)."""
    try:
        managers = await hrms_client.get_delivery_managers()
        return {
            "count": len(managers),
            "delivery_managers": managers,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )


@router.post("/create-user-from-hrms")
async def create_user_from_hrms(
    email: str,
    role_id: int = 6,
    password: str = "password123",
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Create a user account from HRMS employee data.
    
    Args:
        email: The employee's email in HRMS
        role_id: Role to assign (1=Admin, 2=HR, 3=CP, 4=DM, 5=LM, 6=Employee)
        password: Password for the new account
    """
    try:
        # First, try to find the employee in HRMS
        hrms_employees = await hrms_client.get_all_employees()
        
        hrms_emp = None
        for emp in hrms_employees:
            if emp.get("email") == email:
                hrms_emp = emp
                break
        
        if not hrms_emp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with email '{email}' not found in HRMS"
            )
        
        # Extract employee data
        employee_id = hrms_emp.get("company_employee_id") or str(hrms_emp.get("id", ""))
        name = hrms_emp.get("name", email.split("@")[0])
        name_parts = name.split(" ", 1) if name else ["", ""]
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Check if employee exists locally
        existing_emp = db.query(Employee).filter(
            (Employee.company_email == email) | (Employee.employee_id == employee_id)
        ).first()
        
        if existing_emp:
            # Update existing employee
            existing_emp.name = name
            existing_emp.first_name = first_name
            existing_emp.last_name = last_name
            existing_emp.company_email = email
            existing_emp.role_id = role_id
            existing_emp.is_active = True
            employee = existing_emp
            employee_action = "updated"
        else:
            # Create new employee
            employee = Employee(
                employee_id=employee_id or f"HRMS_{email.split('@')[0]}",
                name=name,
                first_name=first_name,
                last_name=last_name,
                company_email=email,
                role_id=role_id,
                is_active=True
            )
            db.add(employee)
            employee_action = "created"
        
        db.flush()
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            # Update existing user
            existing_user.employee_id = employee.employee_id
            existing_user.role_id = role_id
            existing_user.is_active = True
            user_action = "updated"
        else:
            # Create new user
            new_user = User(
                email=email,
                employee_id=employee.employee_id,
                password_hash=get_password_hash(password),
                role_id=role_id,
                is_active=True,
                is_admin=False,
                must_change_password=False
            )
            db.add(new_user)
            user_action = "created"
        
        db.commit()
        
        role_names = {1: "Admin", 2: "HR", 3: "CP", 4: "DM", 5: "LM", 6: "Employee"}
        
        return {
            "status": "success",
            "email": email,
            "employee_id": employee.employee_id,
            "name": name,
            "role": role_names.get(role_id, "Unknown"),
            "role_id": role_id,
            "employee_action": employee_action,
            "user_action": user_action,
            "password": password if user_action == "created" else "(unchanged)"
        }
        
    except HTTPException:
        raise
    except HRMSClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HRMS API error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/setup-test-accounts")
async def setup_test_accounts(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Set up test accounts for Line Manager and Delivery Manager.
    Creates users and employees with proper roles.
    """
    DEFAULT_PASSWORD = "12345678"
    
    test_accounts = [
        {
            "email": "linemanager@nxzen.com",
            "employee_id": "LM001",
            "name": "Line Manager",
            "role_id": 5,  # LINE_MANAGER
            "location_id": "LOC001"
        },
        {
            "email": "deliverymanager@nxzen.com",
            "employee_id": "DM001",
            "name": "Delivery Manager",
            "role_id": 4,  # DELIVERY_MANAGER
            "location_id": "LOC001"
        },
        {
            "email": "saivaishnav.thota@nxzen.com",
            "employee_id": "EMP001",
            "name": "Sai Vaishnav Thota",
            "role_id": 6,  # EMPLOYEE
            "location_id": "LOC001",
            "line_manager_id": "LM001"  # Will be linked
        }
    ]
    
    results = []
    employee_map = {}
    
    try:
        # First pass: Create employees and users
        for account in test_accounts:
            email = account["email"]
            employee_id = account["employee_id"]
            
            # Check/create employee
            employee = db.query(Employee).filter(
                (Employee.employee_id == employee_id) | (Employee.company_email == email)
            ).first()
            
            if employee:
                employee.name = account["name"]
                employee.company_email = email
                employee.employee_id = employee_id
                employee.role_id = account["role_id"]
                employee.location_id = account.get("location_id")
                employee.is_active = True
                emp_action = "updated"
            else:
                name_parts = account["name"].split(" ", 1)
                employee = Employee(
                    employee_id=employee_id,
                    name=account["name"],
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else "",
                    company_email=email,
                    role_id=account["role_id"],
                    location_id=account.get("location_id"),
                    is_active=True
                )
                db.add(employee)
                emp_action = "created"
            
            db.flush()
            employee_map[employee_id] = employee
            
            # Check/create user
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                user.employee_id = employee_id
                user.role_id = account["role_id"]
                user.is_active = True
                user_action = "updated"
            else:
                user = User(
                    email=email,
                    employee_id=employee_id,
                    password_hash=get_password_hash(DEFAULT_PASSWORD),
                    role_id=account["role_id"],
                    is_active=True,
                    is_admin=False,
                    must_change_password=False
                )
                db.add(user)
                user_action = "created"
            
            results.append({
                "email": email,
                "employee_id": employee_id,
                "name": account["name"],
                "role_id": account["role_id"],
                "employee_action": emp_action,
                "user_action": user_action
            })
        
        db.flush()
        
        # Second pass: Set up line manager relationships
        for account in test_accounts:
            if "line_manager_id" in account:
                employee = employee_map.get(account["employee_id"])
                manager = employee_map.get(account["line_manager_id"])
                if employee and manager:
                    employee.line_manager_id = manager.id
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Test accounts created successfully",
            "default_password": DEFAULT_PASSWORD,
            "accounts": results
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up test accounts: {str(e)}"
        )

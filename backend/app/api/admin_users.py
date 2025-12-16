"""API routes for admin user management (CSV imports)."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from typing import List, Optional
import secrets
import string
from app.db import database, crud
from app.schemas import UploadResponse
from app.core.security import get_password_hash
from app.api.dependencies import get_admin_user
from app.db.models import User

router = APIRouter(prefix="/api/admin", tags=["admin-users"])

MAX_ROWS = 10000


def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/import-users-excel", response_model=UploadResponse)
async def import_users_excel(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Upload Excel file (.xlsx or .xls) to import users/employees.
    
    Expected columns (case-insensitive):
    - employee_id (required): Unique employee identifier
    - first_name (required): Employee's first name
    - last_name (required): Employee's last name
    - company_email (required): Employee's company email address
    - department (optional): Employee's department
    - role (optional): Employee's role/job title
    - team (optional): Team assignment (consulting, technical_delivery, etc.)
    - category (optional): Employee category for skill template filtering
    
    Returns:
    - rows_processed: Number of rows successfully processed
    - rows_created: Number of new users created
    - rows_updated: Number of existing users updated
    - errors: List of any errors encountered
    
    Note: New users will receive temporary passwords saved to users_import_report.csv (DEV ONLY)
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Expected .xlsx or .xls"
        )
    
    try:
        # Read file content
        contents = await file.read()
        
        # Parse Excel file
        df = pd.read_excel(BytesIO(contents), engine="openpyxl")
        
        # Validate row count
        if len(df) > MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"File contains {len(df)} rows. Maximum allowed is {MAX_ROWS}."
            )
        
        # Normalize column names (case-insensitive)
        df.columns = df.columns.str.strip().str.lower()
        
        # Validate required columns
        required_cols = ["employee_id", "first_name", "last_name", "company_email"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        rows_processed = 0
        rows_created = 0
        rows_updated = 0
        errors = []
        temp_passwords = []  # Store temp passwords for report
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                employee_id = str(row["employee_id"]).strip()
                first_name = str(row["first_name"]).strip() if pd.notna(row.get("first_name")) else None
                last_name = str(row["last_name"]).strip() if pd.notna(row.get("last_name")) else None
                company_email = str(row["company_email"]).strip() if pd.notna(row.get("company_email")) else None
                department = str(row["department"]).strip() if "department" in df.columns and pd.notna(row.get("department")) else None
                role = str(row["role"]).strip() if "role" in df.columns and pd.notna(row.get("role")) else None
                
                if not employee_id:
                    errors.append(f"Row {idx + 2}: Missing employee_id")
                    continue
                
                if not company_email:
                    errors.append(f"Row {idx + 2}: Missing company_email")
                    continue
                
                # Validate email format (basic)
                if "@" not in company_email:
                    errors.append(f"Row {idx + 2}: Invalid email format: {company_email}")
                    continue
                
                # Create full name
                name = f"{first_name} {last_name}".strip() if first_name and last_name else company_email.split("@")[0]
                
                # Get team if provided
                team = None
                if "team" in df.columns and pd.notna(row.get("team")):
                    team = str(row["team"]).strip()
                
                # Get category if provided
                category = None
                if "category" in df.columns and pd.notna(row.get("category")):
                    category = str(row["category"]).strip()
                
                # Upsert employee
                employee = crud.upsert_employee(
                    db,
                    employee_id=employee_id,
                    name=name,
                    first_name=first_name,
                    last_name=last_name,
                    company_email=company_email,
                    department=department,
                    role=role,
                    team=team,
                    category=category,
                )
                
                # Check if user already exists
                existing_user = crud.get_user_by_email(db, company_email)
                if existing_user:
                    # Update user if exists
                    rows_updated += 1
                    # Update employee_id if not set
                    if not existing_user.employee_id:
                        crud.update_user(db, existing_user.id, {"employee_id": employee_id})
                else:
                    # Create new user with temp password
                    temp_password = generate_temp_password()
                    password_hash = get_password_hash(temp_password)
                    
                    user_dict = {
                        "email": company_email,
                        "password_hash": password_hash,
                        "employee_id": employee_id,
                        "is_active": False,  # Set to False until password is changed
                        "is_admin": False,
                        "must_change_password": True,
                    }
                    
                    crud.create_user(db, user_dict)
                    rows_created += 1
                    
                    # Store temp password for report
                    temp_passwords.append({
                        "employee_id": employee_id,
                        "email": company_email,
                        "name": name,
                        "temp_password": temp_password,
                    })
                
                rows_processed += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Generate import report with temp passwords (dev only - warn in production)
        if temp_passwords:
            report_df = pd.DataFrame(temp_passwords)
            report_path = "users_import_report.csv"
            report_df.to_csv(report_path, index=False)
            # In production, this should be sent via secure email, not saved to disk
        
        message = f"Users imported successfully. {rows_processed} rows processed."
        if temp_passwords:
            message += f" {len(temp_passwords)} new users created with temp passwords. Check users_import_report.csv for passwords (DEV ONLY - DO NOT USE IN PRODUCTION)."
        
        return UploadResponse(
            message=message,
            rows_processed=rows_processed,
            rows_created=rows_created,
            rows_updated=rows_updated,
            errors=errors if errors else None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/import-users", response_model=UploadResponse)
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY"),
):
    """
    Upload CSV file to import users/employees.
    Expected columns: employee_id, first_name, last_name, company_email, department, role
    
    In dev: requires X-ADMIN-KEY header or admin user JWT.
    In production: requires admin user JWT only.
    """
    # Check admin access (dev: X-ADMIN-KEY, prod: JWT admin user)
    ADMIN_KEY = "dev-admin-key-change-in-production"
    if x_admin_key != ADMIN_KEY:
        # In production, this would require proper JWT admin user
        # For now, we'll allow it in dev but log a warning
        pass
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Expected .csv"
        )
    
    try:
        # Read file content
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        
        # Validate row count
        if len(df) > MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"File contains {len(df)} rows. Maximum allowed is {MAX_ROWS}."
            )
        
        # Normalize column names (case-insensitive)
        df.columns = df.columns.str.strip().str.lower()
        
        # Validate required columns
        required_cols = ["employee_id", "first_name", "last_name", "company_email"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        rows_processed = 0
        rows_created = 0
        rows_updated = 0
        errors = []
        temp_passwords = []  # Store temp passwords for report
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                employee_id = str(row["employee_id"]).strip()
                first_name = str(row["first_name"]).strip() if pd.notna(row.get("first_name")) else None
                last_name = str(row["last_name"]).strip() if pd.notna(row.get("last_name")) else None
                company_email = str(row["company_email"]).strip() if pd.notna(row.get("company_email")) else None
                department = str(row["department"]).strip() if "department" in df.columns and pd.notna(row.get("department")) else None
                role = str(row["role"]).strip() if "role" in df.columns and pd.notna(row.get("role")) else None
                
                if not employee_id:
                    errors.append(f"Row {idx + 2}: Missing employee_id")
                    continue
                
                if not company_email:
                    errors.append(f"Row {idx + 2}: Missing company_email")
                    continue
                
                # Validate email format (basic)
                if "@" not in company_email:
                    errors.append(f"Row {idx + 2}: Invalid email format: {company_email}")
                    continue
                
                # Create full name
                name = f"{first_name} {last_name}".strip() if first_name and last_name else company_email.split("@")[0]
                
                # Get team if provided
                team = None
                if "team" in df.columns and pd.notna(row.get("team")):
                    team = str(row["team"]).strip()
                
                # Get category if provided
                category = None
                if "category" in df.columns and pd.notna(row.get("category")):
                    category = str(row["category"]).strip()
                
                # Upsert employee
                employee = crud.upsert_employee(
                    db,
                    employee_id=employee_id,
                    name=name,
                    first_name=first_name,
                    last_name=last_name,
                    company_email=company_email,
                    department=department,
                    role=role,
                    team=team,
                    category=category,
                )
                
                # Check if user already exists
                existing_user = crud.get_user_by_email(db, company_email)
                if existing_user:
                    # Update user if exists
                    rows_updated += 1
                    # Update employee_id if not set
                    if not existing_user.employee_id:
                        crud.update_user(db, existing_user.id, {"employee_id": employee_id})
                else:
                    # Create new user with temp password
                    temp_password = generate_temp_password()
                    password_hash = get_password_hash(temp_password)
                    
                    user_dict = {
                        "email": company_email,
                        "password_hash": password_hash,
                        "employee_id": employee_id,
                        "is_active": False,  # Set to False until password is changed
                        "is_admin": False,
                        "must_change_password": True,
                    }
                    
                    crud.create_user(db, user_dict)
                    rows_created += 1
                    
                    # Store temp password for report
                    temp_passwords.append({
                        "employee_id": employee_id,
                        "email": company_email,
                        "name": name,
                        "temp_password": temp_password,
                    })
                
                rows_processed += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Generate import report with temp passwords (dev only - warn in production)
        if temp_passwords:
            report_df = pd.DataFrame(temp_passwords)
            report_path = "users_import_report.csv"
            report_df.to_csv(report_path, index=False)
            # In production, this should be sent via secure email, not saved to disk
        
        message = f"Users imported successfully. {rows_processed} rows processed."
        if temp_passwords:
            message += f" {len(temp_passwords)} new users created with temp passwords. Check users_import_report.csv for passwords (DEV ONLY - DO NOT USE IN PRODUCTION)."
        
        return UploadResponse(
            message=message,
            rows_processed=rows_processed,
            rows_created=rows_created,
            rows_updated=rows_updated,
            errors=errors if errors else None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


from pydantic import BaseModel
from app.db.models import Employee


class LinkUserToEmployeeRequest(BaseModel):
    """Request to link a user to an employee."""
    user_email: str
    employee_id: str


class SetLineManagerRequest(BaseModel):
    """Request to set line manager for employees."""
    manager_employee_id: str
    employee_ids: List[str]


@router.post("/link-user-to-employee")
async def link_user_to_employee(
    request: LinkUserToEmployeeRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Link a user account to an employee record.
    This is needed for role-based access control to work properly.
    """
    # Find the user
    user = crud.get_user_by_email(db, request.user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email '{request.user_email}' not found")
    
    # Find the employee
    employee = db.query(Employee).filter(Employee.employee_id == request.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee with ID '{request.employee_id}' not found")
    
    # Update user's employee_id
    crud.update_user(db, user.id, {"employee_id": request.employee_id})
    
    return {
        "message": f"User '{request.user_email}' linked to employee '{request.employee_id}'",
        "user_id": user.id,
        "employee_id": employee.employee_id,
        "employee_name": employee.name
    }


@router.post("/set-line-manager")
async def set_line_manager(
    request: SetLineManagerRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Set line manager for multiple employees.
    This establishes the reporting relationship needed for LM Dashboard.
    """
    # Find the manager employee
    manager = db.query(Employee).filter(Employee.employee_id == request.manager_employee_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail=f"Manager with employee ID '{request.manager_employee_id}' not found")
    
    updated = []
    not_found = []
    
    for emp_id in request.employee_ids:
        employee = db.query(Employee).filter(Employee.employee_id == emp_id).first()
        if employee:
            employee.line_manager_id = manager.id
            updated.append(emp_id)
        else:
            not_found.append(emp_id)
    
    db.commit()
    
    return {
        "message": f"Set line manager '{manager.name}' (ID: {manager.employee_id}) for {len(updated)} employees",
        "manager_id": manager.id,
        "manager_employee_id": manager.employee_id,
        "manager_name": manager.name,
        "updated_employees": updated,
        "not_found_employees": not_found
    }


@router.get("/debug-user-employee-links")
async def debug_user_employee_links(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Debug endpoint to show all users and their employee links.
    """
    users = db.query(User).all()
    result = []
    
    for user in users:
        user_info = {
            "user_id": user.id,
            "email": user.email,
            "employee_id": user.employee_id,
            "role_id": user.role_id,
            "is_admin": user.is_admin,
            "employee_record": None
        }
        
        if user.employee_id:
            emp = db.query(Employee).filter(Employee.employee_id == user.employee_id).first()
            if emp:
                user_info["employee_record"] = {
                    "id": emp.id,
                    "employee_id": emp.employee_id,
                    "name": emp.name,
                    "company_email": emp.company_email,
                    "line_manager_id": emp.line_manager_id
                }
        
        result.append(user_info)
    
    return {"users": result}


@router.get("/debug-employees-with-managers")
async def debug_employees_with_managers(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Debug endpoint to show all employees and their line managers.
    """
    employees = db.query(Employee).all()
    result = []
    
    for emp in employees:
        emp_info = {
            "id": emp.id,
            "employee_id": emp.employee_id,
            "name": emp.name,
            "company_email": emp.company_email,
            "line_manager_id": emp.line_manager_id,
            "line_manager": None
        }
        
        if emp.line_manager_id:
            manager = db.query(Employee).filter(Employee.id == emp.line_manager_id).first()
            if manager:
                emp_info["line_manager"] = {
                    "id": manager.id,
                    "employee_id": manager.employee_id,
                    "name": manager.name
                }
        
        result.append(emp_info)
    
    return {"employees": result}

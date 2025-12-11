"""
Organizational Structure API endpoints for HRMS pre-integration.
Manages employee hierarchy, line managers, and reporting structure.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import database
from app.db.models import OrgStructure, Employee, User
from app.schemas import (
    OrgStructure as OrgStructureSchema,
    OrgStructureCreate,
    Employee as EmployeeSchema
)
from app.api.rbac import require_role, require_hr, get_user_role
from app.api.dependencies import get_current_user
import pandas as pd
import io

router = APIRouter(prefix="/api/org-structure", tags=["org-structure"])


@router.post("/assign-manager")
async def assign_line_manager(
    employee_id: int,
    manager_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Assign a line manager to an employee.
    Requires: HR or System Admin role
    """
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Verify manager exists
    manager = db.query(Employee).filter(Employee.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Prevent self-assignment
    if employee_id == manager_id:
        raise HTTPException(status_code=400, detail="Employee cannot be their own manager")
    
    # Update employee's line manager
    employee.line_manager_id = manager_id
    
    # Update or create org structure entry
    org_entry = db.query(OrgStructure).filter(
        OrgStructure.employee_id == employee_id
    ).first()
    
    if org_entry:
        org_entry.manager_id = manager_id
    else:
        org_entry = OrgStructure(
            employee_id=employee_id,
            manager_id=manager_id
        )
        db.add(org_entry)
    
    db.commit()
    return {"message": "Line manager assigned successfully"}


@router.post("/upload")
async def upload_org_structure(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Upload organizational structure from Excel/CSV file.
    Expected columns: employee_id, manager_id, level (optional)
    Requires: HR or System Admin role
    """
    try:
        contents = await file.read()
        
        # Read file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_cols = ['employee_id', 'manager_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        processed = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                emp_id = str(row['employee_id']).strip()
                mgr_id = str(row['manager_id']).strip() if pd.notna(row['manager_id']) else None
                level = int(row['level']) if 'level' in df.columns and pd.notna(row['level']) else None
                
                # Find employee by employee_id
                employee = db.query(Employee).filter(
                    Employee.employee_id == emp_id
                ).first()
                
                if not employee:
                    errors.append(f"Row {idx + 2}: Employee {emp_id} not found")
                    continue
                
                # Find manager if provided
                manager = None
                if mgr_id:
                    manager = db.query(Employee).filter(
                        Employee.employee_id == mgr_id
                    ).first()
                    
                    if not manager:
                        errors.append(f"Row {idx + 2}: Manager {mgr_id} not found")
                        continue
                
                # Update employee's line manager
                employee.line_manager_id = manager.id if manager else None
                
                # Update or create org structure
                org_entry = db.query(OrgStructure).filter(
                    OrgStructure.employee_id == employee.id
                ).first()
                
                if org_entry:
                    org_entry.manager_id = manager.id if manager else None
                    org_entry.level = level
                else:
                    org_entry = OrgStructure(
                        employee_id=employee.id,
                        manager_id=manager.id if manager else None,
                        level=level
                    )
                    db.add(org_entry)
                
                processed += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        db.commit()
        
        return {
            "message": "Org structure uploaded successfully",
            "rows_processed": processed,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.get("", response_model=List[OrgStructureSchema])
async def get_org_structure(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Get complete organizational structure.
    Requires: HR or System Admin role
    """
    org_structure = db.query(OrgStructure).all()
    return org_structure


@router.get("/employees/{employee_id}/direct-reports", response_model=List[EmployeeSchema])
async def get_direct_reports(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all direct reports for an employee.
    Access controlled by RBAC.
    """
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if user can view this data
    role_name = get_user_role(current_user, db)
    current_employee = db.query(Employee).filter(
        Employee.employee_id == current_user.employee_id
    ).first()
    
    # Only allow if:
    # 1. System Admin or HR
    # 2. The employee themselves (viewing their team)
    # 3. Line Manager viewing their reports
    if role_name not in ["System Admin", "HR"]:
        if not current_employee or current_employee.id != employee_id:
            # Check if current user is this employee's manager
            if not current_employee or employee.line_manager_id != current_employee.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this employee's direct reports"
                )
    
    # Get direct reports
    direct_reports = db.query(Employee).filter(
        Employee.line_manager_id == employee_id
    ).all()
    
    return direct_reports


@router.get("/employees/{employee_id}/hierarchy")
async def get_employee_hierarchy(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get employee's position in organizational hierarchy.
    Returns: manager chain (upwards) and direct reports (downwards)
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get manager chain (upwards)
    manager_chain = []
    current = employee
    visited = set()  # Prevent infinite loops
    
    while current.line_manager_id and current.line_manager_id not in visited:
        visited.add(current.id)
        manager = db.query(Employee).filter(Employee.id == current.line_manager_id).first()
        if manager:
            manager_chain.append({
                "id": manager.id,
                "employee_id": manager.employee_id,
                "name": manager.name,
                "role": manager.role,
                "department": manager.department
            })
            current = manager
        else:
            break
    
    # Get direct reports
    direct_reports = db.query(Employee).filter(
        Employee.line_manager_id == employee_id
    ).all()
    
    return {
        "employee": {
            "id": employee.id,
            "employee_id": employee.employee_id,
            "name": employee.name,
            "role": employee.role,
            "department": employee.department
        },
        "manager_chain": manager_chain,
        "direct_reports": [
            {
                "id": emp.id,
                "employee_id": emp.employee_id,
                "name": emp.name,
                "role": emp.role,
                "department": emp.department
            }
            for emp in direct_reports
        ]
    }

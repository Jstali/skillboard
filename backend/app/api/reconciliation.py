"""API endpoints for Reconciliation.

Provides endpoints for comparing skill board and HRMS assignments,
identifying discrepancies, and generating reports with role-based access.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.db.database import get_db
from app.db.models import Employee, User
from app.services.reconciliation_service import (
    ReconciliationService, ReconciliationResult, ReconciliationReport,
    Discrepancy, get_reconciliation_service
)
from app.services.financial_filter import financial_filter
from app.api.dependencies import get_current_user, get_hr_or_admin_user
from app.core.permissions import RoleID

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])


@router.get("/compare/{employee_id}", response_model=ReconciliationResult)
async def compare_employee_assignments(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_or_admin_user)
):
    """
    Compare skill board and HRMS assignments for an employee.
    
    Returns comparison result with any discrepancies identified.
    
    Access: HR and Admin only
    """
    service = get_reconciliation_service(db)
    result = service.get_employee_reconciliation(employee_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found"
        )
    
    return result


@router.get("/discrepancies", response_model=List[Discrepancy])
async def get_all_discrepancies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_or_admin_user)
):
    """
    Get all discrepancies across all employees.
    
    Returns list of all assignment discrepancies.
    
    Access: HR and Admin only
    """
    service = get_reconciliation_service(db)
    
    # Get all employees and check for discrepancies
    all_discrepancies = []
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    for employee in employees:
        result = service.get_employee_reconciliation(employee.employee_id)
        if result and result.discrepancies:
            all_discrepancies.extend(result.discrepancies)
    
    return all_discrepancies


@router.get("/report", response_model=ReconciliationReport)
async def get_reconciliation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_or_admin_user)
):
    """
    Generate a full reconciliation report.
    
    Returns summary and details of all reconciliation results.
    
    Access: HR and Admin only
    """
    service = get_reconciliation_service(db)
    
    # Get all employees and reconcile
    results = []
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    for employee in employees:
        result = service.get_employee_reconciliation(employee.employee_id)
        if result:
            results.append(result)
    
    report = service.generate_reconciliation_report(results)
    return report


@router.get("/export")
async def export_reconciliation_data(
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hr_or_admin_user)
):
    """
    Export reconciliation data.
    
    Returns sanitized export data (no financial information).
    
    Access: HR and Admin only
    """
    service = get_reconciliation_service(db)
    
    # Generate report
    results = []
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    
    for employee in employees:
        result = service.get_employee_reconciliation(employee.employee_id)
        if result:
            results.append(result)
    
    report = service.generate_reconciliation_report(results)
    export_data = service.export_reconciliation_data(report)
    
    if format == "json":
        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=reconciliation_export.json"}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}. Supported formats: json"
        )

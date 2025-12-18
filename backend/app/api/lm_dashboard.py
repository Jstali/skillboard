"""Line Manager Dashboard API endpoints.

Line Managers act as a bridge between clients and employees.
An employee can have MULTIPLE line managers (one per project).
LM sees employees from:
1. Direct reports (Employee.line_manager_id) - primary/default manager
2. Project assignments (EmployeeProjectAssignment.line_manager_id) - project-specific managers
3. HRMS data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db import database
from app.db.models import Employee, EmployeeSkill, User, EmployeeProjectAssignment, Project
from app.api.dependencies import get_current_active_user
from app.services.hrms_client import hrms_client, HRMSClientError
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard/lm", tags=["lm-dashboard"])


class TeamMemberResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    capability: Optional[str] = None
    pathway: Optional[str] = None  # For skill filtering
    band: Optional[str] = None
    skills_count: int = 0
    source: str = "local"  # "local", "hrms", or "project"
    project_name: Optional[str] = None  # If from project assignment

    class Config:
        from_attributes = True


class SkillInfo(BaseModel):
    name: str
    rating: Optional[str] = None


class TeamSkillsResponse(BaseModel):
    employee_id: str
    name: str
    skills: List[SkillInfo]


@router.get("/direct-reports", response_model=List[TeamMemberResponse])
async def get_direct_reports(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get direct reports for the current line manager from both local DB and HRMS."""
    result = []
    seen_employee_ids = set()
    
    # Get manager from local DB if user has employee_id
    manager = None
    if current_user.employee_id:
        manager = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    # If user doesn't have employee_id, try to find employee by email and auto-link
    if not manager:
        emp_by_email = db.query(Employee).filter(Employee.company_email == current_user.email).first()
        if emp_by_email:
            # Auto-link user to employee
            from app.db import crud
            crud.update_user(db, current_user.id, {"employee_id": emp_by_email.employee_id})
            manager = emp_by_email
            logger.info(f"Auto-linked user {current_user.email} to employee {emp_by_email.employee_id}")
    
    # First, get local direct reports (primary line manager relationship)
    if manager:
        local_reports = db.query(Employee).filter(Employee.line_manager_id == manager.id).all()
        for emp in local_reports:
            skills_count = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == emp.id).count()
            result.append(TeamMemberResponse(
                id=emp.id,
                employee_id=emp.employee_id,
                name=emp.name,
                capability=emp.capability or emp.home_capability,
                pathway=emp.pathway,
                band=emp.band,
                skills_count=skills_count,
                source="local",
                project_name=None
            ))
            seen_employee_ids.add(emp.employee_id)
        
        # Also get employees from project assignments where this manager is the line manager
        project_assignments = db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.line_manager_id == manager.id
        ).all()
        
        for assignment in project_assignments:
            emp = assignment.employee
            if emp and emp.employee_id not in seen_employee_ids:
                skills_count = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == emp.id).count()
                project_name = assignment.project.name if assignment.project else None
                result.append(TeamMemberResponse(
                    id=emp.id,
                    employee_id=emp.employee_id,
                    name=emp.name,
                    capability=emp.capability or emp.home_capability,
                    pathway=emp.pathway,
                    band=emp.band,
                    skills_count=skills_count,
                    source="project",
                    project_name=project_name
                ))
                seen_employee_ids.add(emp.employee_id)
    
    # Then, try to get employees from HRMS
    try:
        hrms_employees = await hrms_client.get_employees_by_manager_email(current_user.email)
        logger.info(f"HRMS returned {len(hrms_employees)} employees for {current_user.email}")
        
        for hrms_emp in hrms_employees:
            # HRMS returns: id, name, email, hr, projects
            emp_id = str(hrms_emp.get("id", ""))
            emp_email = hrms_emp.get("email", "")
            emp_name = hrms_emp.get("name", "Unknown")
            
            # Skip if already in local results (by email since HRMS uses different IDs)
            if emp_id in seen_employee_ids:
                continue
            
            # Check if this employee exists in local DB by email
            local_emp = db.query(Employee).filter(Employee.company_email == emp_email).first()
            
            if local_emp:
                # Skip if we already have this employee
                if local_emp.employee_id in seen_employee_ids:
                    continue
                skills_count = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == local_emp.id).count()
                result.append(TeamMemberResponse(
                    id=local_emp.id,
                    employee_id=local_emp.employee_id,
                    name=local_emp.name,
                    capability=local_emp.capability or local_emp.home_capability,
                    pathway=local_emp.pathway,
                    band=local_emp.band,
                    skills_count=skills_count,
                    source="hrms"
                ))
                seen_employee_ids.add(local_emp.employee_id)
            else:
                # Employee only exists in HRMS
                result.append(TeamMemberResponse(
                    id=0,
                    employee_id=emp_id,
                    name=emp_name,
                    capability=hrms_emp.get("capability"),
                    pathway=hrms_emp.get("pathway"),
                    band=hrms_emp.get("band"),
                    skills_count=0,
                    source="hrms"
                ))
                seen_employee_ids.add(emp_id)
            
    except Exception as e:
        logger.error(f"HRMS error: {type(e).__name__}: {e}")
    
    return result


@router.get("/team-skills", response_model=List[TeamSkillsResponse])
async def get_team_skills(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get skills overview for all direct reports (local + HRMS)."""
    # Get manager from local DB
    manager = None
    if current_user.employee_id:
        manager = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    # If user doesn't have employee_id, try to find employee by email
    if not manager:
        manager = db.query(Employee).filter(Employee.company_email == current_user.email).first()
    
    if not manager:
        return []
    
    result = []
    seen_employee_ids = set()
    
    # Get local direct reports
    local_reports = db.query(Employee).filter(Employee.line_manager_id == manager.id).all()
    
    for emp in local_reports:
        employee_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == emp.id
        ).all()
        
        skills = []
        for es in employee_skills:
            if es.skill:
                skills.append(SkillInfo(
                    name=es.skill.name,
                    rating=es.rating.value if es.rating else None
                ))
        
        result.append(TeamSkillsResponse(
            employee_id=emp.employee_id,
            name=emp.name,
            skills=skills
        ))
        seen_employee_ids.add(emp.employee_id)
    
    # Try to get HRMS employees and their skills
    try:
        manager_email = current_user.email
        hrms_employees = await hrms_client.get_employees_by_manager_email(manager_email)
        
        for hrms_emp in hrms_employees:
            emp_id = hrms_emp.get("company_employee_id") or str(hrms_emp.get("employeeId", ""))
            
            if emp_id in seen_employee_ids:
                continue
            
            # Check if employee exists locally
            local_emp = db.query(Employee).filter(Employee.employee_id == emp_id).first()
            
            if local_emp:
                employee_skills = db.query(EmployeeSkill).filter(
                    EmployeeSkill.employee_id == local_emp.id
                ).all()
                
                skills = []
                for es in employee_skills:
                    if es.skill:
                        skills.append(SkillInfo(
                            name=es.skill.name,
                            rating=es.rating.value if es.rating else None
                        ))
                
                result.append(TeamSkillsResponse(
                    employee_id=local_emp.employee_id,
                    name=local_emp.name,
                    skills=skills
                ))
            else:
                # HRMS-only employee, no skills in SkillBoard yet
                result.append(TeamSkillsResponse(
                    employee_id=emp_id,
                    name=hrms_emp.get("name", "Unknown"),
                    skills=[]
                ))
            
            seen_employee_ids.add(emp_id)
            
    except Exception as e:
        logger.warning(f"Error fetching HRMS employees for skills: {e}")
    
    return result


@router.get("/debug-manager-info")
async def debug_manager_info(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Debug endpoint to check manager-employee relationship setup."""
    result = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "employee_id": current_user.employee_id,
            "role_id": current_user.role_id,
            "is_admin": current_user.is_admin
        },
        "manager_employee": None,
        "local_direct_reports": [],
        "project_based_reports": [],
        "hrms_direct_reports": [],
        "all_employees_sample": [],
        "issues": []
    }
    
    # Check if user has employee_id
    if not current_user.employee_id:
        result["issues"].append("User does NOT have an employee_id linked. This is required to find direct reports.")
        
        # Try to find employee by email
        emp_by_email = db.query(Employee).filter(Employee.company_email == current_user.email).first()
        if emp_by_email:
            result["issues"].append(f"Found Employee by email: id={emp_by_email.id}, employee_id={emp_by_email.employee_id}, name={emp_by_email.name}")
            result["issues"].append(f"FIX: Update user.employee_id = '{emp_by_email.employee_id}'")
    else:
        # Find manager's Employee record
        manager_emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
        if not manager_emp:
            result["issues"].append(f"User has employee_id='{current_user.employee_id}' but no Employee record found with that ID")
        else:
            result["manager_employee"] = {
                "id": manager_emp.id,
                "employee_id": manager_emp.employee_id,
                "name": manager_emp.name,
                "company_email": manager_emp.company_email,
                "line_manager_id": manager_emp.line_manager_id
            }
            
            # Find local direct reports (primary line manager)
            local_reports = db.query(Employee).filter(Employee.line_manager_id == manager_emp.id).all()
            for emp in local_reports:
                result["local_direct_reports"].append({
                    "id": emp.id,
                    "employee_id": emp.employee_id,
                    "name": emp.name,
                    "line_manager_id": emp.line_manager_id
                })
            
            # Find project-based reports (line manager per project)
            project_assignments = db.query(EmployeeProjectAssignment).filter(
                EmployeeProjectAssignment.line_manager_id == manager_emp.id
            ).all()
            for assignment in project_assignments:
                emp = assignment.employee
                if emp:
                    result["project_based_reports"].append({
                        "id": emp.id,
                        "employee_id": emp.employee_id,
                        "name": emp.name,
                        "project_id": assignment.project_id,
                        "project_name": assignment.project.name if assignment.project else None
                    })
            
            if not local_reports and not project_assignments:
                result["issues"].append(f"No employees have line_manager_id = {manager_emp.id} (neither direct nor project-based)")
    
    # Show sample of all employees
    all_emps = db.query(Employee).limit(10).all()
    for emp in all_emps:
        result["all_employees_sample"].append({
            "id": emp.id,
            "employee_id": emp.employee_id,
            "name": emp.name,
            "company_email": emp.company_email,
            "line_manager_id": emp.line_manager_id
        })
    
    # Try HRMS
    try:
        hrms_employees = await hrms_client.get_employees_by_manager_email(current_user.email)
        for emp in hrms_employees[:10]:
            result["hrms_direct_reports"].append({
                "id": emp.get("id"),
                "name": emp.get("name"),
                "email": emp.get("email")
            })
    except Exception as e:
        result["issues"].append(f"HRMS error: {type(e).__name__}: {str(e)}")
    
    return result


@router.post("/assign-direct-report")
async def assign_direct_report(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Assign an employee as a direct report to the current manager.
    This sets the employee's line_manager_id to the current user's employee ID.
    """
    # Get manager from local DB
    manager = None
    if current_user.employee_id:
        manager = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    if not manager:
        manager = db.query(Employee).filter(Employee.company_email == current_user.email).first()
        if manager:
            from app.db import crud
            crud.update_user(db, current_user.id, {"employee_id": manager.employee_id})
    
    if not manager:
        return {"success": False, "error": "Manager employee record not found"}
    
    # Find the employee to assign
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return {"success": False, "error": f"Employee with ID {employee_id} not found"}
    
    # Assign the employee to this manager
    old_manager_id = employee.line_manager_id
    employee.line_manager_id = manager.id
    db.commit()
    
    return {
        "success": True,
        "message": f"Assigned {employee.name} as direct report",
        "employee": {
            "id": employee.id,
            "employee_id": employee.employee_id,
            "name": employee.name,
            "old_line_manager_id": old_manager_id,
            "new_line_manager_id": manager.id
        },
        "manager": {
            "id": manager.id,
            "employee_id": manager.employee_id,
            "name": manager.name
        }
    }


@router.post("/sync-hrms-reports")
async def sync_hrms_reports(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Sync direct reports from HRMS to local database.
    This creates/updates local employee records and sets line_manager_id.
    """
    result = {
        "manager_email": current_user.email,
        "synced_employees": [],
        "created_employees": [],
        "errors": []
    }
    
    # Get manager from local DB
    manager = None
    if current_user.employee_id:
        manager = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    # If user doesn't have employee_id, try to find employee by email
    if not manager:
        manager = db.query(Employee).filter(Employee.company_email == current_user.email).first()
        if manager:
            # Auto-link user to employee
            from app.db import crud
            crud.update_user(db, current_user.id, {"employee_id": manager.employee_id})
    
    if not manager:
        result["errors"].append("Manager employee record not found in local database")
        return result
    
    result["manager_id"] = manager.id
    result["manager_employee_id"] = manager.employee_id
    result["manager_name"] = manager.name
    
    # Get employees from HRMS
    try:
        hrms_employees = await hrms_client.get_employees_by_manager_email(current_user.email)
        logger.info(f"HRMS returned {len(hrms_employees)} employees for {current_user.email}")
        
        for hrms_emp in hrms_employees:
            emp_id = str(hrms_emp.get("id", ""))
            emp_email = hrms_emp.get("email", "")
            emp_name = hrms_emp.get("name", "Unknown")
            
            # Try to find employee in local DB by email first, then by ID
            local_emp = None
            if emp_email:
                local_emp = db.query(Employee).filter(Employee.company_email == emp_email).first()
            
            if not local_emp and emp_id:
                local_emp = db.query(Employee).filter(Employee.employee_id == emp_id).first()
            
            if local_emp:
                # Update line_manager_id
                if local_emp.line_manager_id != manager.id:
                    local_emp.line_manager_id = manager.id
                    result["synced_employees"].append({
                        "employee_id": local_emp.employee_id,
                        "name": local_emp.name,
                        "action": "updated_manager"
                    })
            else:
                # Create new employee record
                new_emp = Employee(
                    employee_id=emp_id or f"HRMS_{emp_email.split('@')[0]}",
                    name=emp_name,
                    company_email=emp_email,
                    line_manager_id=manager.id,
                    is_active=True
                )
                db.add(new_emp)
                result["created_employees"].append({
                    "employee_id": new_emp.employee_id,
                    "name": new_emp.name,
                    "email": emp_email
                })
        
        db.commit()
        
    except Exception as e:
        result["errors"].append(f"HRMS error: {type(e).__name__}: {str(e)}")
    
    return result

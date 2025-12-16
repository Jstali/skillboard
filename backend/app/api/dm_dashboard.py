"""Delivery Manager Dashboard API endpoints.

Delivery Managers see employees by LOCATION.
Each location has one Delivery Manager who oversees all employees in that location.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from app.db import database
from app.db.models import Employee, User, EmployeeProjectAssignment, Project
from app.api.dependencies import get_current_active_user
from app.services.hrms_client import hrms_client, HRMSClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard/dm", tags=["dm-dashboard"])


class TeamMemberResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    capability: Optional[str] = None
    band: Optional[str] = None
    location: Optional[str] = None
    projects_count: int = 0

    class Config:
        from_attributes = True


class HRMSProjectResponse(BaseModel):
    id: Optional[int] = None
    project_id: Optional[str] = None
    name: str
    client_name: Optional[str] = None
    status: Optional[str] = None
    manager_name: Optional[str] = None


@router.get("/team-overview", response_model=List[TeamMemberResponse])
def get_team_overview(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get team overview for delivery manager - filtered by LOCATION.
    
    DM sees all employees in their location.
    If DM's location is not set, shows all employees (fallback).
    """
    # Get DM's employee record to find their location
    dm_employee = None
    if current_user.employee_id:
        dm_employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    # If no employee_id, try to find by email
    if not dm_employee:
        dm_employee = db.query(Employee).filter(Employee.company_email == current_user.email).first()
    
    # Get employees based on location
    if dm_employee and dm_employee.location_id:
        # Filter by DM's location
        employees = db.query(Employee).filter(
            Employee.is_active == True,
            Employee.location_id == dm_employee.location_id
        ).all()
        logger.info(f"DM {current_user.email} viewing {len(employees)} employees in location {dm_employee.location_id}")
    else:
        # Fallback: show all employees if location not set
        employees = db.query(Employee).filter(Employee.is_active == True).all()
        logger.warning(f"DM {current_user.email} has no location set, showing all {len(employees)} employees")
    
    result = []
    for emp in employees:
        # Count projects for this employee
        projects_count = db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == emp.id
        ).count()
        
        result.append(TeamMemberResponse(
            id=emp.id,
            employee_id=emp.employee_id,
            name=emp.name,
            capability=emp.capability or emp.home_capability,
            band=emp.band,
            location=emp.location_id,
            projects_count=projects_count
        ))
    
    return result


@router.get("/debug-dm-info")
async def debug_dm_info(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Debug endpoint to check DM's location and employee setup."""
    result = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "employee_id": current_user.employee_id,
            "role_id": current_user.role_id
        },
        "dm_employee": None,
        "location": None,
        "employees_in_location": 0,
        "all_locations": [],
        "issues": []
    }
    
    # Get DM's employee record
    dm_employee = None
    if current_user.employee_id:
        dm_employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    
    if not dm_employee:
        dm_employee = db.query(Employee).filter(Employee.company_email == current_user.email).first()
    
    if dm_employee:
        result["dm_employee"] = {
            "id": dm_employee.id,
            "employee_id": dm_employee.employee_id,
            "name": dm_employee.name,
            "location_id": dm_employee.location_id
        }
        result["location"] = dm_employee.location_id
        
        if dm_employee.location_id:
            count = db.query(Employee).filter(
                Employee.is_active == True,
                Employee.location_id == dm_employee.location_id
            ).count()
            result["employees_in_location"] = count
        else:
            result["issues"].append("DM has no location_id set - showing all employees")
    else:
        result["issues"].append("No employee record found for this user")
    
    # Get all unique locations
    locations = db.query(Employee.location_id).distinct().all()
    result["all_locations"] = [loc[0] for loc in locations if loc[0]]
    
    return result


@router.get("/projects", response_model=List[HRMSProjectResponse])
async def get_hrms_projects(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Fetch all projects - tries HRMS first, falls back to local DB."""
    from app.db.models import Project, HRMSProject
    
    # Try HRMS first
    try:
        projects = await hrms_client.get_all_projects()
        
        result = []
        for proj in projects:
            result.append(HRMSProjectResponse(
                id=proj.get("project_id") or proj.get("id"),
                project_id=str(proj.get("project_id") or proj.get("id", "")),
                name=proj.get("project_name") or proj.get("name", "Unknown"),
                client_name=proj.get("client_name") or proj.get("client"),
                status=proj.get("status", "Active"),
                manager_name=proj.get("manager_name") or proj.get("project_manager")
            ))
        
        logger.info(f"Fetched {len(result)} projects from HRMS")
        return result
        
    except Exception as e:
        logger.warning(f"Could not fetch from HRMS, falling back to local DB: {e}")
        
        # Fallback to local HRMS projects
        hrms_projects = db.query(HRMSProject).all()
        if hrms_projects:
            return [
                HRMSProjectResponse(
                    id=p.id,
                    project_id=p.hrms_project_id,
                    name=p.project_name,
                    client_name=p.client_name,
                    status=p.status,
                    manager_name=p.project_manager_name
                )
                for p in hrms_projects
            ]
        
        # Final fallback to local projects
        local_projects = db.query(Project).all()
        return [
            HRMSProjectResponse(
                id=p.id,
                project_id=str(p.id),
                name=p.name,
                client_name=None,
                status="Active",
                manager_name=None
            )
            for p in local_projects
        ]


@router.get("/projects/count")
async def get_projects_count(
    current_user: User = Depends(get_current_active_user)
):
    """Get count of active projects from HRMS."""
    try:
        projects = await hrms_client.get_all_projects()
        active_count = len([p for p in projects if p.get("status", "Active") == "Active"])
        
        return {
            "total": len(projects),
            "active": active_count
        }
    except Exception as e:
        logger.warning(f"Could not get project count from HRMS: {e}")
        return {"total": 0, "active": 0}

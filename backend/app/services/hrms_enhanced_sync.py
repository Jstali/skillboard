"""Enhanced HRMS data synchronization service.

Pulls employee data including:
- Line managers from project allocations
- Band (defaults to 'A' if not provided)
- Current project information
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.db.models import (
    Employee, HRMSProject, HRMSProjectAssignment, HRMSImportLog,
    EmployeeProjectAssignment, Project
)
from app.services.hrms_client import hrms_client, HRMSClientError

logger = logging.getLogger(__name__)


class EnhancedHRMSSync:
    """Enhanced HRMS sync that pulls line managers from project allocations."""
    
    DEFAULT_BAND = "A"  # Default band if not provided
    
    def __init__(self, db: Session):
        self.db = db
        self.client = hrms_client
    
    async def sync_employees_with_managers(self) -> Dict[str, Any]:
        """
        Sync employees from HRMS including line managers from project allocations.
        
        This method:
        1. Fetches all employees from HRMS
        2. For each employee, fetches their project allocations
        3. Extracts line manager from project allocations
        4. Defaults band to 'A' if not provided
        5. Updates the local employee records
        """
        logger.info("Starting enhanced employee sync with manager data from HRMS")
        
        # Create import log
        import_log = HRMSImportLog(
            import_type="employees_with_managers",
            import_timestamp=datetime.utcnow(),
            status="in_progress"
        )
        self.db.add(import_log)
        self.db.commit()
        
        stats = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "managers_assigned": 0,
            "bands_defaulted": 0,
            "errors": []
        }
        
        try:
            # Fetch all employees from HRMS
            hrms_employees = await self.client.get_all_employees()
            logger.info(f"Fetched {len(hrms_employees)} employees from HRMS")
            
            # Fetch all projects to get manager info
            hrms_projects = await self.client.get_all_projects()
            logger.info(f"Fetched {len(hrms_projects)} projects from HRMS")
            
            # Build project manager lookup
            project_managers = self._build_project_manager_lookup(hrms_projects)
            
            for hrms_emp in hrms_employees:
                try:
                    result = await self._sync_employee_with_manager(
                        hrms_emp, project_managers
                    )
                    stats["processed"] += 1
                    
                    if result.get("created"):
                        stats["created"] += 1
                    elif result.get("updated"):
                        stats["updated"] += 1
                    
                    if result.get("manager_assigned"):
                        stats["managers_assigned"] += 1
                    
                    if result.get("band_defaulted"):
                        stats["bands_defaulted"] += 1
                        
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Employee {hrms_emp.get('id', 'unknown')}: {str(e)}")
                    logger.error(f"Failed to sync employee: {e}")
            
            # Update import log
            import_log.status = "success" if stats["failed"] == 0 else "partial"
            import_log.records_processed = stats["processed"]
            import_log.records_created = stats["created"]
            import_log.records_updated = stats["updated"]
            import_log.records_failed = stats["failed"]
            self.db.commit()
            
            logger.info(f"Enhanced sync completed: {stats}")
            return stats
            
        except Exception as e:
            import_log.status = "failed"
            import_log.error_details = str(e)
            self.db.commit()
            logger.error(f"Enhanced sync failed: {e}")
            raise
    
    def _build_project_manager_lookup(self, projects: List[Dict]) -> Dict[str, Dict]:
        """Build a lookup of project ID to manager info."""
        lookup = {}
        for proj in projects:
            proj_id = str(proj.get("id", proj.get("project_id", "")))
            if proj_id:
                lookup[proj_id] = {
                    "manager_id": proj.get("manager_id"),
                    "manager_name": proj.get("manager_name", proj.get("project_manager_name")),
                    "manager_email": proj.get("manager_email"),
                    "project_name": proj.get("name", proj.get("project_name"))
                }
        return lookup
    
    async def _sync_employee_with_manager(
        self, 
        hrms_emp: Dict[str, Any],
        project_managers: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Sync a single employee with manager data from project allocations."""
        result = {
            "created": False,
            "updated": False,
            "manager_assigned": False,
            "band_defaulted": False
        }
        
        # Extract employee ID
        emp_id = str(hrms_emp.get("id", hrms_emp.get("employee_id", "")))
        if not emp_id:
            raise ValueError("Employee ID not found in HRMS data")
        
        # Extract basic employee data
        name = hrms_emp.get("name", hrms_emp.get("full_name", ""))
        email = hrms_emp.get("email", hrms_emp.get("company_email", ""))
        department = hrms_emp.get("department", hrms_emp.get("dept", ""))
        role = hrms_emp.get("role", hrms_emp.get("job_title", hrms_emp.get("position", "")))
        team = hrms_emp.get("team", "")
        location_id = hrms_emp.get("location_id", hrms_emp.get("location"))
        capability = hrms_emp.get("capability", hrms_emp.get("home_capability", ""))
        
        # Extract band - default to 'A' if not provided
        band = hrms_emp.get("band", hrms_emp.get("grade", hrms_emp.get("level", "")))
        if not band or band.strip() == "":
            band = self.DEFAULT_BAND
            result["band_defaulted"] = True
            logger.info(f"Employee {emp_id}: Band defaulted to '{self.DEFAULT_BAND}'")
        
        # Extract managers list from HRMS data
        managers_list = hrms_emp.get("managers", [])
        
        # Extract current project from HRMS data
        current_project = hrms_emp.get("current_project", hrms_emp.get("project", ""))
        
        # Try to find line manager from project allocations
        line_manager_id = None
        line_manager_name = None
        
        # Method 1: Check if managers list is provided directly
        if managers_list and len(managers_list) > 0:
            # First manager in the list is typically the primary line manager
            line_manager_name = managers_list[0] if isinstance(managers_list[0], str) else managers_list[0].get("name", "")
            logger.info(f"Employee {emp_id}: Found manager from managers list: {line_manager_name}")
        
        # Method 2: Try to get manager from current project
        if not line_manager_name and current_project:
            # Look up project manager
            for proj_id, proj_info in project_managers.items():
                if proj_info.get("project_name") == current_project:
                    line_manager_name = proj_info.get("manager_name")
                    logger.info(f"Employee {emp_id}: Found manager from project '{current_project}': {line_manager_name}")
                    break
        
        # Method 3: Fetch allocations to get line manager
        if not line_manager_name:
            try:
                # Get current month allocations
                current_month = datetime.now().strftime("%Y-%m")
                allocations = await self.client.get_employee_allocations(emp_id, current_month)
                
                if allocations and isinstance(allocations, dict):
                    projects_data = allocations.get("projects", [])
                    if projects_data and len(projects_data) > 0:
                        # Get manager from first/primary project
                        primary_project = projects_data[0]
                        line_manager_name = primary_project.get("manager_name", primary_project.get("line_manager"))
                        current_project = primary_project.get("project_name", current_project)
                        logger.info(f"Employee {emp_id}: Found manager from allocations: {line_manager_name}")
            except Exception as e:
                logger.warning(f"Could not fetch allocations for {emp_id}: {e}")
        
        # Find or create the employee record
        existing_employee = self.db.query(Employee).filter(
            Employee.employee_id == emp_id
        ).first()
        
        # Resolve line manager ID if we have a name
        if line_manager_name:
            manager_emp = self.db.query(Employee).filter(
                Employee.name == line_manager_name
            ).first()
            if manager_emp:
                line_manager_id = manager_emp.id
                result["manager_assigned"] = True
        
        if existing_employee:
            # Update existing employee
            existing_employee.name = name or existing_employee.name
            existing_employee.company_email = email or existing_employee.company_email
            existing_employee.department = department or existing_employee.department
            existing_employee.role = role or existing_employee.role
            existing_employee.team = team or existing_employee.team
            existing_employee.band = band
            existing_employee.home_capability = capability or existing_employee.home_capability
            
            if line_manager_id:
                existing_employee.line_manager_id = line_manager_id
            
            if location_id:
                existing_employee.location_id = location_id
            
            existing_employee.hrms_last_sync = datetime.utcnow()
            result["updated"] = True
            
        else:
            # Create new employee
            new_employee = Employee(
                employee_id=emp_id,
                name=name,
                company_email=email,
                department=department,
                role=role,
                team=team,
                band=band,
                home_capability=capability,
                line_manager_id=line_manager_id,
                location_id=location_id,
                is_active=True,
                hrms_last_sync=datetime.utcnow()
            )
            self.db.add(new_employee)
            result["created"] = True
        
        self.db.commit()
        return result
    
    async def sync_project_assignments_with_managers(self) -> Dict[str, Any]:
        """
        Sync project assignments and update employee line managers based on allocations.
        """
        logger.info("Syncing project assignments with line managers")
        
        stats = {
            "assignments_processed": 0,
            "managers_updated": 0,
            "errors": []
        }
        
        try:
            # Get all projects
            projects = await self.client.get_all_projects()
            
            for project in projects:
                proj_id = project.get("id", project.get("project_id"))
                proj_name = project.get("name", project.get("project_name"))
                manager_name = project.get("manager_name", project.get("project_manager_name"))
                
                if not proj_id:
                    continue
                
                # Find manager employee record
                manager_emp = None
                if manager_name:
                    manager_emp = self.db.query(Employee).filter(
                        Employee.name == manager_name
                    ).first()
                
                # Get employees assigned to this project
                try:
                    assigned_employees = await self.client.get_manager_employees(str(proj_id))
                    
                    for emp_data in assigned_employees:
                        emp_id = str(emp_data.get("id", emp_data.get("employee_id", "")))
                        if not emp_id:
                            continue
                        
                        # Find employee in our database
                        employee = self.db.query(Employee).filter(
                            Employee.employee_id == emp_id
                        ).first()
                        
                        if employee and manager_emp:
                            # Update line manager if not already set
                            if not employee.line_manager_id:
                                employee.line_manager_id = manager_emp.id
                                stats["managers_updated"] += 1
                                logger.info(f"Updated line manager for {emp_id} to {manager_name}")
                        
                        stats["assignments_processed"] += 1
                        
                except Exception as e:
                    stats["errors"].append(f"Project {proj_name}: {str(e)}")
                    logger.warning(f"Could not process project {proj_name}: {e}")
            
            self.db.commit()
            logger.info(f"Project assignment sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Project assignment sync failed: {e}")
            raise
    
    async def update_missing_bands(self) -> Dict[str, Any]:
        """Update all employees with missing bands to default 'A'."""
        logger.info("Updating employees with missing bands")
        
        # Find employees with null or empty band
        employees_without_band = self.db.query(Employee).filter(
            (Employee.band == None) | (Employee.band == "")
        ).all()
        
        count = 0
        for emp in employees_without_band:
            emp.band = self.DEFAULT_BAND
            count += 1
            logger.info(f"Set band to '{self.DEFAULT_BAND}' for employee {emp.employee_id}")
        
        self.db.commit()
        
        return {
            "employees_updated": count,
            "default_band": self.DEFAULT_BAND
        }


def get_enhanced_hrms_sync(db: Session) -> EnhancedHRMSSync:
    """Factory function to create EnhancedHRMSSync instance."""
    return EnhancedHRMSSync(db)

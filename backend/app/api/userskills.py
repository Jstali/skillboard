"""API routes for user/employee skills management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import database, crud
from app.schemas import EmployeeSkill, EmployeeSkillCreate, EmployeeSkillCreateMe, EmployeeSkillUpdate, Employee
from app.db.models import RatingEnum, EmployeeSkill as EmployeeSkillModel, User
from app.api.dependencies import get_current_active_user

router = APIRouter(prefix="/api/user-skills", tags=["user-skills"])


@router.get("/me/employee", response_model=Employee)
async def get_my_employee(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Get employee details for the current logged-in user, fetching from HRMS when available."""
    from app.db.models import Employee as EmployeeModel, EmployeeProjectAssignment, Project, HRMSProjectAssignment, HRMSProject
    from app.services.hrms_client import hrms_client
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Initialize with local data
    line_manager_name = None
    current_project = None
    band = employee.band
    role = employee.role
    location = employee.location_id
    
    # Get line manager name from local DB
    if employee.line_manager_id:
        line_manager = db.query(EmployeeModel).filter(EmployeeModel.id == employee.line_manager_id).first()
        if line_manager:
            line_manager_name = line_manager.name
    
    # Try to fetch employee profile from HRMS
    hrms_emp_id = employee.hrms_employee_id or employee.employee_id
    current_month = datetime.now().strftime("%Y-%m")
    
    try:
        # Fetch employee profile from HRMS (includes manager info)
        hrms_profile = await hrms_client.get_employee_profile(hrms_emp_id)
        
        if hrms_profile:
            # Update with HRMS data if available
            if hrms_profile.get("manager_name"):
                line_manager_name = hrms_profile.get("manager_name")
            if hrms_profile.get("band") or hrms_profile.get("grade"):
                band = hrms_profile.get("band") or hrms_profile.get("grade") or band
            if hrms_profile.get("role") or hrms_profile.get("designation"):
                role = hrms_profile.get("role") or hrms_profile.get("designation") or role
            if hrms_profile.get("location") or hrms_profile.get("country"):
                location = hrms_profile.get("location") or hrms_profile.get("country") or location
                
            logger.info(f"Got profile from HRMS for {employee.employee_id}")
    except Exception as e:
        logger.warning(f"Could not fetch profile from HRMS for {employee.employee_id}: {e}")
    
    # Try to get current project from HRMS allocations
    try:
        # Fetch allocations from HRMS
        allocations = await hrms_client.get_employee_allocations(hrms_emp_id, current_month)
        
        if allocations:
            # Get primary project from allocations
            projects = allocations.get("projects") or allocations.get("allocations") or []
            if isinstance(allocations, dict) and allocations.get("project_name"):
                current_project = allocations.get("project_name")
            elif projects and len(projects) > 0:
                # Get the project with highest allocation or first one
                primary = max(projects, key=lambda p: p.get("allocation_percentage", 0) or p.get("allocated_days", 0), default=None)
                if primary:
                    current_project = primary.get("project_name") or primary.get("name")
            
            logger.info(f"Got allocations from HRMS for {employee.employee_id}: {current_project}")
    except Exception as e:
        logger.warning(f"Could not fetch allocations from HRMS for {employee.employee_id}: {e}")
    
    # Try active projects endpoint as fallback
    if not current_project:
        try:
            active_projects = await hrms_client.get_active_projects(hrms_emp_id, current_month)
            if active_projects and len(active_projects) > 0:
                current_project = active_projects[0].get("project_name") or active_projects[0].get("name")
                logger.info(f"Got active project from HRMS for {employee.employee_id}: {current_project}")
        except Exception as e:
            logger.warning(f"Could not fetch active projects from HRMS: {e}")
    
    # Final fallback to local DB
    if not current_project:
        # Try HRMS project assignments in local DB
        hrms_assignment = db.query(HRMSProjectAssignment).filter(
            HRMSProjectAssignment.employee_id == employee.id,
            HRMSProjectAssignment.is_primary == True
        ).first()
        
        if hrms_assignment:
            hrms_project = db.query(HRMSProject).filter(HRMSProject.id == hrms_assignment.project_id).first()
            if hrms_project:
                current_project = hrms_project.project_name
        
        # Final fallback to local project assignments
        if not current_project:
            project_assignment = db.query(EmployeeProjectAssignment).filter(
                EmployeeProjectAssignment.employee_id == employee.id,
                EmployeeProjectAssignment.is_primary == True
            ).first()
            if project_assignment:
                project = db.query(Project).filter(Project.id == project_assignment.project_id).first()
                if project:
                    current_project = project.name
    
    # Return employee with HRMS-enriched data
    return Employee(
        id=employee.id,
        employee_id=employee.employee_id,
        name=employee.name,
        first_name=employee.first_name,
        last_name=employee.last_name,
        company_email=employee.company_email,
        department=employee.department,
        role=role,
        team=employee.team,
        band=band,
        category=employee.category,
        capability=employee.capability,
        home_capability=employee.home_capability,
        location_id=location,
        line_manager_name=line_manager_name,
        current_project=current_project
    )


@router.get("/me", response_model=List[EmployeeSkill])
def get_my_skills(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Get all skills for the current logged-in user."""
    if not current_user.employee_id:
        return []
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        return []
    
    return crud.get_employee_skills_by_employee_id(db, employee.id)


@router.get("/employee/{employee_id}", response_model=List[EmployeeSkill])
def get_employee_skills(employee_id: str, db: Session = Depends(database.get_db)):
    """Get all skills for an employee (admin or public endpoint)."""
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return crud.get_employee_skills_by_employee_id(db, employee.id)


@router.post("/me", status_code=410)
def create_my_skill(
    current_user: User = Depends(get_current_active_user),
):
    """
    DEPRECATED: Self-service skill editing has been disabled.
    
    Skills are now assessed by Line Managers and Delivery Managers only.
    Use GET /api/assessments/employee/{employee_id} to view your assessed skills.
    """
    raise HTTPException(
        status_code=410,
        detail="Self-service skill editing has been disabled. Skills are now assessed by managers only."
    )


@router.post("/", response_model=EmployeeSkill)
def create_employee_skill(
    employee_skill: EmployeeSkillCreate, db: Session = Depends(database.get_db)
):
    """Create or update an employee-skill mapping (legacy endpoint)."""
    # Get or create employee
    employee_name = employee_skill.employee_name or employee_skill.employee_id
    employee = crud.upsert_employee(
        db, employee_skill.employee_id, employee_name
    )

    # Get or create skill
    skill = crud.upsert_skill(db, employee_skill.skill_name)

    # Create or update employee-skill mapping
    return crud.upsert_employee_skill(
        db,
        employee.id,
        skill.id,
        employee_skill.rating,
        employee_skill.years_experience,
        is_interested=employee_skill.is_interested or False,
        notes=employee_skill.notes,
        is_custom=employee_skill.is_custom or False,
    )


@router.put("/me/{employee_skill_id}", response_model=EmployeeSkill)
def update_my_skill(
    employee_skill_id: int,
    employee_skill: EmployeeSkillUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Update a skill for the current logged-in user."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db_employee_skill = db.query(EmployeeSkillModel).filter(
        EmployeeSkillModel.id == employee_skill_id,
        EmployeeSkillModel.employee_id == employee.id,
    ).first()
    
    if not db_employee_skill:
        raise HTTPException(status_code=404, detail="Employee skill not found")

    if employee_skill.rating:
        # Convert enum to value (string) for storage
        rating_value = employee_skill.rating.value if hasattr(employee_skill.rating, 'value') else str(employee_skill.rating)
        db_employee_skill.rating = rating_value
    if employee_skill.years_experience is not None:
        db_employee_skill.years_experience = employee_skill.years_experience
    if employee_skill.is_interested is not None:
        db_employee_skill.is_interested = employee_skill.is_interested
    if employee_skill.notes is not None:
        db_employee_skill.notes = employee_skill.notes
    if employee_skill.learning_status is not None:
        db_employee_skill.learning_status = employee_skill.learning_status
        from datetime import datetime
        db_employee_skill.status_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_employee_skill)
    return db_employee_skill


@router.put("/{employee_skill_id}", response_model=EmployeeSkill)
def update_employee_skill(
    employee_skill_id: int,
    employee_skill: EmployeeSkillUpdate,
    db: Session = Depends(database.get_db),
):
    """Update an employee-skill mapping (legacy endpoint)."""
    db_employee_skill = db.query(EmployeeSkillModel).filter(
        EmployeeSkillModel.id == employee_skill_id
    ).first()
    if not db_employee_skill:
        raise HTTPException(status_code=404, detail="Employee skill not found")

    if employee_skill.rating:
        # Convert enum to value (string) for storage
        rating_value = employee_skill.rating.value if hasattr(employee_skill.rating, 'value') else str(employee_skill.rating)
        db_employee_skill.rating = rating_value
    if employee_skill.years_experience is not None:
        db_employee_skill.years_experience = employee_skill.years_experience
    if employee_skill.is_interested is not None:
        db_employee_skill.is_interested = employee_skill.is_interested
    if employee_skill.notes is not None:
        db_employee_skill.notes = employee_skill.notes
    if employee_skill.learning_status is not None:
        db_employee_skill.learning_status = employee_skill.learning_status
        from datetime import datetime
        db_employee_skill.status_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_employee_skill)
    return db_employee_skill


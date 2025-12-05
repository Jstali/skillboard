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
def get_my_employee(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Get employee details for the current logged-in user."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee


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


@router.post("/me", response_model=EmployeeSkill)
def create_my_skill(
    employee_skill: EmployeeSkillCreateMe,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Create or update a skill for the current logged-in user."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    # Use current user's employee_id
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get or create skill (with optional category)
    skill = crud.upsert_skill(db, employee_skill.skill_name, category=employee_skill.skill_category)
    
    # Validate skill is in employee's category template if category is set and not a custom skill
    is_custom = employee_skill.is_custom or False
    if employee.category and not is_custom:
        from app.db.models import CategorySkillTemplate
        template_entry = (
            db.query(CategorySkillTemplate)
            .filter(
                CategorySkillTemplate.category == employee.category,
                CategorySkillTemplate.skill_id == skill.id
            )
            .first()
        )
        if not template_entry:
            # Skill not in template - mark as custom
            is_custom = True
    
    # Create or update employee-skill mapping
    # If is_interested is True, rating should be None
    # If is_interested is False, rating is required (default to Beginner if not provided)
    rating = None if employee_skill.is_interested else (employee_skill.rating or RatingEnum.BEGINNER)
    
    return crud.upsert_employee_skill(
        db,
        employee.id,
        skill.id,
        rating,
        employee_skill.years_experience,
        is_interested=employee_skill.is_interested or False,
        notes=employee_skill.notes,
        is_custom=is_custom,
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

    db.commit()
    db.refresh(db_employee_skill)
    return db_employee_skill


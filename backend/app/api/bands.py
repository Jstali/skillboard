"""API routes for band calculation and skill gap analysis."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import database, crud
from app.db.models import RatingEnum, Employee, EmployeeSkill, Skill, RoleRequirement
from app.api.dependencies import get_current_active_user, get_admin_user
from app.db.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/api/bands", tags=["bands"])

# Rating to number mapping
RATING_TO_NUMBER = {
    RatingEnum.BEGINNER: 1,
    RatingEnum.DEVELOPING: 2,
    RatingEnum.INTERMEDIATE: 3,
    RatingEnum.ADVANCED: 4,
    RatingEnum.EXPERT: 5,
}

# Number to rating mapping
NUMBER_TO_RATING = {v: k for k, v in RATING_TO_NUMBER.items()}

# Band calculation based on average rating
# A: avg 1.0-1.5 (all Beginner)
# B: avg 1.5-2.5 (mostly Beginner/Developing)
# C: avg 2.5-3.5 (mostly Developing/Intermediate)
# L1: avg 3.5-4.5 (mostly Intermediate/Advanced)
# L2: avg 4.5-5.0 (mostly Advanced/Expert)
BAND_THRESHOLDS = {
    "A": (1.0, 1.5),
    "B": (1.5, 2.5),
    "C": (2.5, 3.5),
    "L1": (3.5, 4.5),
    "L2": (4.5, 5.1),  # Include 5.0 in L2 range
}

# Default required ratings for each band when no specific requirement is defined
BAND_DEFAULT_RATINGS = {
    "A": RatingEnum.BEGINNER,      # 1
    "B": RatingEnum.DEVELOPING,    # 2
    "C": RatingEnum.INTERMEDIATE,   # 3
    "L1": RatingEnum.ADVANCED,     # 4
    "L2": RatingEnum.EXPERT,       # 5
}


def calculate_band(average_rating: float) -> str:
    """Calculate band based on average rating."""
    for band, (min_val, max_val) in BAND_THRESHOLDS.items():
        if min_val <= average_rating < max_val:
            return band
    # Default to A if below threshold
    if average_rating < 1.0:
        return "A"
    # Default to L2 if above threshold (5.0 or higher)
    return "L2"


def calculate_employee_band(db: Session, employee_id: int) -> Optional[str]:
    """Calculate and return employee band based on their skill ratings."""
    employee_skills = (
        db.query(EmployeeSkill)
        .filter(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.is_interested == False,  # Only count existing skills
            EmployeeSkill.rating.isnot(None)  # Only skills with ratings
        )
        .all()
    )
    
    if not employee_skills:
        return "A"  # Default to A if no skills
    
    # Calculate average rating
    total_rating = 0
    count = 0
    for emp_skill in employee_skills:
        if emp_skill.rating:
            total_rating += RATING_TO_NUMBER[emp_skill.rating]
            count += 1
    
    if count == 0:
        return "A"
    
    average_rating = total_rating / count
    return calculate_band(average_rating)


class SkillGap(BaseModel):
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    current_rating_text: Optional[str]
    current_rating_number: Optional[int]
    required_rating_text: str
    required_rating_number: int
    gap: int  # current - required (positive = above requirement, negative = below requirement)
    is_required: bool


class BandAnalysis(BaseModel):
    employee_id: str
    employee_name: str
    band: str
    average_rating: float
    total_skills: int
    skills_above_requirement: int
    skills_at_requirement: int
    skills_below_requirement: int
    skill_gaps: List[SkillGap]


@router.get("/me/analysis", response_model=BandAnalysis)
def get_my_band_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Get band analysis for current user."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return get_employee_band_analysis(db, employee.id, employee.employee_id, employee.name)


@router.get("/employee/{employee_id}/analysis", response_model=BandAnalysis)
def get_employee_band_analysis_endpoint(
    employee_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get band analysis for an employee."""
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if user can access this employee (own data or admin)
    if not current_user.is_admin and current_user.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this employee's data")
    
    return get_employee_band_analysis(db, employee.id, employee.employee_id, employee.name)


@router.get("/all/analysis", response_model=List[BandAnalysis])
def get_all_employees_band_analysis(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get band analysis for all employees (admin only)."""
    employees = db.query(Employee).all()
    analyses = []
    
    for employee in employees:
        try:
            analysis = get_employee_band_analysis(
                db, 
                employee.id, 
                employee.employee_id, 
                employee.name
            )
            analyses.append(analysis)
        except Exception as e:
            # Skip employees with errors, but log them
            print(f"Error getting analysis for employee {employee.employee_id}: {e}")
            continue
    
    return analyses


def get_employee_band_analysis(
    db: Session,
    employee_db_id: int,
    employee_id: str,
    employee_name: str
) -> BandAnalysis:
    """Calculate band analysis for an employee."""
    # Get all employee skills (existing skills only, with ratings)
    employee_skills = (
        db.query(EmployeeSkill, Skill)
        .join(Skill, EmployeeSkill.skill_id == Skill.id)
        .filter(
            EmployeeSkill.employee_id == employee_db_id,
            EmployeeSkill.is_interested == False,
            EmployeeSkill.rating.isnot(None)
        )
        .all()
    )
    
    if not employee_skills:
        # No skills - return default analysis
        return BandAnalysis(
            employee_id=employee_id,
            employee_name=employee_name,
            band="A",
            average_rating=1.0,
            total_skills=0,
            skills_above_requirement=0,
            skills_at_requirement=0,
            skills_below_requirement=0,
            skill_gaps=[],
        )
    
    # Calculate average rating and band
    total_rating = 0
    count = 0
    for emp_skill, skill in employee_skills:
        if emp_skill.rating:
            total_rating += RATING_TO_NUMBER[emp_skill.rating]
            count += 1
    
    average_rating = total_rating / count if count > 0 else 1.0
    band = calculate_band(average_rating)
    
    # Get role requirements for this band
    role_requirements = (
        db.query(RoleRequirement, Skill)
        .join(Skill, RoleRequirement.skill_id == Skill.id)
        .filter(RoleRequirement.band == band)
        .all()
    )
    
    # Create a map of skill_id -> requirement
    requirement_map = {
        req.skill_id: req for req, _ in role_requirements
    }
    
    # Build skill gaps
    skill_gaps = []
    skills_above = 0
    skills_at = 0
    skills_below = 0
    
    for emp_skill, skill in employee_skills:
        current_rating_num = RATING_TO_NUMBER[emp_skill.rating] if emp_skill.rating else None
        current_rating_text = emp_skill.rating.value if emp_skill.rating else None
        
        # Check if there's a requirement for this skill
        requirement = requirement_map.get(skill.id)
        if requirement:
            required_rating_num = RATING_TO_NUMBER[requirement.required_rating]
            required_rating_text = requirement.required_rating.value
            gap = (current_rating_num or 0) - required_rating_num
            
            if gap > 0:
                skills_above += 1
            elif gap == 0:
                skills_at += 1
            else:
                skills_below += 1
        else:
            # No requirement defined - use band's default requirement
            # L1 defaults to Advanced (4), L2 defaults to Expert (5)
            default_rating = BAND_DEFAULT_RATINGS.get(band, RatingEnum.INTERMEDIATE)
            required_rating_num = RATING_TO_NUMBER[default_rating]
            required_rating_text = default_rating.value
            gap = (current_rating_num or 0) - required_rating_num
            
            if gap > 0:
                skills_above += 1
            elif gap == 0:
                skills_at += 1
            else:
                skills_below += 1
        
        skill_gaps.append(SkillGap(
            skill_id=skill.id,
            skill_name=skill.name,
            skill_category=skill.category,
            current_rating_text=current_rating_text,
            current_rating_number=current_rating_num,
            required_rating_text=required_rating_text,
            required_rating_number=required_rating_num,
            gap=gap,
            is_required=requirement.is_required if requirement else True,
        ))
    
    return BandAnalysis(
        employee_id=employee_id,
        employee_name=employee_name,
        band=band,
        average_rating=round(average_rating, 2),
        total_skills=len(employee_skills),
        skills_above_requirement=skills_above,
        skills_at_requirement=skills_at,
        skills_below_requirement=skills_below,
        skill_gaps=skill_gaps,
    )


@router.post("/calculate-all")
def calculate_all_employee_bands(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Calculate and update bands for all employees (admin only)."""
    employees = db.query(Employee).all()
    updated = 0
    
    for employee in employees:
        band = calculate_employee_band(db, employee.id)
        if employee.band != band:
            employee.band = band
            updated += 1
    
    db.commit()
    
    return {
        "message": f"Updated bands for {updated} employees",
        "total_employees": len(employees),
        "updated": updated,
    }


# Role Requirement Management (Admin only)
class RoleRequirementCreate(BaseModel):
    band: str
    skill_id: int
    required_rating: RatingEnum
    is_required: bool = True


class RoleRequirementResponse(BaseModel):
    id: int
    band: str
    skill_id: int
    required_rating: str
    is_required: bool
    skill: dict

    class Config:
        from_attributes = True


@router.get("/requirements/{band}", response_model=List[RoleRequirementResponse])
def get_role_requirements(
    band: str,
    db: Session = Depends(database.get_db),
):
    """Get role requirements for a specific band."""
    requirements = (
        db.query(RoleRequirement, Skill)
        .join(Skill, RoleRequirement.skill_id == Skill.id)
        .filter(RoleRequirement.band == band)
        .all()
    )
    
    return [
        RoleRequirementResponse(
            id=req.id,
            band=req.band,
            skill_id=req.skill_id,
            required_rating=req.required_rating.value,
            is_required=req.is_required,
            skill={
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
            },
        )
        for req, skill in requirements
    ]


@router.post("/requirements", response_model=RoleRequirementResponse)
def create_role_requirement(
    requirement: RoleRequirementCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a role requirement (admin only)."""
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == requirement.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if requirement already exists
    existing = (
        db.query(RoleRequirement)
        .filter(
            RoleRequirement.band == requirement.band,
            RoleRequirement.skill_id == requirement.skill_id
        )
        .first()
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Requirement already exists for this band and skill")
    
    # Create requirement
    db_requirement = RoleRequirement(
        band=requirement.band,
        skill_id=requirement.skill_id,
        required_rating=requirement.required_rating,
        is_required=requirement.is_required,
    )
    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)
    
    return RoleRequirementResponse(
        id=db_requirement.id,
        band=db_requirement.band,
        skill_id=db_requirement.skill_id,
        required_rating=db_requirement.required_rating.value,
        is_required=db_requirement.is_required,
        skill={
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
        },
    )


@router.delete("/requirements/{requirement_id}")
def delete_role_requirement(
    requirement_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a role requirement (admin only)."""
    requirement = db.query(RoleRequirement).filter(RoleRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    db.delete(requirement)
    db.commit()
    
    return {"message": "Requirement deleted successfully"}


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


class SuggestedCourse(BaseModel):
    id: int
    title: str
    external_url: Optional[str]
    is_mandatory: bool


class SkillGap(BaseModel):
    skill_id: int
    employee_skill_id: int  # ID of the EmployeeSkill record for updating
    skill_name: str
    skill_category: Optional[str]
    current_rating_text: Optional[str]
    current_rating_number: Optional[int]
    required_rating_text: str
    required_rating_number: int
    requirement_source: str # Template, Role, or Band Default
    gap: int  # current - required (positive = above requirement, negative = below requirement)
    is_required: bool
    notes: Optional[str]  # Improvement plan/notes
    learning_status: str # Not Started, Learning, Stuck, Completed
    pending_days: Optional[int] # Days since status update if not completed
    suggested_courses: List[SuggestedCourse] = []


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
    target_band: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(database.get_db),
):
    """Get band analysis for current user."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = crud.get_employee_by_id(db, current_user.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return get_employee_band_analysis(db, employee.id, employee.employee_id, employee.name, target_band)


@router.get("/employee/{employee_id}/analysis", response_model=BandAnalysis)
def get_employee_band_analysis_endpoint(
    employee_id: str,
    target_band: Optional[str] = None,
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
    
    return get_employee_band_analysis(db, employee.id, employee.employee_id, employee.name, target_band)


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


    # ... (existing imports, etc) ...

def get_employee_band_analysis(
    db: Session,
    employee_db_id: int,
    employee_id: str,
    employee_name: str,
    target_band: Optional[str] = None
) -> BandAnalysis:
    """Calculate band analysis for an employee."""
    from app.db.models import TemplateAssignment, SkillTemplate
    import json
    
    # Get employee to get their predefined band from database
    employee = db.query(Employee).filter(Employee.id == employee_db_id).first()
    
    # Get all employee skills (existing skills only, with ratings)
    # EXCLUDE custom skills (is_custom=True) - they are not required for the role
    employee_skills_query = (
        db.query(EmployeeSkill, Skill)
        .join(Skill, EmployeeSkill.skill_id == Skill.id)
        .filter(
            EmployeeSkill.employee_id == employee_db_id,
            EmployeeSkill.is_interested == False,
            EmployeeSkill.is_custom == False,  # Exclude custom skills from gap analysis
            EmployeeSkill.rating.isnot(None)
        )
        .all()
    )
    
    # Map skill_id -> {emp_skill, skill_obj}
    employee_skill_map = {}
    for emp_skill, skill in employee_skills_query:
        employee_skill_map[skill.id] = {"emp_skill": emp_skill, "skill": skill}

    # Fetch ALL skills to map names to IDs for templates
    all_skills = db.query(Skill).all()
    skill_name_to_id = {s.name.lower(): s for s in all_skills}
    skill_id_to_obj = {s.id: s for s in all_skills}
    
    # Use target_band if provided, otherwise use employee's band, else default to "A"
    band = target_band if target_band else (employee.band if employee and employee.band else "A")

    # --- 1. Fetch Assigned Templates & Parse Requirements ---
    assigned_templates = (
        db.query(SkillTemplate)
        .join(TemplateAssignment, TemplateAssignment.template_id == SkillTemplate.id)
        .filter(TemplateAssignment.employee_id == employee_db_id)
        .all()
    )
    
    # Map of Skill ID -> Required Rating (from Templates)
    # Priority: Template Requirement > Role Requirement > Band Default
    template_requirements = {} 
    
    for template in assigned_templates:
        try:
            content = json.loads(template.content)
            if not content: continue
            
            # Simple header detection (assuming first row is header)
            headers = [str(h).lower().strip() for h in content[0]]
            
            # Find column indices
            skill_col_idx = -1
            req_level_col_idx = -1
            
            for idx, header in enumerate(headers):
                if 'skill' in header and 'category' not in header:
                    skill_col_idx = idx
                if 'required' in header or 'level' in header or 'rating' in header:
                    req_level_col_idx = idx
            
            if skill_col_idx == -1 or req_level_col_idx == -1:
                print(f"Skipping template {template.template_name}: Could not find Skill or Required Level columns.")
                continue
                
            # Iterate rows
            for row in content[1:]:
                if len(row) <= max(skill_col_idx, req_level_col_idx): continue
                
                skill_name = str(row[skill_col_idx]).strip()
                req_level_str = str(row[req_level_col_idx]).strip()
                
                if not skill_name or not req_level_str: continue
                
                # Normalize rating string to Enum
                req_rating_enum = None
                req_level_lower = req_level_str.lower()
                
                if 'beginner' in req_level_lower: req_rating_enum = RatingEnum.BEGINNER
                elif 'developing' in req_level_lower: req_rating_enum = RatingEnum.DEVELOPING
                elif 'intermediate' in req_level_lower: req_rating_enum = RatingEnum.INTERMEDIATE
                elif 'advanced' in req_level_lower: req_rating_enum = RatingEnum.ADVANCED
                elif 'expert' in req_level_lower: req_rating_enum = RatingEnum.EXPERT
                
                if req_rating_enum:
                     # Find Skill ID from Name
                     if skill_name.lower() in skill_name_to_id:
                         skill_obj = skill_name_to_id[skill_name.lower()]
                         template_requirements[skill_obj.id] = req_rating_enum
                     else:
                         print(f"Warning: Template skill '{skill_name}' not found in database.")
                             
        except Exception as e:
            print(f"Error parsing template {template.template_name}: {e}")

    # --- 2. Role Requirements (Database) ---
    # Filter by employee's pathway if they have one
    role_requirements_query = (
        db.query(RoleRequirement, Skill)
        .join(Skill, RoleRequirement.skill_id == Skill.id)
        .filter(RoleRequirement.band == band)
    )
    
    # If employee has a pathway, only get requirements for skills in that pathway
    if employee and employee.pathway:
        role_requirements_query = role_requirements_query.filter(Skill.pathway == employee.pathway)
    
    role_requirements = role_requirements_query.all()
    
    # Create a map of skill_id -> requirement
    role_req_map = {
        req.skill_id: req.required_rating for req, _ in role_requirements
    }
    
    # --- 3. Build Gaps (Union of Employee Skills + Required Skills) ---
    all_relevant_skill_ids = set(employee_skill_map.keys()) | set(template_requirements.keys()) | set(role_req_map.keys())
    
    skill_gaps = []
    skills_above = 0
    skills_at = 0
    skills_below = 0
    
    from datetime import datetime
    
    for skill_id in all_relevant_skill_ids:
        skill_obj = skill_id_to_obj.get(skill_id)
        if not skill_obj: continue # Should not happen given logic above

        # Determine Employee's Current Rating
        current_rating_enum = None
        current_rating_num = 0 # Default to 0 for missing skills
        current_rating_text = "Not Rated"
        emp_skill_id = 0 # Dummy ID if missing
        notes = None
        learning_status = "Not Started"
        status_updated_at = None
        
        if skill_id in employee_skill_map:
            emp_data = employee_skill_map[skill_id]
            emp_skill = emp_data["emp_skill"]
            
            if emp_skill.rating:
                current_rating_enum = emp_skill.rating
                current_rating_num = RATING_TO_NUMBER[emp_skill.rating]
                current_rating_text = emp_skill.rating.value
            
            emp_skill_id = emp_skill.id
            notes = emp_skill.notes
            learning_status = emp_skill.learning_status or "Not Started"
            status_updated_at = emp_skill.status_updated_at
        
        # Determine Required Rating
        required_rating = None
        source = "Default"
        
        # Priority 1: Template
        if skill_id in template_requirements:
            required_rating = template_requirements[skill_id]
            source = "Template"
        # Priority 2: Role Requirement
        elif skill_id in role_req_map:
            required_rating = role_req_map[skill_id]
            source = "Role"
        # Priority 3: Band Default (Only if the employee has the skill, OR if we want to enforce defaults on everything? 
        # Usually defaults only apply if we have a reason to grade it. 
        # But for gap analysis, if it's not in Template or Role, and Employee has it, we compare against default.)
        elif skill_id in employee_skill_map:
             required_rating = BAND_DEFAULT_RATINGS.get(band, RatingEnum.INTERMEDIATE)
             source = "Band Default"
        else:
            # Skill is not in Template, not in Role, and not in Employee Profile.
            # This shouldn't happen because we iterate over the union. 
            # If it's in the union set but not in map or reqs, it must be in employee map, covered above.
            continue
             
        required_rating_num = RATING_TO_NUMBER[required_rating]
        required_rating_text = required_rating.value
        
        gap = current_rating_num - required_rating_num
        
        if gap > 0:
            skills_above += 1
        elif gap == 0:
            skills_at += 1
        else:
            skills_below += 1
        
        # Calculate pending days
        pending_days = 0
        if learning_status in ["Learning", "Stuck"] and status_updated_at:
            delta = datetime.utcnow() - status_updated_at
            pending_days = delta.days

        # Fetch suggested courses
        from app.db.models import Course 
        courses = db.query(Course).filter(Course.skill_id == skill_id).all()
        suggested_courses = [
            SuggestedCourse(
                id=c.id, 
                title=c.title, 
                external_url=c.external_url, 
                is_mandatory=c.is_mandatory
            ) for c in courses
        ]

        skill_gaps.append(SkillGap(
            skill_id=skill_id,
            employee_skill_id=emp_skill_id,
            skill_name=skill_obj.name,
            skill_category=skill_obj.category,
            current_rating_text=current_rating_text,
            current_rating_number=current_rating_num,
            required_rating_text=required_rating_text,
            required_rating_number=required_rating_num,
            gap=gap,
            is_required=True, # Simplified for now
            requirement_source=source,
            notes=notes,
            learning_status=learning_status,
            pending_days=pending_days,
            suggested_courses=suggested_courses,
        ))
    
    total_skills_count = len(skill_gaps) # Total tracked skills for this band/role/template
    
    # Calculate average rating only for skills the employee HAS
    if len(employee_skill_map) > 0:
         # This part is a bit tricky if we want "Band Average" - usually strictly based on held skills
         pass 

    return BandAnalysis(
        employee_id=employee_id,
        employee_name=employee_name,
        band=band,
        average_rating=0.0,  # No longer calculated - band comes from database
        total_skills=total_skills_count,
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


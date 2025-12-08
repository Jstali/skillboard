"""API routes for admin/HR dashboard."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.db import database, crud
from app.schemas import Employee, EmployeeSkill, Skill
from app.api.dependencies import get_admin_user
from app.db.models import User, Employee as EmployeeModel, EmployeeSkill as EmployeeSkillModel, Skill as SkillModel

router = APIRouter(prefix="/api/admin", tags=["admin-dashboard"])


@router.get("/employees", response_model=List[Employee])
def get_all_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all employees (admin/HR only)."""
    query = db.query(EmployeeModel)
    
    if department:
        query = query.filter(EmployeeModel.department == department)
    
    employees = query.offset(skip).limit(limit).all()
    return employees


from pydantic import BaseModel

class SkillRatingCriteria(BaseModel):
    skill_name: str
    rating: Optional[str] = None

class MultiSkillSearchRequest(BaseModel):
    criteria: List[SkillRatingCriteria]

@router.post("/employees/search")
def search_employees_by_skill(
    request: MultiSkillSearchRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Search for employees by multiple skill-rating criteria (admin/HR only).
    
    Accepts multiple skill-rating pairs. Returns employees who match ALL criteria.
    Each criterion can have:
    - skill_name: Required - uses fuzzy matching with partial word support
    - rating: Optional - includes ±1 level flexibility (e.g., Intermediate shows Advanced & Developing)
    
    Example:
    {
      "criteria": [
        {"skill_name": "Python", "rating": "Advanced"},
        {"skill_name": "JavaScript", "rating": "Intermediate"}
      ]
    }
    """
    from app.db.models import RatingEnum
    from rapidfuzz import process, fuzz
    from collections import defaultdict
    
    if not request.criteria or len(request.criteria) == 0:
        return {
            "total_results": 0,
            "employees": [],
        }
    
    # Get all skills for fuzzy matching
    all_skills = crud.get_all_skills(db, skip=0, limit=10000)
    skill_names = [skill.name for skill in all_skills]
    
    # Process each criterion to find matching skills
    criteria_matches = []  # List of {skill_ids, rating_filter, match_scores_map}
    
    for criterion in request.criteria:
        skill_name = criterion.skill_name.strip().lower()
        rating = criterion.rating.strip().capitalize() if criterion.rating else None
        
        # Find matching skills using fuzzy matching
        matched_skills_with_scores = {}
        
        if skill_names:
            # Use multiple scoring methods for better partial word matching
            matches_token_sort = process.extract(
                skill_name, skill_names, scorer=fuzz.token_sort_ratio, limit=50
            )
            matches_partial = process.extract(
                skill_name, skill_names, scorer=fuzz.partial_ratio, limit=50
            )
            matches_token_set = process.extract(
                skill_name, skill_names, scorer=fuzz.token_set_ratio, limit=50
            )
            
            # Combine all matches
            all_matches = {}
            for skill_name_match, score, _ in matches_token_sort + matches_partial + matches_token_set:
                skill_lower = skill_name_match.lower()
                search_words = skill_name.split()
                word_match = any(word in skill_lower for word in search_words)
                
                current_score = all_matches.get(skill_name_match, 0)
                boosted_score = score
                if word_match and score < 60:
                    boosted_score = max(score, 60)
                
                all_matches[skill_name_match] = max(current_score, boosted_score)
            
            matched_skills_with_scores = {
                skill_name_match: score 
                for skill_name_match, score in all_matches.items()
                if score >= 50
            }
        
        if not matched_skills_with_scores:
            # No matches for this criterion - skip it or return empty?
            continue
        
        # Get skill IDs for matched skills
        matched_skill_ids = [
            skill.id for skill in all_skills 
            if skill.name in matched_skills_with_scores
        ]
        
        # Process rating filter
        allowed_ratings = None
        rating_enum = None
        if rating:
            try:
                rating_enum = RatingEnum(rating)
                rating_order = {
                    RatingEnum.BEGINNER: 1,
                    RatingEnum.DEVELOPING: 2,
                    RatingEnum.INTERMEDIATE: 3,
                    RatingEnum.ADVANCED: 4,
                    RatingEnum.EXPERT: 5,
                }
                required_order = rating_order.get(rating_enum, 0)
                allowed_ratings = [
                    r_enum for r_enum, order in rating_order.items()
                    if abs(order - required_order) <= 1
                ]
            except ValueError:
                continue  # Skip invalid rating
        
        criteria_matches.append({
            "skill_ids": matched_skill_ids,
            "allowed_ratings": allowed_ratings,
            "required_rating": rating_enum,
            "match_scores": matched_skills_with_scores,
        })
    
    if not criteria_matches:
        return {
            "total_results": 0,
            "employees": [],
        }
    
    # Get all employees with their skills
    all_employee_skills = (
        db.query(EmployeeModel, EmployeeSkillModel, SkillModel)
        .join(EmployeeSkillModel, EmployeeModel.id == EmployeeSkillModel.employee_id)
        .join(SkillModel, EmployeeSkillModel.skill_id == SkillModel.id)
        .filter(EmployeeSkillModel.is_interested == False)
        .filter(EmployeeSkillModel.rating.isnot(None))
        .all()
    )
    
    # Group by employee and check criteria matches
    employee_skills_map = defaultdict(lambda: {
        "employee": None,
        "skills": []
    })
    
    for employee, employee_skill, skill in all_employee_skills:
        emp_id = employee.employee_id
        if employee_skills_map[emp_id]["employee"] is None:
            employee_skills_map[emp_id]["employee"] = employee
        employee_skills_map[emp_id]["skills"].append({
            "skill_id": skill.id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "rating": employee_skill.rating,
            "years_experience": employee_skill.years_experience,
        })
    
    # Check each employee against all criteria
    result_list = []
    for emp_id, emp_data in employee_skills_map.items():
        employee = emp_data["employee"]
        employee_skills = emp_data["skills"]
        
        # Check how many criteria this employee matches
        matched_criteria = []
        total_criteria_score = 0
        
        for criterion_idx, criterion in enumerate(criteria_matches):
            # Find if employee has any skill matching this criterion
            best_match = None
            best_score = 0
            
            for emp_skill in employee_skills:
                if emp_skill["skill_id"] in criterion["skill_ids"]:
                    # Check rating if required
                    if criterion["allowed_ratings"]:
                        if emp_skill["rating"] not in criterion["allowed_ratings"]:
                            continue
                    
                    # Calculate match score
                    skill_name = emp_skill["skill_name"]
                    skill_match_score = criterion["match_scores"].get(skill_name, 100)
                    
                    # Adjust for rating match
                    rating_boost = 0
                    if criterion["required_rating"] and emp_skill["rating"]:
                        rating_order = {
                            RatingEnum.BEGINNER: 1,
                            RatingEnum.DEVELOPING: 2,
                            RatingEnum.INTERMEDIATE: 3,
                            RatingEnum.ADVANCED: 4,
                            RatingEnum.EXPERT: 5,
                        }
                        required_order = rating_order.get(criterion["required_rating"], 0)
                        actual_order = rating_order.get(emp_skill["rating"], 0)
                        
                        if actual_order == required_order:
                            rating_boost = 10
                        elif abs(actual_order - required_order) == 1:
                            rating_boost = 0
                    
                    final_score = min(100, skill_match_score + rating_boost)
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = {
                            "skill_id": emp_skill["skill_id"],
                            "skill_name": emp_skill["skill_name"],
                            "skill_category": emp_skill["skill_category"],
                            "rating": emp_skill["rating"].value if emp_skill["rating"] else None,
                            "years_experience": emp_skill["years_experience"],
                            "match_score": round(final_score, 2),
                            "criterion_index": criterion_idx,
                        }
            
            if best_match:
                matched_criteria.append(best_match)
                total_criteria_score += best_score
        
        # Only include employees who match at least one criterion
        if matched_criteria:
            # Calculate overall match percentage
            match_percentage = total_criteria_score / len(criteria_matches) if criteria_matches else 0
            
            result_list.append({
                "employee": {
                    "id": employee.id,
                    "employee_id": employee.employee_id,
                    "name": employee.name,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "company_email": employee.company_email,
                    "department": employee.department,
                    "role": employee.role,
                    "team": employee.team,
                    "band": employee.band,
                    "category": employee.category,
                },
                "matching_skills": matched_criteria,
                "match_count": len(matched_criteria),
                "criteria_count": len(criteria_matches),
                "match_percentage": round(match_percentage, 2),
            })
    
    # Sort by match percentage (descending), then by number of matching criteria
    result_list.sort(key=lambda x: (x["match_percentage"], x["match_count"]), reverse=True)
    
    return {
        "total_results": len(result_list),
        "employees": result_list,
    }


@router.get("/employees/{employee_id}/skills", response_model=List[EmployeeSkill])
def get_employee_skills_admin(
    employee_id: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all skills for a specific employee (admin/HR only)."""
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return crud.get_employee_skills_by_employee_id(db, employee.id)


@router.get("/skills/overview")
def get_skills_overview(
    category: Optional[str] = Query(None, description="Filter by employee category (e.g., Technical, P&C)"),
    skill_category: Optional[str] = Query(None, description="Filter by skill category (e.g., Programming, Database)"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get overview of all skills with employee counts and rating breakdown.
    
    If category is provided, only returns skills from that category's template.
    If skill_category is provided, filters by skill's category field.
    """
    from sqlalchemy import func, Integer, case, cast
    from app.db.models import RatingEnum, CategorySkillTemplate
    
    # Start with skills query
    skills_subquery = db.query(SkillModel)
    
    # If employee category filter is provided, only get skills from that category template
    if category:
        skills_subquery = skills_subquery.join(
            CategorySkillTemplate, 
            CategorySkillTemplate.skill_id == SkillModel.id
        ).filter(CategorySkillTemplate.category == category)
    
    # If skill category filter is provided, filter by skill's category field
    if skill_category:
        skills_subquery = skills_subquery.filter(SkillModel.category == skill_category)
    
    # Get skill IDs from filtered skills
    skill_ids = [s.id for s in skills_subquery.all()]
    
    if not skill_ids:
        # No skills match the filters
        return []
    
    # Build base query with counts
    base_query = (
        db.query(
            SkillModel,
            func.count(func.distinct(EmployeeSkillModel.employee_id)).label('employee_count'),
            func.sum(cast(EmployeeSkillModel.is_interested == False, Integer)).label('existing_count'),
            func.sum(cast(EmployeeSkillModel.is_interested == True, Integer)).label('interested_count'),
        )
        .filter(SkillModel.id.in_(skill_ids))
        .outerjoin(EmployeeSkillModel, SkillModel.id == EmployeeSkillModel.skill_id)
    )
    
    # Get all skills with counts of employees who have them
    skills_with_counts = (
        base_query
        .group_by(SkillModel.id)
        .all()
    )
    
    result = []
    for skill, emp_count, existing_count, interested_count in skills_with_counts:
        # Get rating breakdown for this skill (only for existing skills, not interested)
        rating_breakdown = (
            db.query(
                EmployeeSkillModel.rating,
                func.count(EmployeeSkillModel.id).label('count')
            )
            .filter(EmployeeSkillModel.skill_id == skill.id)
            .filter(EmployeeSkillModel.is_interested == False)
            .filter(EmployeeSkillModel.rating.isnot(None))
            .group_by(EmployeeSkillModel.rating)
            .all()
        )
        
        # Build rating counts dictionary
        rating_counts = {
            "Beginner": 0,
            "Developing": 0,
            "Intermediate": 0,
            "Advanced": 0,
            "Expert": 0,
        }
        for rating, count in rating_breakdown:
            if rating:
                rating_counts[rating.value] = count
        
        result.append({
            "skill": {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
            },
            "total_employees": emp_count or 0,
            "existing_skills_count": existing_count or 0,
            "interested_skills_count": interested_count or 0,
            "rating_breakdown": rating_counts,
        })
    
    return result


@router.get("/skill-improvements")
def get_skill_improvements(
    skill_id: Optional[int] = Query(None),
    employee_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get skill improvements - employees who have upgraded their skill ratings.
    Includes both manual skill entries and template submissions.
    Shows skills where current_rating > initial_rating (actual improvements).
    """
    from app.db.models import RatingEnum, EmployeeTemplateResponse, TemplateAssignment
    from sqlalchemy import func, and_
    
    # Rating order for comparison: Beginner < Developing < Intermediate < Advanced < Expert
    rating_order = {
        "Beginner": 1,
        "Developing": 2,
        "Intermediate": 3,
        "Advanced": 4,
        "Expert": 5,
    }
    
    improvements = []
    
    # 1. Get improvements from manual skill entries (existing logic)
    query = (
        db.query(
            EmployeeModel.employee_id,
            EmployeeModel.name,
            SkillModel.name.label('skill_name'),
            EmployeeSkillModel.rating,
            EmployeeSkillModel.initial_rating,
            EmployeeSkillModel.years_experience,
        )
        .join(EmployeeSkillModel, EmployeeModel.id == EmployeeSkillModel.employee_id)
        .join(SkillModel, EmployeeSkillModel.skill_id == SkillModel.id)
        .filter(EmployeeSkillModel.is_interested == False)
        .filter(EmployeeSkillModel.rating.isnot(None))
        .filter(EmployeeSkillModel.initial_rating.isnot(None))
    )
    
    if skill_id:
        query = query.filter(SkillModel.id == skill_id)
    
    if employee_id:
        query = query.filter(EmployeeModel.employee_id == employee_id)
    
    results = query.all()
    
    for row in results:
        current_rating = row.rating
        initial_rating = row.initial_rating
        
        if current_rating and initial_rating:
            current_order = rating_order.get(current_rating.value if hasattr(current_rating, 'value') else current_rating, 0)
            initial_order = rating_order.get(initial_rating.value if hasattr(initial_rating, 'value') else initial_rating, 0)
            
            if current_order > initial_order:
                improvements.append({
                    "employee_id": row.employee_id,
                    "employee_name": row.name,
                    "skill_name": row.skill_name,
                    "initial_rating": initial_rating.value if hasattr(initial_rating, 'value') else initial_rating,
                    "current_rating": current_rating.value if hasattr(current_rating, 'value') else current_rating,
                    "years_experience": row.years_experience,
                    "source": "Manual Entry"
                })
    
    # 2. Get improvements from template submissions
    # Find employees with multiple template submissions for the same skill
    # Compare first submission (baseline) vs latest submission (current)
    
    # Subquery to get first (earliest) submission per employee-skill
    first_submission = (
        db.query(
            EmployeeTemplateResponse.skill_id,
            TemplateAssignment.employee_id,
            func.min(EmployeeTemplateResponse.created_at).label('first_date')
        )
        .join(TemplateAssignment, EmployeeTemplateResponse.assignment_id == TemplateAssignment.id)
        .group_by(EmployeeTemplateResponse.skill_id, TemplateAssignment.employee_id)
    ).subquery()
    
    # Subquery to get latest (most recent) submission per employee-skill
    latest_submission = (
        db.query(
            EmployeeTemplateResponse.skill_id,
            TemplateAssignment.employee_id,
            func.max(EmployeeTemplateResponse.created_at).label('latest_date')
        )
        .join(TemplateAssignment, EmployeeTemplateResponse.assignment_id == TemplateAssignment.id)
        .group_by(EmployeeTemplateResponse.skill_id, TemplateAssignment.employee_id)
    ).subquery()
    
    # Get first submission details
    first_details = (
        db.query(
            EmployeeModel.employee_id,
            EmployeeModel.name.label('employee_name'),
            SkillModel.name.label('skill_name'),
            EmployeeTemplateResponse.employee_level.label('first_rating'),
            EmployeeTemplateResponse.skill_id,
            TemplateAssignment.employee_id.label('emp_id')
        )
        .join(TemplateAssignment, EmployeeTemplateResponse.assignment_id == TemplateAssignment.id)
        .join(EmployeeModel, TemplateAssignment.employee_id == EmployeeModel.id)
        .join(SkillModel, EmployeeTemplateResponse.skill_id == SkillModel.id)
        .join(
            first_submission,
            and_(
                EmployeeTemplateResponse.skill_id == first_submission.c.skill_id,
                TemplateAssignment.employee_id == first_submission.c.employee_id,
                EmployeeTemplateResponse.created_at == first_submission.c.first_date
            )
        )
    ).subquery()
    
    # Get latest submission details and join with first submission
    template_improvements = (
        db.query(
            first_details.c.employee_id,
            first_details.c.employee_name,
            first_details.c.skill_name,
            first_details.c.first_rating,
            EmployeeTemplateResponse.employee_level.label('latest_rating'),
        )
        .join(TemplateAssignment, EmployeeTemplateResponse.assignment_id == TemplateAssignment.id)
        .join(
            latest_submission,
            and_(
                EmployeeTemplateResponse.skill_id == latest_submission.c.skill_id,
                TemplateAssignment.employee_id == latest_submission.c.employee_id,
                EmployeeTemplateResponse.created_at == latest_submission.c.latest_date
            )
        )
        .join(
            first_details,
            and_(
                EmployeeTemplateResponse.skill_id == first_details.c.skill_id,
                TemplateAssignment.employee_id == first_details.c.emp_id
            )
        )
    ).all()
    
    for row in template_improvements:
        first_rating = row.first_rating
        latest_rating = row.latest_rating
        
        if first_rating and latest_rating:
            first_order = rating_order.get(first_rating, 0)
            latest_order = rating_order.get(latest_rating, 0)
            
            # Only include if there's actual improvement
            if latest_order > first_order:
                improvements.append({
                    "employee_id": row.employee_id,
                    "employee_name": row.employee_name,
                    "skill_name": row.skill_name,
                    "initial_rating": first_rating,
                    "current_rating": latest_rating,
                    "years_experience": None,
                    "source": "Template Submission"
                })
    
    return {
        "improvements": improvements,
        "total_count": len(improvements),
        "note": "Showing skills where employees have improved (current rating > initial rating). Includes both manual entries and template submissions."
    }


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get dashboard statistics for admin/HR."""
    from sqlalchemy import func
    
    # Total employees
    total_employees = db.query(func.count(EmployeeModel.id)).scalar()
    
    # Total skills
    total_skills = db.query(func.count(SkillModel.id)).scalar()
    
    # Total employee-skill mappings
    total_mappings = db.query(func.count(EmployeeSkillModel.id)).scalar()
    
    # Employees with existing skills
    employees_with_skills = (
        db.query(func.count(func.distinct(EmployeeSkillModel.employee_id)))
        .filter(EmployeeSkillModel.is_interested == False)
        .scalar()
    )
    
    # Employees with interested skills
    employees_interested = (
        db.query(func.count(func.distinct(EmployeeSkillModel.employee_id)))
        .filter(EmployeeSkillModel.is_interested == True)
        .scalar()
    )
    
    # Skills by rating
    rating_counts = (
        db.query(
            EmployeeSkillModel.rating,
            func.count(EmployeeSkillModel.id).label('count')
        )
        .filter(EmployeeSkillModel.is_interested == False)
        .filter(EmployeeSkillModel.rating.isnot(None))
        .group_by(EmployeeSkillModel.rating)
        .all()
    )
    
    rating_breakdown = {}
    for rating, count in rating_counts:
        if rating:
            rating_breakdown[rating.value] = count
        else:
            rating_breakdown["None"] = count
    
    return {
        "total_employees": total_employees or 0,
        "total_skills": total_skills or 0,
        "total_skill_mappings": total_mappings or 0,
        "employees_with_existing_skills": employees_with_skills or 0,
        "employees_with_interested_skills": employees_interested or 0,
        "rating_breakdown": rating_breakdown,
    }


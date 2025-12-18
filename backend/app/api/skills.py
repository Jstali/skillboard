"""API routes for skills management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import database, crud
from app.schemas import Skill, SkillCreate
from app.api.dependencies import get_optional_current_user
from app.db.models import User, CategorySkillTemplate, Skill as SkillModel

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/", response_model=List[Skill])
def get_skills(
    skip: int = 0,
    limit: int = 100,
    pathway: Optional[str] = None,  # Filter by pathway
    db: Session = Depends(database.get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Get skills. If user is logged in and has a pathway, returns only skills from their pathway.
    If pathway parameter is provided, returns skills from that pathway.
    Otherwise, returns all skills.
    """
    try:
        # If user is logged in, try to get their pathway
        employee_pathway = None
        if current_user and current_user.employee_id:
            try:
                employee = crud.get_employee_by_id(db, current_user.employee_id)
                if employee and employee.pathway:
                    employee_pathway = employee.pathway
            except Exception as e:
                # Log error but continue - don't fail the whole request
                print(f"Error getting employee pathway: {e}")
        
        # Use provided pathway or employee's pathway
        filter_pathway = pathway or employee_pathway
        
        if filter_pathway:
            # Get skills that belong to this pathway
            skills = (
                db.query(SkillModel)
                .filter(SkillModel.pathway == filter_pathway)
                .order_by(SkillModel.category.asc().nullslast(), SkillModel.name.asc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return skills
        else:
            # Return all skills if no pathway filter
            skills = crud.get_all_skills(db, skip=skip, limit=limit)
            return skills
    except Exception as e:
        # Log the error and return empty list or raise proper HTTP exception
        print(f"Error in get_skills: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")


@router.get("/all", response_model=List[Skill])
def get_all_skills_simple(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """
    Get all skills without any filtering. Useful for admin interfaces.
    No authentication required for reading skills.
    """
    try:
        skills = crud.get_all_skills(db, skip=skip, limit=limit)
        return skills
    except Exception as e:
        print(f"Error in get_all_skills_simple: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")


@router.get("/grouped")
def get_skills_grouped_by_pathway(
    db: Session = Depends(database.get_db),
):
    """
    Get all skills grouped by pathway and category.
    Returns: { pathway: { category: [skills] } }
    """
    try:
        skills = db.query(SkillModel).order_by(
            SkillModel.pathway.asc().nullslast(),
            SkillModel.category.asc().nullslast(),
            SkillModel.name.asc()
        ).all()
        
        result = {}
        for skill in skills:
            pathway = skill.pathway or "Uncategorized"
            category = skill.category or "General"
            
            if pathway not in result:
                result[pathway] = {}
            if category not in result[pathway]:
                result[pathway][category] = []
            
            result[pathway][category].append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "pathway": skill.pathway,
                "category": skill.category
            })
        
        return result
    except Exception as e:
        print(f"Error in get_skills_grouped: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")


@router.get("/pathways")
def get_pathways(
    db: Session = Depends(database.get_db),
):
    """
    Get list of all unique pathways with their categories and skill counts.
    """
    try:
        from sqlalchemy import func
        
        # Get pathway -> category -> count
        results = db.query(
            SkillModel.pathway,
            SkillModel.category,
            func.count(SkillModel.id).label('skill_count')
        ).group_by(
            SkillModel.pathway,
            SkillModel.category
        ).order_by(
            SkillModel.pathway.asc().nullslast(),
            SkillModel.category.asc().nullslast()
        ).all()
        
        pathways = {}
        for pathway, category, count in results:
            pathway_name = pathway or "Uncategorized"
            category_name = category or "General"
            
            if pathway_name not in pathways:
                pathways[pathway_name] = {
                    "name": pathway_name,
                    "categories": {},
                    "total_skills": 0
                }
            
            pathways[pathway_name]["categories"][category_name] = count
            pathways[pathway_name]["total_skills"] += count
        
        return list(pathways.values())
    except Exception as e:
        print(f"Error in get_pathways: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching pathways: {str(e)}")


@router.get("/{skill_id}", response_model=Skill)
def get_skill(skill_id: int, db: Session = Depends(database.get_db)):
    """Get a skill by ID."""
    skill = crud.get_skill_by_id(db, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/", response_model=Skill)
def create_skill(
    skill: SkillCreate, 
    add_to_category: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Create a new skill and optionally add it to a category template."""
    # Check if skill already exists
    existing = crud.get_skill_by_name(db, skill.name)
    if existing:
        raise HTTPException(status_code=400, detail="Skill already exists")
    
    # Create the skill
    new_skill = crud.create_skill(db, skill.model_dump())
    
    # If add_to_category is provided, add the skill to that category's template
    if add_to_category:
        # Check if already in template
        existing_template = db.query(CategorySkillTemplate).filter(
            CategorySkillTemplate.category == add_to_category,
            CategorySkillTemplate.skill_id == new_skill.id
        ).first()
        
        if not existing_template:
            # Add to category template
            template_entry = CategorySkillTemplate(
                category=add_to_category,
                skill_id=new_skill.id,
                is_required=False
            )
            db.add(template_entry)
            db.commit()
    
    return new_skill


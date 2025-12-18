"""API routes for managing role requirements (band-based skill requirements)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from collections import defaultdict
from app.db import database
from app.db.models import RoleRequirement, Skill, RatingEnum, CategorySkillTemplate
from app.api.dependencies import get_admin_user, User
from pydantic import BaseModel

router = APIRouter(prefix="/api/role-requirements", tags=["role-requirements"])

# Standard bands in order
BANDS = ["A", "B", "C", "L1", "L2", "L3", "U"]


class RoleRequirementCreate(BaseModel):
    band: str
    skill_id: int
    required_rating: RatingEnum
    is_required: bool = True


class RoleRequirementResponse(BaseModel):
    id: int
    band: str
    skill_id: int
    skill_name: str
    required_rating: str
    is_required: bool

    class Config:
        from_attributes = True


class BulkUpdateRequest(BaseModel):
    band_requirements: Dict[str, str]  # band -> required_rating


class PathwaySkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    band_requirements: Dict[str, str]  # band -> required_rating


@router.post("", response_model=RoleRequirementResponse)
def create_role_requirement(
    requirement: RoleRequirementCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new role requirement (admin only)."""
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == requirement.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if requirement already exists
    existing = db.query(RoleRequirement).filter(
        RoleRequirement.band == requirement.band,
        RoleRequirement.skill_id == requirement.skill_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Role requirement already exists for this band and skill")
    
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
        skill_name=skill.name,
        required_rating=db_requirement.required_rating.value,
        is_required=db_requirement.is_required,
    )


@router.get("", response_model=List[RoleRequirementResponse])
def get_role_requirements(
    band: Optional[str] = None,
    skill_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all role requirements with optional filters (admin only)."""
    query = db.query(RoleRequirement)
    
    if band:
        query = query.filter(RoleRequirement.band == band)
    if skill_id:
        query = query.filter(RoleRequirement.skill_id == skill_id)
    
    requirements = query.all()
    
    result = []
    for req in requirements:
        skill = db.query(Skill).filter(Skill.id == req.skill_id).first()
        result.append(RoleRequirementResponse(
            id=req.id,
            band=req.band,
            skill_id=req.skill_id,
            skill_name=skill.name if skill else "Unknown",
            required_rating=req.required_rating.value,
            is_required=req.is_required,
        ))
    
    return result


@router.put("/{requirement_id}", response_model=RoleRequirementResponse)
def update_role_requirement(
    requirement_id: int,
    update: RoleRequirementCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a role requirement (admin only)."""
    requirement = db.query(RoleRequirement).filter(RoleRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Role requirement not found")
    
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == update.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    requirement.band = update.band
    requirement.skill_id = update.skill_id
    requirement.required_rating = update.required_rating
    requirement.is_required = update.is_required
    
    db.commit()
    db.refresh(requirement)
    
    return RoleRequirementResponse(
        id=requirement.id,
        band=requirement.band,
        skill_id=requirement.skill_id,
        skill_name=skill.name,
        required_rating=requirement.required_rating.value,
        is_required=requirement.is_required,
    )


@router.delete("/{requirement_id}")
def delete_role_requirement(
    requirement_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a role requirement (admin only)."""
    requirement = db.query(RoleRequirement).filter(RoleRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Role requirement not found")
    
    db.delete(requirement)
    db.commit()
    
    return {"message": "Role requirement deleted successfully"}


@router.get("/pathways", response_model=Dict[str, List[PathwaySkillResponse]])
def get_pathways(
    category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all career pathways grouped by skill category (admin only).
    
    Returns skills with their required levels for each band.
    """
    # Get all role requirements
    requirements = db.query(RoleRequirement).all()
    
    # Build a map of skill_id -> {band -> rating}
    skill_requirements: Dict[int, Dict[str, str]] = defaultdict(dict)
    for req in requirements:
        skill_requirements[req.skill_id][req.band] = req.required_rating.value
    
    # Get all skills that have requirements
    skill_ids = list(skill_requirements.keys())
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all() if skill_ids else []
    
    # Group by category
    pathways: Dict[str, List[PathwaySkillResponse]] = defaultdict(list)
    for skill in skills:
        cat = skill.category or "Uncategorized"
        if category and cat != category:
            continue
        pathways[cat].append(PathwaySkillResponse(
            skill_id=skill.id,
            skill_name=skill.name,
            skill_category=skill.category,
            band_requirements=skill_requirements[skill.id],
        ))
    
    # Sort skills within each category
    for cat in pathways:
        pathways[cat].sort(key=lambda x: x.skill_name)
    
    return dict(pathways)


@router.post("/bulk-update/{skill_id}")
def bulk_update_skill_requirements(
    skill_id: int,
    update: BulkUpdateRequest,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Bulk update requirements for a skill across all bands (admin only).
    
    This will create, update, or delete requirements as needed.
    """
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Get existing requirements for this skill
    existing = db.query(RoleRequirement).filter(RoleRequirement.skill_id == skill_id).all()
    existing_map = {req.band: req for req in existing}
    
    created = 0
    updated = 0
    deleted = 0
    
    for band in BANDS:
        rating = update.band_requirements.get(band)
        existing_req = existing_map.get(band)
        
        if rating:
            # Validate rating
            try:
                rating_enum = RatingEnum(rating)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rating: {rating}")
            
            if existing_req:
                # Update existing
                existing_req.required_rating = rating_enum
                updated += 1
            else:
                # Create new
                new_req = RoleRequirement(
                    band=band,
                    skill_id=skill_id,
                    required_rating=rating_enum,
                    is_required=True,
                )
                db.add(new_req)
                created += 1
        elif existing_req:
            # Delete if no rating provided but exists
            db.delete(existing_req)
            deleted += 1
    
    db.commit()
    
    return {
        "message": f"Updated requirements for {skill.name}",
        "created": created,
        "updated": updated,
        "deleted": deleted,
    }


@router.post("/add-skill")
def add_skill_to_pathway(
    skill_id: int,
    category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Add a skill to career pathways with default requirements (admin only).
    
    Creates default requirements for all bands based on progression:
    A=Beginner, B=Developing, C=Intermediate, L1=Advanced, L2+=Expert
    """
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if skill already has requirements
    existing = db.query(RoleRequirement).filter(RoleRequirement.skill_id == skill_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Skill already has pathway requirements")
    
    # Default progression
    default_ratings = {
        "A": RatingEnum.BEGINNER,
        "B": RatingEnum.DEVELOPING,
        "C": RatingEnum.INTERMEDIATE,
        "L1": RatingEnum.ADVANCED,
        "L2": RatingEnum.EXPERT,
        "L3": RatingEnum.EXPERT,
        "U": RatingEnum.EXPERT,
    }
    
    for band, rating in default_ratings.items():
        req = RoleRequirement(
            band=band,
            skill_id=skill_id,
            required_rating=rating,
            is_required=True,
        )
        db.add(req)
        
    # Update skill category if provided and different
    if category and skill.category != category:
        skill.category = category
    
    db.commit()
    
    return {
        "message": f"Added {skill.name} to career pathways with default requirements",
        "skill_id": skill_id,
        "skill_name": skill.name,
    }


@router.delete("/remove-skill/{skill_id}")
def remove_skill_from_pathway(
    skill_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Remove a skill from career pathways (delete all band requirements) (admin only)."""
    # Verify skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Delete all requirements for this skill
    deleted = db.query(RoleRequirement).filter(RoleRequirement.skill_id == skill_id).delete()
    db.commit()
    
    return {
        "message": f"Removed {skill.name} from career pathways",
        "deleted_requirements": deleted,
    }


@router.post("/add-all-skills")
def add_all_skills_to_pathways(
    pathway: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Add skills to career pathways with default requirements (admin only).
    
    If pathway is provided, adds skills that have that pathway field value,
    or falls back to category template if no pathway field match.
    Otherwise, adds ALL skills.
    Skills are organized by their skill category.
    """
    # Get skills based on pathway filter
    if pathway:
        # First try to get skills by pathway field
        pathway_skills = db.query(Skill).filter(Skill.pathway == pathway).all()
        
        # If no skills found by pathway, try category template
        if not pathway_skills:
            pathway_skills = (
                db.query(Skill)
                .join(CategorySkillTemplate, CategorySkillTemplate.skill_id == Skill.id)
                .filter(CategorySkillTemplate.category == pathway)
                .all()
            )
        
        all_skills = pathway_skills
    else:
        # Get all skills
        all_skills = db.query(Skill).all()
    
    # Get skills that already have requirements
    existing_skill_ids = set(
        req.skill_id for req in db.query(RoleRequirement.skill_id).distinct().all()
    )
    
    # Default progression
    default_ratings = {
        "A": RatingEnum.BEGINNER,
        "B": RatingEnum.DEVELOPING,
        "C": RatingEnum.INTERMEDIATE,
        "L1": RatingEnum.ADVANCED,
        "L2": RatingEnum.EXPERT,
        "L3": RatingEnum.EXPERT,
        "U": RatingEnum.EXPERT,
    }
    
    added_count = 0
    skipped_count = 0
    added_skills = []
    
    for skill in all_skills:
        if skill.id in existing_skill_ids:
            skipped_count += 1
            continue
        
        # Add requirements for all bands
        for band, rating in default_ratings.items():
            req = RoleRequirement(
                band=band,
                skill_id=skill.id,
                required_rating=rating,
                is_required=True,
            )
            db.add(req)
        
        added_count += 1
        added_skills.append({
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category or "Uncategorized",
        })
    
    db.commit()
    
    pathway_msg = f" from pathway '{pathway}'" if pathway else ""
    return {
        "message": f"Added {added_count} skills{pathway_msg} to career pathways with default requirements",
        "added": added_count,
        "skipped": skipped_count,
        "added_skills": added_skills,
        "pathway": pathway,
    }


@router.get("/pathways-list")
def get_pathways_list(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get list of all available pathways with skill counts.
    
    Pathways are determined by the 'pathway' field on skills (e.g., Consulting, Technical).
    Falls back to CategorySkillTemplate categories if no pathway field is set.
    """
    # Get all distinct pathways from Skills table
    skill_pathways = [p[0] for p in db.query(Skill.pathway).filter(Skill.pathway.isnot(None)).distinct().all()]
    
    # Also get categories from CategorySkillTemplate as fallback
    template_categories = [c[0] for c in db.query(CategorySkillTemplate.category).distinct().all()]
    
    # Combine: prefer pathways, add template categories that aren't already pathways
    all_pathways = sorted(list(set(skill_pathways + template_categories)))
    
    result = []
    for pathway in all_pathways:
        # Count total skills in this pathway
        # First check if it's a pathway field match
        total_skills = (
            db.query(Skill)
            .filter(Skill.pathway == pathway)
            .count()
        )
        
        # If no skills found by pathway, check by category template
        if total_skills == 0:
            total_skills = (
                db.query(Skill)
                .join(CategorySkillTemplate, CategorySkillTemplate.skill_id == Skill.id)
                .filter(CategorySkillTemplate.category == pathway)
                .count()
            )
        
        # Count skills already in role requirements
        skills_in_requirements = (
            db.query(RoleRequirement.skill_id)
            .join(Skill, Skill.id == RoleRequirement.skill_id)
            .filter((Skill.pathway == pathway) | (Skill.category == pathway))
            .distinct()
            .count()
        )
        
        # Get skill categories within this pathway
        skill_categories = [
            c[0] for c in db.query(Skill.category)
            .filter(Skill.pathway == pathway)
            .filter(Skill.category.isnot(None))
            .distinct()
            .all()
        ]
        
        if not skill_categories:
            skill_categories = [pathway]
        
        result.append({
            "pathway": pathway,
            "total_skills": total_skills,
            "skills_in_requirements": skills_in_requirements,
            "skills_remaining": total_skills - skills_in_requirements,
            "skill_categories": skill_categories,
        })
    
    # Filter out pathways with 0 skills
    result = [r for r in result if r["total_skills"] > 0]
    
    return result


@router.get("/pathway/{pathway_name}/skills")
def get_pathway_skills(
    pathway_name: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get skills for a specific pathway grouped by skill category.
    
    Returns skills that:
    1. Have the pathway field matching pathway_name, OR
    2. Belong to the pathway's category template
    3. Have role requirements configured
    """
    # First try to get skills by pathway field
    pathway_skills = db.query(Skill).filter(Skill.pathway == pathway_name).all()
    pathway_skill_ids = [s.id for s in pathway_skills]
    
    # If no skills found by pathway, try category template
    if not pathway_skill_ids:
        template_skill_ids = (
            db.query(CategorySkillTemplate.skill_id)
            .filter(CategorySkillTemplate.category == pathway_name)
            .all()
        )
        pathway_skill_ids = [s[0] for s in template_skill_ids]
    
    if not pathway_skill_ids:
        return {}
    
    # Get role requirements for these skills
    requirements = (
        db.query(RoleRequirement)
        .filter(RoleRequirement.skill_id.in_(pathway_skill_ids))
        .all()
    )
    
    # Build a map of skill_id -> {band -> rating}
    skill_requirements: Dict[int, Dict[str, str]] = defaultdict(dict)
    for req in requirements:
        skill_requirements[req.skill_id][req.band] = req.required_rating.value
    
    # Get skills that have requirements
    skill_ids_with_requirements = list(skill_requirements.keys())
    if not skill_ids_with_requirements:
        return {}
    
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids_with_requirements)).all()
    
    # Group by skill category
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for skill in skills:
        cat = skill.category or "Uncategorized"
        grouped[cat].append({
            "skill_id": skill.id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "band_requirements": skill_requirements[skill.id],
        })
    
    # Sort skills within each category
    for cat in grouped:
        grouped[cat].sort(key=lambda x: x["skill_name"])
    
    return dict(grouped)


@router.get("/pathway/{pathway_name}/skills/public")
def get_pathway_skills_public(
    pathway_name: str,
    db: Session = Depends(database.get_db),
):
    """Get skills for a specific pathway grouped by skill category (public endpoint for managers).
    
    Returns skills that:
    1. Have the pathway field matching pathway_name, OR
    2. Belong to the pathway's category template
    3. Have role requirements configured
    """
    # First try to get skills by pathway field
    pathway_skills = db.query(Skill).filter(Skill.pathway == pathway_name).all()
    pathway_skill_ids = [s.id for s in pathway_skills]
    
    # If no skills found by pathway, try category template
    if not pathway_skill_ids:
        template_skill_ids = (
            db.query(CategorySkillTemplate.skill_id)
            .filter(CategorySkillTemplate.category == pathway_name)
            .all()
        )
        pathway_skill_ids = [s[0] for s in template_skill_ids]
    
    if not pathway_skill_ids:
        return {}
    
    # Get role requirements for these skills
    requirements = (
        db.query(RoleRequirement)
        .filter(RoleRequirement.skill_id.in_(pathway_skill_ids))
        .all()
    )
    
    # Build a map of skill_id -> {band -> rating}
    skill_requirements: Dict[int, Dict[str, str]] = defaultdict(dict)
    for req in requirements:
        skill_requirements[req.skill_id][req.band] = req.required_rating.value
    
    # Get skills that have requirements
    skill_ids_with_requirements = list(skill_requirements.keys())
    if not skill_ids_with_requirements:
        return {}
    
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids_with_requirements)).all()
    
    # Group by skill category
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for skill in skills:
        cat = skill.category or "Uncategorized"
        grouped[cat].append({
            "skill_id": skill.id,
            "skill_name": skill.name,
            "skill_category": skill.category,
            "band_requirements": skill_requirements[skill.id],
        })
    
    # Sort skills within each category
    for cat in grouped:
        grouped[cat].sort(key=lambda x: x["skill_name"])
    
    return dict(grouped)

"""API routes for admin operations (Excel uploads)."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from typing import List, Optional
import re
from app.db import database, crud
from app.schemas import UploadResponse
from app.db.models import RatingEnum

router = APIRouter(prefix="/api/admin", tags=["admin"])

MAX_ROWS = 10000


def parse_rating(rating_str: str) -> RatingEnum:
    """Parse rating string to RatingEnum."""
    if not rating_str:
        return RatingEnum.BEGINNER
    
    rating_str = str(rating_str).strip()
    rating_lower = rating_str.lower()
    
    if rating_lower in ["beginner", "beg", "b", "1"]:
        return RatingEnum.BEGINNER
    elif rating_lower in ["developing", "dev", "d", "2"]:
        return RatingEnum.DEVELOPING
    elif rating_lower in ["intermediate", "int", "i", "mid", "3"]:
        return RatingEnum.INTERMEDIATE
    elif rating_lower in ["advanced", "adv", "a", "4"]:
        return RatingEnum.ADVANCED
    elif rating_lower in ["expert", "exp", "e", "5"]:
        return RatingEnum.EXPERT
    else:
        return RatingEnum.BEGINNER


@router.post("/upload-skills", response_model=UploadResponse)
async def upload_skills(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """
    Upload Excel/CSV file to populate master skills list.
    Expected columns: name (required), description (optional)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Expected .xlsx, .xls, or .csv")

    try:
        contents = await file.read()
        
        if file_ext == "csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents), engine="openpyxl")

        df.columns = df.columns.str.strip().str.lower()

        if len(df) > MAX_ROWS:
            raise HTTPException(status_code=400, detail=f"File contains {len(df)} rows. Maximum allowed is {MAX_ROWS}.")

        if "name" not in df.columns:
            raise HTTPException(status_code=400, detail="Missing required column: 'name'")

        rows_processed = 0
        rows_created = 0
        rows_updated = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                skill_name = str(row["name"]).strip()
                if not skill_name:
                    errors.append(f"Row {idx + 2}: Empty skill name")
                    continue

                description = None
                if "description" in df.columns and pd.notna(row.get("description")):
                    description = str(row["description"]).strip() or None
                
                category = None
                if "category" in df.columns and pd.notna(row.get("category")):
                    category = str(row["category"]).strip() or None

                existing = crud.get_skill_by_name(db, skill_name)
                if existing:
                    rows_updated += 1
                else:
                    rows_created += 1

                crud.upsert_skill(db, skill_name, description, category)
                rows_processed += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")

        return UploadResponse(
            message="Skills uploaded successfully",
            rows_processed=rows_processed,
            rows_created=rows_created,
            rows_updated=rows_updated,
            errors=errors if errors else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/upload-skills-with-requirements", response_model=UploadResponse)
async def upload_skills_with_requirements(
    file: UploadFile = File(...),
    pathway: Optional[str] = Query(None, description="Pathway name (e.g., Consulting, Technical, Legal)"),
    delete_existing: bool = False,
    db: Session = Depends(database.get_db),
):
    """
    Upload Excel/CSV file to populate skills with band requirements.
    
    Supports 3-level hierarchy: Pathway -> Category -> Skills
    
    Expected format:
    | Skill | A | B | C | L1 | L2 |
    | 1. Category Name | | | | | |
    | Skill Name | Beginner | Developing | Intermediate | Advanced | Expert |
    
    Category rows start with a number and dot (e.g., "1. Core Legal Skills")
    Skill rows have the skill name and rating requirements for each band.
    
    Parameters:
    - pathway: The pathway name (e.g., "Consulting", "Legal", "Technical")
    - delete_existing: If True, deletes all existing skills before import
    """
    from app.db.models import Skill, RoleRequirement, EmployeeSkill, TeamSkillTemplate, CategorySkillTemplate, SkillGapResult, EmployeeTemplateResponse
    from sqlalchemy import text
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Expected .xlsx, .xls, or .csv")

    def normalize_rating(rating_str: str) -> Optional[str]:
        """Normalize rating string to enum value."""
        if not rating_str or str(rating_str).strip().lower() in ['', 'nan', 'none']:
            return None
        rating = str(rating_str).strip().lower()
        mapping = {
            'beginner': 'Beginner',
            'developing': 'Developing',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced',
            'expert': 'Expert',
        }
        return mapping.get(rating)

    def is_category_header(text_val: str) -> bool:
        """Check if row is a category header like '1. Core Legal Skills'"""
        if not text_val:
            return False
        return bool(re.match(r'^\d+\.\s*.+$', str(text_val).strip()))

    def extract_category_name(text_val: str) -> str:
        """Extract category name from header like '1. Core Legal Skills'"""
        match = re.match(r'^\d+\.\s*(.+)$', str(text_val).strip())
        return match.group(1).strip() if match else str(text_val).strip()

    try:
        contents = await file.read()
        
        if file_ext == "csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents), engine="openpyxl")

        df.columns = df.columns.str.strip()
        
        # Find the skill column
        skill_col = df.columns[0]
        for col in df.columns:
            if col.lower() in ['skill', 'name', 'skill name', 'competency']:
                skill_col = col
                break
        
        # Find band columns
        band_cols = {}
        for col in df.columns:
            col_upper = str(col).strip().upper()
            if col_upper in ['A', 'B', 'C', 'L1', 'L2']:
                band_cols[col_upper] = col
        
        if not band_cols:
            raise HTTPException(status_code=400, detail="No band columns found. Expected columns: A, B, C, L1, L2")

        # Delete existing data if requested
        if delete_existing:
            db.query(EmployeeTemplateResponse).delete()
            db.query(SkillGapResult).delete()
            db.query(EmployeeSkill).delete()
            db.query(TeamSkillTemplate).delete()
            db.query(RoleRequirement).delete()
            db.query(CategorySkillTemplate).delete()
            db.execute(text("UPDATE courses SET skill_id = NULL"))
            db.execute(text("UPDATE course_assignments SET skill_id = NULL"))
            db.query(Skill).delete()
            db.commit()

        rows_processed = 0
        rows_created = 0
        rows_updated = 0
        requirements_created = 0
        errors = []
        current_category = None

        # Derive pathway from filename if not provided
        if not pathway:
            # Try to extract from filename (e.g., "Consulting_Skills.xlsx" -> "Consulting")
            base_name = file.filename.rsplit('.', 1)[0]
            pathway = base_name.replace('_', ' ').replace('-', ' ').split()[0] if base_name else None

        for idx, row in df.iterrows():
            try:
                skill_name = str(row[skill_col]).strip() if pd.notna(row[skill_col]) else ''
                
                if not skill_name:
                    continue
                
                # Check if this is a category header
                if is_category_header(skill_name):
                    current_category = extract_category_name(skill_name)
                    continue
                
                # Skip if no category yet
                if not current_category:
                    errors.append(f"Row {idx + 2}: Skill '{skill_name}' has no category")
                    continue
                
                # Check if skill exists
                existing_skill = db.query(Skill).filter(Skill.name == skill_name).first()
                
                if existing_skill:
                    skill = existing_skill
                    skill.pathway = pathway
                    skill.category = current_category
                    skill.description = f"{current_category} skill"
                    rows_updated += 1
                else:
                    skill = Skill(
                        name=skill_name,
                        pathway=pathway,
                        category=current_category,
                        description=f"{current_category} skill"
                    )
                    db.add(skill)
                    db.flush()
                    rows_created += 1
                
                # Create/update role requirements for each band
                for band, col_name in band_cols.items():
                    rating_str = row[col_name] if col_name in row.index else None
                    rating = normalize_rating(str(rating_str) if pd.notna(rating_str) else '')
                    
                    if rating:
                        existing_req = db.query(RoleRequirement).filter(
                            RoleRequirement.band == band,
                            RoleRequirement.skill_id == skill.id
                        ).first()
                        
                        if existing_req:
                            existing_req.required_rating = RatingEnum(rating)
                        else:
                            req = RoleRequirement(
                                band=band,
                                skill_id=skill.id,
                                required_rating=RatingEnum(rating),
                                is_required=True
                            )
                            db.add(req)
                            requirements_created += 1
                
                rows_processed += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")

        db.commit()

        pathway_msg = f" for pathway '{pathway}'" if pathway else ""
        return UploadResponse(
            message=f"Skills uploaded successfully{pathway_msg}. Created {requirements_created} band requirements.",
            rows_processed=rows_processed,
            rows_created=rows_created,
            rows_updated=rows_updated,
            errors=errors if errors else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/upload-employee-skills", response_model=UploadResponse)
async def upload_employee_skills(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    """
    Upload Excel/CSV file to populate employee-skill mappings.
    Expected columns: EmployeeID, EmployeeName, SkillName, Rating, YearsExperience (optional)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["xlsx", "xls", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Expected .xlsx, .xls, or .csv")

    try:
        contents = await file.read()
        
        if file_ext == "csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents), engine="openpyxl")

        if len(df) > MAX_ROWS:
            raise HTTPException(status_code=400, detail=f"File contains {len(df)} rows. Maximum allowed is {MAX_ROWS}.")

        required_cols = ["employeeid", "employeename", "skillname", "rating"]
        df.columns = df.columns.str.lower()
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing_cols)}")

        rows_processed = 0
        rows_created = 0
        rows_updated = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                employee_id = str(row["employeeid"]).strip()
                employee_name = str(row["employeename"]).strip()
                skill_name = str(row["skillname"]).strip()
                rating_str = str(row["rating"]).strip()

                if not employee_id or not employee_name or not skill_name:
                    errors.append(f"Row {idx + 2}: Missing required fields")
                    continue

                rating = parse_rating(rating_str)

                years_experience = None
                if "yearsexperience" in df.columns and pd.notna(row.get("yearsexperience")):
                    try:
                        years_experience = float(row["yearsexperience"])
                    except (ValueError, TypeError):
                        pass

                employee = crud.upsert_employee(db, employee_id, employee_name)
                skill = crud.upsert_skill(db, skill_name)

                existing = crud.get_employee_skill(db, employee.id, skill.id)
                if existing:
                    rows_updated += 1
                else:
                    rows_created += 1

                crud.upsert_employee_skill(db, employee.id, skill.id, rating, years_experience, is_interested=False)
                rows_processed += 1

            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")

        return UploadResponse(
            message="Employee skills uploaded successfully",
            rows_processed=rows_processed,
            rows_created=rows_created,
            rows_updated=rows_updated,
            errors=errors if errors else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

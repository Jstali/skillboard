"""Baseline Assignment Service for Manager-Driven Skill Assessment.

Handles automatic assignment of baseline skill levels when an employee
is assigned a Band + Pathway combination.

Band to Baseline Level Mapping:
- Band A → Beginner
- Band B → Developing
- Band C → Intermediate
- Band L1 → Advanced
- Band L2 → Expert
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import (
    Employee, Skill, SkillAssessment, AssessmentHistory,
    PathwaySkill, RatingEnum, AssessmentTypeEnum, AssessorRoleEnum
)


class BaselineService:
    """Service for assigning baseline skill levels based on band and pathway."""
    
    # Band to baseline proficiency level mapping
    BAND_BASELINE_MAP: Dict[str, RatingEnum] = {
        "A": RatingEnum.BEGINNER,
        "B": RatingEnum.DEVELOPING,
        "C": RatingEnum.INTERMEDIATE,
        "L1": RatingEnum.ADVANCED,
        "L2": RatingEnum.EXPERT,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_baseline_level(self, band: str) -> Optional[RatingEnum]:
        """
        Get the baseline proficiency level for a given band.
        
        Args:
            band: The employee's band (A, B, C, L1, L2)
            
        Returns:
            RatingEnum for the baseline level, or None if band not recognized
        """
        return self.BAND_BASELINE_MAP.get(band.upper() if band else "")
    
    def get_pathway_skills(self, pathway: str) -> List[PathwaySkill]:
        """
        Get all skills belonging to a pathway.
        
        Args:
            pathway: The career pathway name
            
        Returns:
            List of PathwaySkill objects
        """
        return self.db.query(PathwaySkill).filter(
            PathwaySkill.pathway == pathway
        ).order_by(PathwaySkill.display_order).all()
    
    def assign_baseline(
        self,
        employee_id: int,
        band: str,
        pathway: str,
        skip_existing: bool = True
    ) -> List[SkillAssessment]:
        """
        Assign baseline skill assessments for an employee based on band and pathway.
        
        Args:
            employee_id: The employee's ID
            band: The employee's band (A, B, C, L1, L2)
            pathway: The career pathway name
            skip_existing: If True, skip skills that already have assessments
            
        Returns:
            List of created SkillAssessment objects
        """
        baseline_level = self.get_baseline_level(band)
        if not baseline_level:
            raise ValueError(f"Invalid band: {band}. Must be one of: A, B, C, L1, L2")
        
        # Get all skills for the pathway
        pathway_skills = self.get_pathway_skills(pathway)
        if not pathway_skills:
            # If no pathway skills defined, return empty list
            return []
        
        created_assessments = []
        now = datetime.utcnow()
        
        for ps in pathway_skills:
            # Check if assessment already exists
            if skip_existing:
                existing = self.db.query(SkillAssessment).filter(
                    SkillAssessment.employee_id == employee_id,
                    SkillAssessment.skill_id == ps.skill_id
                ).first()
                
                if existing:
                    continue
            
            # Create the baseline assessment
            assessment = SkillAssessment(
                employee_id=employee_id,
                skill_id=ps.skill_id,
                level=baseline_level,
                assessment_type=AssessmentTypeEnum.BASELINE,
                assessor_id=None,  # SYSTEM assessment
                assessor_role=AssessorRoleEnum.SYSTEM,
                comments=f"Baseline assessment for Band {band} + {pathway} pathway",
                assessed_at=now,
                created_at=now,
                updated_at=now
            )
            self.db.add(assessment)
            
            # Create history record
            history = AssessmentHistory(
                employee_id=employee_id,
                skill_id=ps.skill_id,
                previous_level=None,  # First assessment
                new_level=baseline_level,
                assessment_type=AssessmentTypeEnum.BASELINE,
                assessor_id=None,
                assessor_role=AssessorRoleEnum.SYSTEM,
                comments=f"Baseline assessment for Band {band} + {pathway} pathway",
                assessed_at=now
            )
            self.db.add(history)
            
            created_assessments.append(assessment)
        
        self.db.commit()
        
        # Refresh to get IDs
        for assessment in created_assessments:
            self.db.refresh(assessment)
        
        return created_assessments
    
    def assign_baseline_for_employee(self, employee: Employee) -> List[SkillAssessment]:
        """
        Assign baseline assessments for an employee using their current band and pathway.
        
        Args:
            employee: The Employee object
            
        Returns:
            List of created SkillAssessment objects
        """
        if not employee.band:
            raise ValueError(f"Employee {employee.employee_id} has no band assigned")
        
        if not employee.pathway:
            raise ValueError(f"Employee {employee.employee_id} has no pathway assigned")
        
        return self.assign_baseline(
            employee_id=employee.id,
            band=employee.band,
            pathway=employee.pathway
        )


def get_baseline_service(db: Session) -> BaselineService:
    """Factory function to create BaselineService instance."""
    return BaselineService(db)

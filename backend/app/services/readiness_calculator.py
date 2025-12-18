"""Readiness Calculator Service for Manager-Driven Skill Assessment.

Calculates promotion readiness scores by comparing current assessed skills
against the requirements for the target band.
"""
from typing import List, Optional, Dict
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.db.models import (
    Employee, SkillAssessment, RoleRequirement, Skill,
    RatingEnum
)


# Numeric values for rating comparison
RATING_VALUES: Dict[RatingEnum, int] = {
    RatingEnum.BEGINNER: 1,
    RatingEnum.DEVELOPING: 2,
    RatingEnum.INTERMEDIATE: 3,
    RatingEnum.ADVANCED: 4,
    RatingEnum.EXPERT: 5,
}

# Band progression order
BAND_ORDER = ["A", "B", "C", "L1", "L2"]


@dataclass
class SkillGapInfo:
    """Information about a skill gap."""
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    current_level: Optional[str]
    current_level_value: int
    required_level: str
    required_level_value: int
    gap_value: int  # Negative means below requirement
    meets_requirement: bool


@dataclass
class ReadinessResult:
    """Result of readiness calculation."""
    employee_id: int
    current_band: str
    target_band: str
    readiness_score: float  # 0-100 percentage
    total_required_skills: int
    skills_meeting_requirement: int
    skills_below_requirement: int
    skill_gaps: List[SkillGapInfo]


class ReadinessCalculator:
    """Calculates promotion readiness based on skill assessments."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_next_band(self, current_band: str) -> Optional[str]:
        """Get the next band in the progression."""
        if not current_band:
            return "A"
        
        current_upper = current_band.upper()
        if current_upper not in BAND_ORDER:
            return None
        
        idx = BAND_ORDER.index(current_upper)
        if idx >= len(BAND_ORDER) - 1:
            return None  # Already at highest band
        
        return BAND_ORDER[idx + 1]
    
    def get_rating_value(self, rating: Optional[RatingEnum]) -> int:
        """Convert rating enum to numeric value."""
        if rating is None:
            return 0
        return RATING_VALUES.get(rating, 0)
    
    def calculate_readiness(
        self,
        employee_id: int,
        target_band: Optional[str] = None
    ) -> ReadinessResult:
        """
        Calculate readiness score for an employee toward a target band.
        
        Args:
            employee_id: The employee's ID
            target_band: Target band (defaults to next band)
            
        Returns:
            ReadinessResult with score and gap details
        """
        # Get employee
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        current_band = employee.band or "A"
        
        # Determine target band
        if not target_band:
            target_band = self.get_next_band(current_band)
            if not target_band:
                # Already at highest band
                return ReadinessResult(
                    employee_id=employee_id,
                    current_band=current_band,
                    target_band=current_band,
                    readiness_score=100.0,
                    total_required_skills=0,
                    skills_meeting_requirement=0,
                    skills_below_requirement=0,
                    skill_gaps=[]
                )
        
        # Get requirements for target band
        requirements = self.db.query(RoleRequirement).filter(
            RoleRequirement.band == target_band,
            RoleRequirement.is_required == True
        ).all()
        
        if not requirements:
            # No requirements defined for target band
            return ReadinessResult(
                employee_id=employee_id,
                current_band=current_band,
                target_band=target_band,
                readiness_score=100.0,
                total_required_skills=0,
                skills_meeting_requirement=0,
                skills_below_requirement=0,
                skill_gaps=[]
            )
        
        # Get employee's current assessments
        assessments = self.db.query(SkillAssessment).filter(
            SkillAssessment.employee_id == employee_id
        ).all()
        
        # Create lookup by skill_id
        assessment_by_skill = {a.skill_id: a for a in assessments}
        
        # Calculate gaps
        skill_gaps = []
        skills_meeting = 0
        skills_below = 0
        
        for req in requirements:
            skill = self.db.query(Skill).filter(Skill.id == req.skill_id).first()
            skill_name = skill.name if skill else f"Skill {req.skill_id}"
            skill_category = skill.category if skill else None
            
            required_value = self.get_rating_value(req.required_rating)
            
            assessment = assessment_by_skill.get(req.skill_id)
            if assessment:
                current_value = self.get_rating_value(assessment.level)
                current_level = assessment.level.value if assessment.level else None
            else:
                current_value = 0
                current_level = None
            
            gap_value = current_value - required_value
            meets_requirement = current_value >= required_value
            
            if meets_requirement:
                skills_meeting += 1
            else:
                skills_below += 1
            
            skill_gaps.append(SkillGapInfo(
                skill_id=req.skill_id,
                skill_name=skill_name,
                skill_category=skill_category,
                current_level=current_level,
                current_level_value=current_value,
                required_level=req.required_rating.value if req.required_rating else None,
                required_level_value=required_value,
                gap_value=gap_value,
                meets_requirement=meets_requirement
            ))
        
        # Calculate readiness score
        total_required = len(requirements)
        readiness_score = (skills_meeting / total_required * 100) if total_required > 0 else 100.0
        
        return ReadinessResult(
            employee_id=employee_id,
            current_band=current_band,
            target_band=target_band,
            readiness_score=round(readiness_score, 1),
            total_required_skills=total_required,
            skills_meeting_requirement=skills_meeting,
            skills_below_requirement=skills_below,
            skill_gaps=skill_gaps
        )
    
    def get_skill_gaps(
        self,
        employee_id: int,
        target_band: Optional[str] = None
    ) -> List[SkillGapInfo]:
        """
        Get skill gaps for an employee (skills below requirement only).
        
        Args:
            employee_id: The employee's ID
            target_band: Target band (defaults to next band)
            
        Returns:
            List of SkillGapInfo for skills below requirement
        """
        result = self.calculate_readiness(employee_id, target_band)
        return [gap for gap in result.skill_gaps if not gap.meets_requirement]


def get_readiness_calculator(db: Session) -> ReadinessCalculator:
    """Factory function to create ReadinessCalculator instance."""
    return ReadinessCalculator(db)

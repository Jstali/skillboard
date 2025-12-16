"""Capability Alignment Service for alignment calculations.

This service provides capability alignment calculations, comparing
employee skills against capability requirements.
"""
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models import Employee, EmployeeSkill, Skill, RoleRequirement, TeamSkillTemplate
from app.services.proficiency_display import proficiency_service


class SkillRequirement(BaseModel):
    """Skill requirement for a capability."""
    skill_id: int
    skill_name: str
    required_level: str
    required_numeric: int


class SkillComparison(BaseModel):
    """Comparison of actual vs required skill level."""
    skill_id: int
    skill_name: str
    category: Optional[str]
    required_level: str
    actual_level: Optional[str]
    required_numeric: int
    actual_numeric: int
    meets_requirement: bool
    gap: int  # Positive = below requirement


class AlignmentResult(BaseModel):
    """Result of capability alignment calculation."""
    capability: str
    alignment_score: float  # 0-100
    required_skills_met: int
    required_skills_total: int
    average_proficiency: float
    skill_comparisons: List[SkillComparison]
    gaps: List[SkillComparison]  # Only skills with gaps


class CapabilityAlignmentCalculator:
    """
    Calculator for capability alignment.
    
    Compares employee skills against capability requirements
    and calculates alignment scores.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def compare_skills_to_requirements(
        self,
        employee_skills: Dict[int, str],  # skill_id -> rating
        requirements: Dict[int, str]  # skill_id -> required_level
    ) -> List[SkillComparison]:
        """
        Compare employee skills against requirements.
        
        Args:
            employee_skills: Dict mapping skill_id to rating
            requirements: Dict mapping skill_id to required level
            
        Returns:
            List of skill comparisons
        """
        comparisons = []
        
        for skill_id, required_level in requirements.items():
            actual_level = employee_skills.get(skill_id)
            required_numeric = proficiency_service.get_numeric_value(required_level)
            actual_numeric = proficiency_service.get_numeric_value(actual_level) if actual_level else 0
            
            meets_req = actual_numeric >= required_numeric if actual_level else False
            gap = required_numeric - actual_numeric
            
            comparisons.append(SkillComparison(
                skill_id=skill_id,
                skill_name=f"Skill_{skill_id}",  # Will be populated from DB if available
                category=None,
                required_level=required_level,
                actual_level=actual_level,
                required_numeric=required_numeric,
                actual_numeric=actual_numeric,
                meets_requirement=meets_req,
                gap=gap
            ))
        
        return comparisons

    
    def calculate_alignment_score(
        self,
        comparisons: List[SkillComparison]
    ) -> Tuple[float, int, int]:
        """
        Calculate alignment score from skill comparisons.
        
        Args:
            comparisons: List of skill comparisons
            
        Returns:
            Tuple of (alignment_score, skills_met, total_skills)
        """
        if not comparisons:
            return 100.0, 0, 0
        
        skills_met = sum(1 for c in comparisons if c.meets_requirement)
        total_skills = len(comparisons)
        
        alignment_score = (skills_met / total_skills * 100) if total_skills > 0 else 100.0
        
        return round(alignment_score, 2), skills_met, total_skills
    
    def identify_skill_gaps(
        self,
        comparisons: List[SkillComparison]
    ) -> List[SkillComparison]:
        """
        Identify skills with gaps (below requirements).
        
        Args:
            comparisons: List of skill comparisons
            
        Returns:
            List of comparisons where there's a gap
        """
        return [c for c in comparisons if c.gap > 0]
    
    def calculate_average_proficiency(
        self,
        comparisons: List[SkillComparison]
    ) -> float:
        """
        Calculate average proficiency from comparisons.
        
        Args:
            comparisons: List of skill comparisons
            
        Returns:
            Average proficiency (1-5 scale)
        """
        if not comparisons:
            return 0.0
        
        # Only count skills that have actual ratings
        rated_skills = [c for c in comparisons if c.actual_level is not None]
        if not rated_skills:
            return 0.0
        
        total = sum(c.actual_numeric for c in rated_skills)
        return round(total / len(rated_skills), 2)
    
    def get_alignment_result(
        self,
        capability: str,
        employee_skills: Dict[int, str],
        requirements: Dict[int, str]
    ) -> AlignmentResult:
        """
        Get complete alignment result for a capability.
        
        Args:
            capability: Capability name
            employee_skills: Dict mapping skill_id to rating
            requirements: Dict mapping skill_id to required level
            
        Returns:
            Complete alignment result
        """
        comparisons = self.compare_skills_to_requirements(employee_skills, requirements)
        score, met, total = self.calculate_alignment_score(comparisons)
        gaps = self.identify_skill_gaps(comparisons)
        avg_prof = self.calculate_average_proficiency(comparisons)
        
        return AlignmentResult(
            capability=capability,
            alignment_score=score,
            required_skills_met=met,
            required_skills_total=total,
            average_proficiency=avg_prof,
            skill_comparisons=comparisons,
            gaps=gaps
        )


class CapabilityAlignmentService:
    """
    Service for capability alignment operations with database access.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.calculator = CapabilityAlignmentCalculator(db)
    
    def get_employee_alignment(self, employee_id: str) -> Optional[AlignmentResult]:
        """
        Get capability alignment for an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            Alignment result or None if employee not found
        """
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return None
        
        capability = employee.home_capability or employee.capability
        if not capability:
            return None
        
        # Get employee skills
        employee_skills = {}
        for es in self.db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id
        ).all():
            if es.rating:
                employee_skills[es.skill_id] = es.rating.value
        
        # Get requirements
        requirements = self._get_requirements(employee)
        
        # Calculate alignment
        result = self.calculator.get_alignment_result(
            capability, employee_skills, requirements
        )
        
        # Enrich with skill names from database
        self._enrich_skill_names(result.skill_comparisons)
        self._enrich_skill_names(result.gaps)
        
        return result
    
    def _get_requirements(self, employee: Employee) -> Dict[int, str]:
        """Get skill requirements for an employee."""
        requirements = {}
        
        # From band requirements
        if employee.band:
            for req in self.db.query(RoleRequirement).filter(
                RoleRequirement.band == employee.band,
                RoleRequirement.is_required == True
            ).all():
                requirements[req.skill_id] = req.required_rating.value
        
        # From team templates
        if employee.team:
            for tmpl in self.db.query(TeamSkillTemplate).filter(
                TeamSkillTemplate.team == employee.team,
                TeamSkillTemplate.is_required == True
            ).all():
                if tmpl.skill_id not in requirements:
                    requirements[tmpl.skill_id] = "Intermediate"
        
        return requirements
    
    def _enrich_skill_names(self, comparisons: List[SkillComparison]) -> None:
        """Enrich comparisons with skill names from database."""
        for comp in comparisons:
            skill = self.db.query(Skill).filter(Skill.id == comp.skill_id).first()
            if skill:
                comp.skill_name = skill.name
                comp.category = skill.category


# Factory function
def get_capability_alignment_service(db: Session) -> CapabilityAlignmentService:
    """Create a CapabilityAlignmentService instance."""
    return CapabilityAlignmentService(db)

"""Skill Board Service for employee skill operations.

This service provides employee skill data, capability alignment calculations,
and skill gap analysis for the Skill Board views.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import Employee, EmployeeSkill, Skill, RoleRequirement, TeamSkillTemplate
from app.services.proficiency_display import proficiency_service, ProficiencyDisplay


class SkillGap(BaseModel):
    """Skill gap information."""
    skill_id: int
    skill_name: str
    category: Optional[str]
    required_level: str
    actual_level: Optional[str]
    gap_value: int  # Positive = below requirement
    priority: str  # High, Medium, Low


class SkillWithProficiency(BaseModel):
    """Skill with proficiency information."""
    skill_id: int
    skill_name: str
    category: Optional[str]
    rating: Optional[str]
    rating_display: ProficiencyDisplay
    years_experience: Optional[float]
    is_required: bool
    meets_requirement: bool


class CapabilityAlignment(BaseModel):
    """Capability alignment calculation result."""
    capability: str
    alignment_score: float  # 0-100
    required_skills_met: int
    required_skills_total: int
    average_proficiency: float


class EmployeeSkillBoard(BaseModel):
    """Complete employee skill board data."""
    employee_id: str
    name: str
    home_capability: Optional[str]
    team: Optional[str]
    skills: List[SkillWithProficiency]
    capability_alignment: Optional[CapabilityAlignment]
    skill_gaps: List[SkillGap]


class SkillBoardService:
    """
    Service for skill board operations.
    
    Provides employee skill data, capability alignment calculations,
    and skill gap analysis.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def get_employee_skills(self, employee_id: str) -> List[SkillWithProficiency]:
        """
        Get all skills for an employee with proficiency information.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            List of skills with proficiency display information
        """
        # Get employee
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return []
        
        # Get employee skills
        employee_skills = self.db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id
        ).all()
        
        # Get required skills for employee's team/band
        required_skill_ids = self._get_required_skill_ids(employee)
        
        skills_with_proficiency = []
        for es in employee_skills:
            skill = es.skill
            rating = es.rating.value if es.rating else None
            is_required = skill.id in required_skill_ids
            
            # Check if meets requirement
            meets_req = True
            if is_required and rating:
                required_level = required_skill_ids.get(skill.id)
                if required_level:
                    meets_req = proficiency_service.meets_requirement(rating, required_level)
            
            skills_with_proficiency.append(SkillWithProficiency(
                skill_id=skill.id,
                skill_name=skill.name,
                category=skill.category,
                rating=rating,
                rating_display=proficiency_service.get_proficiency_display(rating or "Beginner"),
                years_experience=es.years_experience,
                is_required=is_required,
                meets_requirement=meets_req
            ))
        
        return skills_with_proficiency
    
    def _get_required_skill_ids(self, employee: Employee) -> Dict[int, str]:
        """Get required skill IDs and levels for an employee based on band/team."""
        required_skills = {}
        
        # Get requirements from band
        if employee.band:
            requirements = self.db.query(RoleRequirement).filter(
                RoleRequirement.band == employee.band,
                RoleRequirement.is_required == True
            ).all()
            for req in requirements:
                required_skills[req.skill_id] = req.required_rating.value
        
        # Get requirements from team template
        if employee.team:
            templates = self.db.query(TeamSkillTemplate).filter(
                TeamSkillTemplate.team == employee.team,
                TeamSkillTemplate.is_required == True
            ).all()
            for tmpl in templates:
                if tmpl.skill_id not in required_skills:
                    required_skills[tmpl.skill_id] = "Intermediate"  # Default required level
        
        return required_skills
    
    def get_skill_gaps(self, employee_id: str) -> List[SkillGap]:
        """
        Identify skill gaps for an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            List of skill gaps where proficiency is below requirements
        """
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return []
        
        required_skills = self._get_required_skill_ids(employee)
        if not required_skills:
            return []
        
        # Get employee's current skills
        employee_skills = {
            es.skill_id: es for es in self.db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee.id
            ).all()
        }
        
        gaps = []
        for skill_id, required_level in required_skills.items():
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                continue
            
            es = employee_skills.get(skill_id)
            actual_level = es.rating.value if es and es.rating else None
            
            # Calculate gap
            gap_value = proficiency_service.calculate_gap(
                actual_level or "Beginner",
                required_level
            )
            
            # Only include if there's a gap (positive value)
            if gap_value > 0:
                priority = "High" if gap_value >= 2 else "Medium" if gap_value == 1 else "Low"
                gaps.append(SkillGap(
                    skill_id=skill_id,
                    skill_name=skill.name,
                    category=skill.category,
                    required_level=required_level,
                    actual_level=actual_level,
                    gap_value=gap_value,
                    priority=priority
                ))
        
        # Sort by priority (High first)
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        gaps.sort(key=lambda g: priority_order.get(g.priority, 3))
        
        return gaps

    
    def get_capability_alignment(self, employee_id: str) -> Optional[CapabilityAlignment]:
        """
        Calculate capability alignment for an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            Capability alignment score and details, or None if no capability
        """
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return None
        
        capability = employee.home_capability or employee.capability
        if not capability:
            return None
        
        required_skills = self._get_required_skill_ids(employee)
        if not required_skills:
            return CapabilityAlignment(
                capability=capability,
                alignment_score=100.0,
                required_skills_met=0,
                required_skills_total=0,
                average_proficiency=0.0
            )
        
        # Get employee's current skills
        employee_skills = {
            es.skill_id: es for es in self.db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee.id
            ).all()
        }
        
        skills_met = 0
        total_proficiency = 0
        proficiency_count = 0
        
        for skill_id, required_level in required_skills.items():
            es = employee_skills.get(skill_id)
            if es and es.rating:
                actual_level = es.rating.value
                total_proficiency += proficiency_service.get_numeric_value(actual_level)
                proficiency_count += 1
                
                if proficiency_service.meets_requirement(actual_level, required_level):
                    skills_met += 1
        
        total_required = len(required_skills)
        alignment_score = (skills_met / total_required * 100) if total_required > 0 else 100.0
        avg_proficiency = (total_proficiency / proficiency_count) if proficiency_count > 0 else 0.0
        
        return CapabilityAlignment(
            capability=capability,
            alignment_score=round(alignment_score, 2),
            required_skills_met=skills_met,
            required_skills_total=total_required,
            average_proficiency=round(avg_proficiency, 2)
        )
    
    def get_employee_skill_board(self, employee_id: str) -> Optional[EmployeeSkillBoard]:
        """
        Get complete skill board data for an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            Complete skill board data or None if employee not found
        """
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return None
        
        skills = self.get_employee_skills(employee_id)
        skill_gaps = self.get_skill_gaps(employee_id)
        alignment = self.get_capability_alignment(employee_id)
        
        return EmployeeSkillBoard(
            employee_id=employee.employee_id,
            name=employee.name,
            home_capability=employee.home_capability or employee.capability,
            team=employee.team,
            skills=skills,
            capability_alignment=alignment,
            skill_gaps=skill_gaps
        )


# Factory function for creating service with db session
def get_skill_board_service(db: Session) -> SkillBoardService:
    """Create a SkillBoardService instance with the given database session."""
    return SkillBoardService(db)

"""Metrics Service for aggregate capability calculations.

This service provides aggregate skill metrics, distributions,
coverage analysis, and training needs identification.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict

from app.db.models import Employee, EmployeeSkill, Skill, RoleRequirement, TeamSkillTemplate
from app.services.proficiency_display import proficiency_service


class SkillDistribution(BaseModel):
    """Aggregate skill distribution."""
    capability: Optional[str]
    total_employees: int
    skill_counts: Dict[str, int]  # skill_name -> count
    proficiency_distribution: Dict[str, Dict[str, int]]  # skill -> proficiency -> count


class CoverageMetrics(BaseModel):
    """Capability coverage metrics."""
    capability: str
    coverage_percentage: float
    skills_with_coverage: int
    skills_without_coverage: int
    critical_gaps: List[str]


class TrendPoint(BaseModel):
    """Single trend data point."""
    date: str
    skill_count: int
    average_proficiency: float


class TrendData(BaseModel):
    """Skill trend data over time."""
    period: str
    data_points: List[TrendPoint]
    growth_rate: float


class TrainingNeed(BaseModel):
    """Training need identification."""
    skill_name: str
    current_coverage: float
    required_coverage: float
    gap_percentage: float
    priority: str  # High, Medium, Low


class MetricsFilter(BaseModel):
    """Filter criteria for metrics queries."""
    capability: Optional[str] = None
    team: Optional[str] = None
    band: Optional[str] = None


class MetricsService:
    """
    Service for aggregate capability metrics.
    
    Provides skill counts, distributions, coverage analysis,
    and training needs identification.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def get_skill_counts_by_proficiency(
        self,
        filters: Optional[MetricsFilter] = None
    ) -> Dict[str, int]:
        """
        Get skill counts grouped by proficiency level.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            Dict mapping proficiency level to count
        """
        query = self.db.query(EmployeeSkill).join(Employee)
        
        if filters:
            if filters.capability:
                query = query.filter(
                    (Employee.home_capability == filters.capability) |
                    (Employee.capability == filters.capability)
                )
            if filters.team:
                query = query.filter(Employee.team == filters.team)
            if filters.band:
                query = query.filter(Employee.band == filters.band)
        
        # Count by proficiency
        counts = defaultdict(int)
        for es in query.all():
            if es.rating:
                counts[es.rating.value] += 1
        
        # Ensure all levels are present
        for level in proficiency_service.get_all_levels():
            if level not in counts:
                counts[level] = 0
        
        return dict(counts)
    
    def get_capability_distribution(
        self,
        capability: Optional[str] = None
    ) -> SkillDistribution:
        """
        Get skill distribution for a capability or organisation-wide.
        
        Args:
            capability: Optional capability to filter by
            
        Returns:
            Skill distribution data
        """
        # Get employees
        emp_query = self.db.query(Employee)
        if capability:
            emp_query = emp_query.filter(
                (Employee.home_capability == capability) |
                (Employee.capability == capability)
            )
        employees = emp_query.all()
        employee_ids = [e.id for e in employees]
        
        # Get skills for these employees
        skill_counts = defaultdict(int)
        proficiency_dist = defaultdict(lambda: defaultdict(int))
        
        if employee_ids:
            skills_query = self.db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id.in_(employee_ids)
            )
            
            for es in skills_query.all():
                skill_name = es.skill.name if es.skill else f"Skill_{es.skill_id}"
                skill_counts[skill_name] += 1
                
                if es.rating:
                    proficiency_dist[skill_name][es.rating.value] += 1
        
        return SkillDistribution(
            capability=capability,
            total_employees=len(employees),
            skill_counts=dict(skill_counts),
            proficiency_distribution={k: dict(v) for k, v in proficiency_dist.items()}
        )

    
    def get_capability_coverage(self, capability: str) -> CoverageMetrics:
        """
        Get coverage metrics for a capability.
        
        Args:
            capability: The capability to analyze
            
        Returns:
            Coverage metrics including percentage and gaps
        """
        # Get employees in this capability
        employees = self.db.query(Employee).filter(
            (Employee.home_capability == capability) |
            (Employee.capability == capability)
        ).all()
        
        if not employees:
            return CoverageMetrics(
                capability=capability,
                coverage_percentage=0.0,
                skills_with_coverage=0,
                skills_without_coverage=0,
                critical_gaps=[]
            )
        
        employee_ids = [e.id for e in employees]
        
        # Get required skills for this capability (from team templates)
        required_skills = set()
        for emp in employees:
            if emp.team:
                templates = self.db.query(TeamSkillTemplate).filter(
                    TeamSkillTemplate.team == emp.team,
                    TeamSkillTemplate.is_required == True
                ).all()
                for t in templates:
                    required_skills.add(t.skill_id)
        
        if not required_skills:
            return CoverageMetrics(
                capability=capability,
                coverage_percentage=100.0,
                skills_with_coverage=0,
                skills_without_coverage=0,
                critical_gaps=[]
            )
        
        # Check coverage for each required skill
        skills_with_coverage = 0
        critical_gaps = []
        
        for skill_id in required_skills:
            # Count employees with this skill at Intermediate or above
            covered = self.db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id.in_(employee_ids),
                EmployeeSkill.skill_id == skill_id,
                EmployeeSkill.rating.in_(['Intermediate', 'Advanced', 'Expert'])
            ).count()
            
            if covered > 0:
                skills_with_coverage += 1
            else:
                skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
                if skill:
                    critical_gaps.append(skill.name)
        
        total_required = len(required_skills)
        coverage_pct = (skills_with_coverage / total_required * 100) if total_required > 0 else 100.0
        
        return CoverageMetrics(
            capability=capability,
            coverage_percentage=round(coverage_pct, 2),
            skills_with_coverage=skills_with_coverage,
            skills_without_coverage=total_required - skills_with_coverage,
            critical_gaps=critical_gaps
        )
    
    def get_training_needs(self, capability: str) -> List[TrainingNeed]:
        """
        Identify training needs for a capability.
        
        Args:
            capability: The capability to analyze
            
        Returns:
            List of training needs prioritized by gap
        """
        # Get employees in this capability
        employees = self.db.query(Employee).filter(
            (Employee.home_capability == capability) |
            (Employee.capability == capability)
        ).all()
        
        if not employees:
            return []
        
        employee_ids = [e.id for e in employees]
        total_employees = len(employees)
        
        # Get required skills
        required_skills = {}
        for emp in employees:
            if emp.team:
                templates = self.db.query(TeamSkillTemplate).filter(
                    TeamSkillTemplate.team == emp.team,
                    TeamSkillTemplate.is_required == True
                ).all()
                for t in templates:
                    skill = self.db.query(Skill).filter(Skill.id == t.skill_id).first()
                    if skill:
                        required_skills[t.skill_id] = skill.name
        
        training_needs = []
        required_coverage = 80.0  # Target 80% coverage
        
        for skill_id, skill_name in required_skills.items():
            # Count employees with adequate proficiency
            covered = self.db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id.in_(employee_ids),
                EmployeeSkill.skill_id == skill_id,
                EmployeeSkill.rating.in_(['Intermediate', 'Advanced', 'Expert'])
            ).count()
            
            current_coverage = (covered / total_employees * 100) if total_employees > 0 else 0.0
            gap = required_coverage - current_coverage
            
            if gap > 0:
                priority = "High" if gap >= 40 else "Medium" if gap >= 20 else "Low"
                training_needs.append(TrainingNeed(
                    skill_name=skill_name,
                    current_coverage=round(current_coverage, 2),
                    required_coverage=required_coverage,
                    gap_percentage=round(gap, 2),
                    priority=priority
                ))
        
        # Sort by gap (highest first)
        training_needs.sort(key=lambda x: x.gap_percentage, reverse=True)
        
        return training_needs


# Factory function
def get_metrics_service(db: Session) -> MetricsService:
    """Create a MetricsService instance."""
    return MetricsService(db)

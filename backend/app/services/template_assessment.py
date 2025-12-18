"""Template Assessment Service for Manager-Driven Skill Assessment.

Handles template-based skill assessments including:
- Retrieving template skills with employee's current levels
- Submitting assessments for all skills in a template
- Tracking assessment progress
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
import json

from app.db.models import (
    Employee, Skill, SkillTemplate, SkillAssessment, TemplateAssessmentLog,
    RatingEnum, AssessmentTypeEnum, AssessorRoleEnum, AssessmentHistory
)
from app.services.authority_validator import AuthorityValidator
from app.core.permissions import RoleID


class TemplateSkillView(BaseModel):
    """A skill from a template with employee's current level."""
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    required_level: Optional[str]
    current_level: Optional[str]
    is_assessed: bool
    
    class Config:
        from_attributes = True


class TemplateAssessmentView(BaseModel):
    """Template with all skills and employee's current levels."""
    template_id: int
    template_name: str
    employee_id: int
    employee_name: str
    skills: List[TemplateSkillView]
    total_skills: int
    assessed_skills: int
    
    class Config:
        from_attributes = True


class SkillAssessmentInput(BaseModel):
    """Input for a single skill assessment."""
    skill_id: int
    level: str
    comments: Optional[str] = None


class TemplateAssessmentResult(BaseModel):
    """Result of submitting template assessments."""
    template_id: int
    employee_id: int
    assessor_id: int
    skills_assessed: int
    total_skills: int
    log_id: int
    assessed_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentProgress(BaseModel):
    """Progress of template assessment."""
    template_id: int
    employee_id: int
    total_skills: int
    assessed_skills: int
    completion_percentage: float
    
    class Config:
        from_attributes = True



class TemplateAssessmentService:
    """Service for managing template-based skill assessments."""
    
    def __init__(self, db: Session):
        self.db = db
        self.authority_validator = AuthorityValidator(db)
    
    def _parse_template_skills(self, template: SkillTemplate) -> List[dict]:
        """
        Parse template content JSON to extract skills.
        
        Template content is stored as JSON array of rows/columns from spreadsheet.
        Expected format: [{"skill_name": "...", "required_level": "...", ...}, ...]
        
        Returns:
            List of dicts with skill_name and required_level
        """
        try:
            content = json.loads(template.content)
            if not isinstance(content, list):
                return []
            
            skills = []
            for row in content:
                if isinstance(row, dict):
                    # Look for skill name in various possible column names
                    skill_name = (
                        row.get('skill_name') or 
                        row.get('Skill Name') or 
                        row.get('skill') or 
                        row.get('Skill') or
                        row.get('name') or
                        row.get('Name')
                    )
                    # Look for required level in various possible column names
                    required_level = (
                        row.get('required_level') or 
                        row.get('Required Level') or 
                        row.get('level') or 
                        row.get('Level') or
                        row.get('required') or
                        row.get('Required')
                    )
                    
                    if skill_name:
                        skills.append({
                            'skill_name': str(skill_name).strip(),
                            'required_level': str(required_level).strip() if required_level else None
                        })
            
            return skills
        except (json.JSONDecodeError, TypeError):
            return []
    
    def get_template_for_assessment(
        self,
        template_id: int,
        employee_id: int
    ) -> TemplateAssessmentView:
        """
        Get template skills with employee's current levels.
        
        Args:
            template_id: The skill template ID
            employee_id: The employee ID to assess
            
        Returns:
            TemplateAssessmentView with all skills and current levels
            
        Raises:
            ValueError: If template or employee not found
        """
        # Get template
        template = self.db.query(SkillTemplate).filter(
            SkillTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Get employee
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Parse template skills
        template_skills = self._parse_template_skills(template)
        
        # Get all skill names from template
        skill_names = [s['skill_name'] for s in template_skills]
        
        # Query skills from database
        skills_db = self.db.query(Skill).filter(
            Skill.name.in_(skill_names)
        ).all() if skill_names else []
        
        skill_map = {s.name.lower(): s for s in skills_db}
        
        # Get employee's current assessments
        assessments = self.db.query(SkillAssessment).filter(
            SkillAssessment.employee_id == employee_id
        ).all()
        
        assessment_map = {a.skill_id: a for a in assessments}
        
        # Build skill views
        skill_views = []
        assessed_count = 0
        
        for ts in template_skills:
            skill_name = ts['skill_name']
            skill = skill_map.get(skill_name.lower())
            
            if skill:
                assessment = assessment_map.get(skill.id)
                is_assessed = assessment is not None
                current_level = assessment.level.value if assessment and assessment.level else None
                
                if is_assessed:
                    assessed_count += 1
                
                skill_views.append(TemplateSkillView(
                    skill_id=skill.id,
                    skill_name=skill.name,
                    skill_category=skill.category,
                    required_level=ts['required_level'],
                    current_level=current_level,
                    is_assessed=is_assessed
                ))
            else:
                # Skill not found in database - include with null skill_id
                skill_views.append(TemplateSkillView(
                    skill_id=0,  # Indicates skill not found
                    skill_name=skill_name,
                    skill_category=None,
                    required_level=ts['required_level'],
                    current_level=None,
                    is_assessed=False
                ))
        
        return TemplateAssessmentView(
            template_id=template.id,
            template_name=template.template_name,
            employee_id=employee.id,
            employee_name=employee.name,
            skills=skill_views,
            total_skills=len(skill_views),
            assessed_skills=assessed_count
        )
    
    def submit_template_assessment(
        self,
        template_id: int,
        employee_id: int,
        assessor_id: int,
        assessor_role_id: int,
        assessments: List[SkillAssessmentInput]
    ) -> TemplateAssessmentResult:
        """
        Submit assessments for all skills in template.
        
        Args:
            template_id: The skill template ID
            employee_id: Target employee's ID
            assessor_id: Assessor's employee ID
            assessor_role_id: Assessor's role ID
            assessments: List of skill assessments to submit
            
        Returns:
            TemplateAssessmentResult with assessment statistics
            
        Raises:
            PermissionError: If assessor lacks authority
            ValueError: If template, employee, or skill not found
        """
        # Validate authority
        is_authorized, reason = self.authority_validator.can_assess(
            assessor_id, assessor_role_id, employee_id
        )
        if not is_authorized:
            raise PermissionError(f"Assessment not authorized: {reason}")
        
        # Verify template exists
        template = self.db.query(SkillTemplate).filter(
            SkillTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Verify employee exists
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Determine assessor role enum
        if assessor_role_id == RoleID.LINE_MANAGER:
            assessor_role = AssessorRoleEnum.LINE_MANAGER
        elif assessor_role_id == RoleID.DELIVERY_MANAGER:
            assessor_role = AssessorRoleEnum.DELIVERY_MANAGER
        else:
            raise PermissionError("Only Line Managers and Delivery Managers can assess skills")
        
        now = datetime.utcnow()
        skills_assessed = 0
        
        # Get template skills for total count
        template_skills = self._parse_template_skills(template)
        total_skills = len(template_skills)
        
        # Process each assessment
        for assessment_input in assessments:
            # Verify skill exists
            skill = self.db.query(Skill).filter(
                Skill.id == assessment_input.skill_id
            ).first()
            
            if not skill:
                continue  # Skip invalid skills
            
            # Convert level string to enum
            try:
                level = RatingEnum(assessment_input.level)
            except ValueError:
                continue  # Skip invalid levels
            
            # Check for existing assessment
            existing = self.db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee_id,
                SkillAssessment.skill_id == assessment_input.skill_id
            ).first()
            
            if existing:
                # Update existing assessment
                previous_level = existing.level
                
                # Create history record
                history = AssessmentHistory(
                    employee_id=employee_id,
                    skill_id=assessment_input.skill_id,
                    previous_level=previous_level,
                    new_level=level,
                    assessment_type=AssessmentTypeEnum.MANAGER,
                    assessor_id=assessor_id,
                    assessor_role=assessor_role,
                    comments=assessment_input.comments,
                    assessed_at=now
                )
                self.db.add(history)
                
                # Update the assessment
                existing.level = level
                existing.assessment_type = AssessmentTypeEnum.MANAGER
                existing.assessor_id = assessor_id
                existing.assessor_role = assessor_role
                existing.comments = assessment_input.comments
                existing.assessed_at = now
                existing.updated_at = now
            else:
                # Create new assessment
                new_assessment = SkillAssessment(
                    employee_id=employee_id,
                    skill_id=assessment_input.skill_id,
                    level=level,
                    assessment_type=AssessmentTypeEnum.MANAGER,
                    assessor_id=assessor_id,
                    assessor_role=assessor_role,
                    comments=assessment_input.comments,
                    assessed_at=now,
                    created_at=now,
                    updated_at=now
                )
                self.db.add(new_assessment)
                
                # Create history record
                history = AssessmentHistory(
                    employee_id=employee_id,
                    skill_id=assessment_input.skill_id,
                    previous_level=None,
                    new_level=level,
                    assessment_type=AssessmentTypeEnum.MANAGER,
                    assessor_id=assessor_id,
                    assessor_role=assessor_role,
                    comments=assessment_input.comments,
                    assessed_at=now
                )
                self.db.add(history)
            
            skills_assessed += 1
        
        # Create template assessment log
        log = TemplateAssessmentLog(
            template_id=template_id,
            employee_id=employee_id,
            assessor_id=assessor_id,
            skills_assessed=skills_assessed,
            total_skills=total_skills,
            assessed_at=now
        )
        self.db.add(log)
        
        self.db.commit()
        self.db.refresh(log)
        
        return TemplateAssessmentResult(
            template_id=template_id,
            employee_id=employee_id,
            assessor_id=assessor_id,
            skills_assessed=skills_assessed,
            total_skills=total_skills,
            log_id=log.id,
            assessed_at=now
        )
    
    def get_assessment_progress(
        self,
        template_id: int,
        employee_id: int
    ) -> AssessmentProgress:
        """
        Get completion percentage for template assessment.
        
        Args:
            template_id: The skill template ID
            employee_id: The employee ID
            
        Returns:
            AssessmentProgress with completion statistics
            
        Raises:
            ValueError: If template or employee not found
        """
        # Get template
        template = self.db.query(SkillTemplate).filter(
            SkillTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Verify employee exists
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Parse template skills
        template_skills = self._parse_template_skills(template)
        skill_names = [s['skill_name'] for s in template_skills]
        
        # Get skill IDs from database
        skills_db = self.db.query(Skill).filter(
            Skill.name.in_(skill_names)
        ).all() if skill_names else []
        
        skill_ids = [s.id for s in skills_db]
        total_skills = len(template_skills)
        
        # Count assessed skills
        if skill_ids:
            assessed_count = self.db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee_id,
                SkillAssessment.skill_id.in_(skill_ids)
            ).count()
        else:
            assessed_count = 0
        
        # Calculate percentage
        completion_percentage = (assessed_count / total_skills * 100) if total_skills > 0 else 0.0
        
        return AssessmentProgress(
            template_id=template_id,
            employee_id=employee_id,
            total_skills=total_skills,
            assessed_skills=assessed_count,
            completion_percentage=completion_percentage
        )


def get_template_assessment_service(db: Session) -> TemplateAssessmentService:
    """Factory function to create TemplateAssessmentService instance."""
    return TemplateAssessmentService(db)

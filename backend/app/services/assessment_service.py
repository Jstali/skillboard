"""Assessment Service for Manager-Driven Skill Assessment.

Handles all skill assessment operations including:
- Creating/updating assessments (manager only)
- Retrieving employee assessments
- Retrieving assessment history
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from app.db.models import (
    Employee, Skill, SkillAssessment, AssessmentHistory,
    RatingEnum, AssessmentTypeEnum, AssessorRoleEnum
)
from app.services.authority_validator import AuthorityValidator


class AssessmentWithDetails(BaseModel):
    """Assessment with skill and assessor details."""
    id: int
    employee_id: int
    skill_id: int
    skill_name: str
    skill_category: Optional[str]
    level: str
    assessment_type: str
    assessor_id: Optional[int]
    assessor_name: Optional[str]
    assessor_role: str
    comments: Optional[str]
    assessed_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentHistoryItem(BaseModel):
    """Assessment history record."""
    id: int
    employee_id: int
    skill_id: int
    skill_name: str
    previous_level: Optional[str]
    new_level: str
    assessment_type: str
    assessor_id: Optional[int]
    assessor_name: Optional[str]
    assessor_role: str
    comments: Optional[str]
    assessed_at: datetime
    
    class Config:
        from_attributes = True


class AssessmentService:
    """Service for managing skill assessments."""
    
    def __init__(self, db: Session):
        self.db = db
        self.authority_validator = AuthorityValidator(db)
    
    def create_assessment(
        self,
        employee_id: int,
        skill_id: int,
        level: RatingEnum,
        assessor_id: int,
        assessor_role_id: int,
        comments: Optional[str] = None
    ) -> Tuple[SkillAssessment, bool]:
        """
        Create or update a skill assessment.
        
        Args:
            employee_id: Target employee's ID
            skill_id: Skill ID to assess
            level: New proficiency level
            assessor_id: Assessor's employee ID
            assessor_role_id: Assessor's role ID
            comments: Optional assessment comments
            
        Returns:
            Tuple of (SkillAssessment, is_new) where is_new indicates if created vs updated
            
        Raises:
            PermissionError: If assessor lacks authority
            ValueError: If employee or skill not found
        """
        # Validate authority
        is_authorized, reason = self.authority_validator.can_assess(
            assessor_id, assessor_role_id, employee_id
        )
        if not is_authorized:
            raise PermissionError(f"Assessment not authorized: {reason}")
        
        # Verify employee exists
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Verify skill exists
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise ValueError(f"Skill with ID {skill_id} not found")
        
        # Determine assessor role enum
        from app.core.permissions import RoleID
        if assessor_role_id == RoleID.LINE_MANAGER:
            assessor_role = AssessorRoleEnum.LINE_MANAGER
        elif assessor_role_id == RoleID.DELIVERY_MANAGER:
            assessor_role = AssessorRoleEnum.DELIVERY_MANAGER
        else:
            raise PermissionError("Only Line Managers and Delivery Managers can assess skills")
        
        now = datetime.utcnow()
        
        # Check for existing assessment
        existing = self.db.query(SkillAssessment).filter(
            SkillAssessment.employee_id == employee_id,
            SkillAssessment.skill_id == skill_id
        ).first()
        
        if existing:
            # Update existing assessment
            previous_level = existing.level
            
            # Create history record BEFORE updating
            history = AssessmentHistory(
                employee_id=employee_id,
                skill_id=skill_id,
                previous_level=previous_level,
                new_level=level,
                assessment_type=AssessmentTypeEnum.MANAGER,
                assessor_id=assessor_id,
                assessor_role=assessor_role,
                comments=comments,
                assessed_at=now
            )
            self.db.add(history)
            
            # Update the assessment
            existing.level = level
            existing.assessment_type = AssessmentTypeEnum.MANAGER
            existing.assessor_id = assessor_id
            existing.assessor_role = assessor_role
            existing.comments = comments
            existing.assessed_at = now
            existing.updated_at = now
            
            self.db.commit()
            self.db.refresh(existing)
            return existing, False
        else:
            # Create new assessment
            assessment = SkillAssessment(
                employee_id=employee_id,
                skill_id=skill_id,
                level=level,
                assessment_type=AssessmentTypeEnum.MANAGER,
                assessor_id=assessor_id,
                assessor_role=assessor_role,
                comments=comments,
                assessed_at=now,
                created_at=now,
                updated_at=now
            )
            self.db.add(assessment)
            
            # Create history record
            history = AssessmentHistory(
                employee_id=employee_id,
                skill_id=skill_id,
                previous_level=None,
                new_level=level,
                assessment_type=AssessmentTypeEnum.MANAGER,
                assessor_id=assessor_id,
                assessor_role=assessor_role,
                comments=comments,
                assessed_at=now
            )
            self.db.add(history)
            
            self.db.commit()
            self.db.refresh(assessment)
            return assessment, True
    
    def get_employee_assessments(
        self,
        employee_id: int
    ) -> List[AssessmentWithDetails]:
        """
        Get all assessments for an employee with skill and assessor details.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            List of AssessmentWithDetails
        """
        assessments = self.db.query(SkillAssessment).filter(
            SkillAssessment.employee_id == employee_id
        ).options(
            joinedload(SkillAssessment.skill),
            joinedload(SkillAssessment.assessor)
        ).order_by(SkillAssessment.assessed_at.desc()).all()
        
        result = []
        for a in assessments:
            result.append(AssessmentWithDetails(
                id=a.id,
                employee_id=a.employee_id,
                skill_id=a.skill_id,
                skill_name=a.skill.name if a.skill else "Unknown",
                skill_category=a.skill.category if a.skill else None,
                level=a.level.value if a.level else None,
                assessment_type=a.assessment_type.value if a.assessment_type else None,
                assessor_id=a.assessor_id,
                assessor_name=a.assessor.name if a.assessor else "System",
                assessor_role=a.assessor_role.value if a.assessor_role else None,
                comments=a.comments,
                assessed_at=a.assessed_at
            ))
        
        return result
    
    def get_assessment_history(
        self,
        employee_id: int,
        skill_id: Optional[int] = None
    ) -> List[AssessmentHistoryItem]:
        """
        Get assessment history for an employee.
        
        Args:
            employee_id: The employee's ID
            skill_id: Optional skill ID to filter by
            
        Returns:
            List of AssessmentHistoryItem ordered by assessed_at DESC
        """
        query = self.db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee_id
        )
        
        if skill_id:
            query = query.filter(AssessmentHistory.skill_id == skill_id)
        
        history = query.options(
            joinedload(AssessmentHistory.skill),
            joinedload(AssessmentHistory.assessor)
        ).order_by(AssessmentHistory.assessed_at.desc()).all()
        
        result = []
        for h in history:
            result.append(AssessmentHistoryItem(
                id=h.id,
                employee_id=h.employee_id,
                skill_id=h.skill_id,
                skill_name=h.skill.name if h.skill else "Unknown",
                previous_level=h.previous_level.value if h.previous_level else None,
                new_level=h.new_level.value if h.new_level else None,
                assessment_type=h.assessment_type.value if h.assessment_type else None,
                assessor_id=h.assessor_id,
                assessor_name=h.assessor.name if h.assessor else "System",
                assessor_role=h.assessor_role.value if h.assessor_role else None,
                comments=h.comments,
                assessed_at=h.assessed_at
            ))
        
        return result


def get_assessment_service(db: Session) -> AssessmentService:
    """Factory function to create AssessmentService instance."""
    return AssessmentService(db)

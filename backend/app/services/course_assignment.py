"""Course Assignment Service for Manager-Driven Skill Assessment.

Handles course assignments by managers including:
- Retrieving courses for skills
- Assigning courses to employees
- Tracking assignment status and progress
- Managing course completion workflow
"""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from pydantic import BaseModel

from app.db.models import (
    Employee, Skill, Course, CourseAssignment, CourseStatusEnum
)
from app.services.authority_validator import AuthorityValidator
from app.core.permissions import RoleID


class CourseWithDetails(BaseModel):
    """Course with full details."""
    id: int
    title: str
    description: Optional[str]
    skill_id: Optional[int]
    skill_name: Optional[str]
    external_url: Optional[str]
    is_mandatory: bool
    
    class Config:
        from_attributes = True


class CourseAssignmentWithDetails(BaseModel):
    """Course assignment with employee and course details."""
    id: int
    course_id: int
    course_title: str
    course_description: Optional[str]
    course_url: Optional[str]
    employee_id: int
    employee_name: str
    assigned_by: Optional[int]
    assigner_name: Optional[str]
    assigned_at: datetime
    due_date: Optional[datetime]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    certificate_url: Optional[str]
    notes: Optional[str]
    skill_id: Optional[int]
    skill_name: Optional[str]
    
    class Config:
        from_attributes = True



class CourseAssignmentService:
    """Service for managing course assignments by managers."""
    
    def __init__(self, db: Session):
        self.db = db
        self.authority_validator = AuthorityValidator(db)
    
    def get_courses_for_skill(self, skill_id: int) -> List[CourseWithDetails]:
        """
        Get available courses for a skill.
        
        Args:
            skill_id: The skill ID to get courses for
            
        Returns:
            List of CourseWithDetails with full course information
            
        **Validates: Requirements 2.1, 2.2**
        """
        courses = self.db.query(Course).options(
            joinedload(Course.skill)
        ).filter(
            Course.skill_id == skill_id
        ).all()
        
        result = []
        for course in courses:
            result.append(CourseWithDetails(
                id=course.id,
                title=course.title,
                description=course.description,
                skill_id=course.skill_id,
                skill_name=course.skill.name if course.skill else None,
                external_url=course.external_url,
                is_mandatory=course.is_mandatory
            ))
        
        return result
    
    def get_all_courses(
        self,
        skill_id: Optional[int] = None,
        is_mandatory: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[CourseWithDetails]:
        """
        Get all courses with optional filtering.
        
        Args:
            skill_id: Filter by skill ID
            is_mandatory: Filter by mandatory status
            search: Search term for title/description
            
        Returns:
            List of CourseWithDetails matching filters
            
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        query = self.db.query(Course).options(joinedload(Course.skill))
        
        if skill_id is not None:
            query = query.filter(Course.skill_id == skill_id)
        
        if is_mandatory is not None:
            query = query.filter(Course.is_mandatory == is_mandatory)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Course.title.ilike(search_term)) |
                (Course.description.ilike(search_term))
            )
        
        courses = query.all()
        
        result = []
        for course in courses:
            result.append(CourseWithDetails(
                id=course.id,
                title=course.title,
                description=course.description,
                skill_id=course.skill_id,
                skill_name=course.skill.name if course.skill else None,
                external_url=course.external_url,
                is_mandatory=course.is_mandatory
            ))
        
        return result
    
    def assign_course(
        self,
        course_id: int,
        employee_id: int,
        assigned_by: int,
        assigned_by_role_id: int,
        due_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        skill_id: Optional[int] = None
    ) -> CourseAssignment:
        """
        Assign a course to an employee.
        
        Args:
            course_id: The course to assign
            employee_id: Target employee's ID
            assigned_by: Assigner's employee ID
            assigned_by_role_id: Assigner's role ID
            due_date: Optional due date
            notes: Optional notes explaining assignment
            skill_id: Optional skill ID for gap linkage
            
        Returns:
            Created CourseAssignment record
            
        Raises:
            PermissionError: If assigner lacks authority
            ValueError: If course/employee not found or already assigned
            
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
        """
        # Validate authority
        is_authorized, reason = self.authority_validator.can_assess(
            assigned_by, assigned_by_role_id, employee_id
        )
        if not is_authorized:
            raise PermissionError(f"Assignment not authorized: {reason}")
        
        # Verify course exists
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course with ID {course_id} not found")
        
        # Verify employee exists
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Check for existing assignment (prevent duplicates)
        existing = self.db.query(CourseAssignment).filter(
            CourseAssignment.course_id == course_id,
            CourseAssignment.employee_id == employee_id
        ).first()
        
        if existing:
            raise ValueError("Course is already assigned to this employee")
        
        # Create assignment
        now = datetime.utcnow()
        assignment = CourseAssignment(
            course_id=course_id,
            employee_id=employee_id,
            assigned_by=assigned_by,
            assigned_at=now,
            due_date=due_date,
            status=CourseStatusEnum.NOT_STARTED,
            notes=notes,
            skill_id=skill_id
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment

    
    def get_manager_assignments(
        self,
        manager_id: int,
        status_filter: Optional[str] = None,
        employee_id: Optional[int] = None,
        course_id: Optional[int] = None
    ) -> List[CourseAssignmentWithDetails]:
        """
        Get all course assignments made by a manager.
        
        Args:
            manager_id: The manager's employee ID
            status_filter: Filter by status (NOT_STARTED, IN_PROGRESS, COMPLETED)
            employee_id: Filter by employee
            course_id: Filter by course
            
        Returns:
            List of CourseAssignmentWithDetails
            
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        query = self.db.query(CourseAssignment).options(
            joinedload(CourseAssignment.course),
            joinedload(CourseAssignment.employee),
            joinedload(CourseAssignment.skill)
        ).filter(
            CourseAssignment.assigned_by == manager_id
        )
        
        if status_filter:
            try:
                status_enum = CourseStatusEnum(status_filter)
                query = query.filter(CourseAssignment.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        if employee_id is not None:
            query = query.filter(CourseAssignment.employee_id == employee_id)
        
        if course_id is not None:
            query = query.filter(CourseAssignment.course_id == course_id)
        
        assignments = query.all()
        
        # Get assigner details
        assigner = self.db.query(Employee).filter(Employee.id == manager_id).first()
        assigner_name = assigner.name if assigner else None
        
        result = []
        for assignment in assignments:
            result.append(CourseAssignmentWithDetails(
                id=assignment.id,
                course_id=assignment.course_id,
                course_title=assignment.course.title if assignment.course else "",
                course_description=assignment.course.description if assignment.course else None,
                course_url=assignment.course.external_url if assignment.course else None,
                employee_id=assignment.employee_id,
                employee_name=assignment.employee.name if assignment.employee else "",
                assigned_by=assignment.assigned_by,
                assigner_name=assigner_name,
                assigned_at=assignment.assigned_at,
                due_date=assignment.due_date,
                status=assignment.status.value if assignment.status else CourseStatusEnum.NOT_STARTED.value,
                started_at=assignment.started_at,
                completed_at=assignment.completed_at,
                certificate_url=assignment.certificate_url,
                notes=assignment.notes,
                skill_id=assignment.skill_id,
                skill_name=assignment.skill.name if assignment.skill else None
            ))
        
        return result
    
    def get_employee_assignments(
        self,
        employee_id: int
    ) -> List[CourseAssignmentWithDetails]:
        """
        Get all courses assigned to an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            List of CourseAssignmentWithDetails
            
        **Validates: Requirements 6.1, 6.2**
        """
        assignments = self.db.query(CourseAssignment).options(
            joinedload(CourseAssignment.course),
            joinedload(CourseAssignment.skill)
        ).filter(
            CourseAssignment.employee_id == employee_id
        ).all()
        
        # Get employee details
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        employee_name = employee.name if employee else ""
        
        result = []
        for assignment in assignments:
            # Get assigner name
            assigner_name = None
            if assignment.assigned_by:
                assigner = self.db.query(Employee).filter(
                    Employee.id == assignment.assigned_by
                ).first()
                assigner_name = assigner.name if assigner else None
            
            result.append(CourseAssignmentWithDetails(
                id=assignment.id,
                course_id=assignment.course_id,
                course_title=assignment.course.title if assignment.course else "",
                course_description=assignment.course.description if assignment.course else None,
                course_url=assignment.course.external_url if assignment.course else None,
                employee_id=assignment.employee_id,
                employee_name=employee_name,
                assigned_by=assignment.assigned_by,
                assigner_name=assigner_name,
                assigned_at=assignment.assigned_at,
                due_date=assignment.due_date,
                status=assignment.status.value if assignment.status else CourseStatusEnum.NOT_STARTED.value,
                started_at=assignment.started_at,
                completed_at=assignment.completed_at,
                certificate_url=assignment.certificate_url,
                notes=assignment.notes,
                skill_id=assignment.skill_id,
                skill_name=assignment.skill.name if assignment.skill else None
            ))
        
        return result

    
    # Valid status transitions
    VALID_TRANSITIONS = {
        CourseStatusEnum.NOT_STARTED: [CourseStatusEnum.IN_PROGRESS],
        CourseStatusEnum.IN_PROGRESS: [CourseStatusEnum.COMPLETED],
        CourseStatusEnum.COMPLETED: []  # No transitions from completed
    }
    
    def update_assignment_status(
        self,
        assignment_id: int,
        new_status: str,
        certificate_url: Optional[str] = None
    ) -> CourseAssignment:
        """
        Update course assignment status.
        
        Args:
            assignment_id: The assignment ID
            new_status: New status (NOT_STARTED, IN_PROGRESS, COMPLETED)
            certificate_url: Certificate URL (required for COMPLETED)
            
        Returns:
            Updated CourseAssignment
            
        Raises:
            ValueError: If assignment not found or invalid transition
            
        **Validates: Requirements 6.3, 6.4**
        """
        # Get assignment
        assignment = self.db.query(CourseAssignment).filter(
            CourseAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            raise ValueError(f"Assignment with ID {assignment_id} not found")
        
        # Parse new status
        try:
            new_status_enum = CourseStatusEnum(new_status)
        except ValueError:
            raise ValueError(f"Invalid status: {new_status}")
        
        # Validate transition
        current_status = assignment.status
        valid_next_statuses = self.VALID_TRANSITIONS.get(current_status, [])
        
        if new_status_enum not in valid_next_statuses:
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status}"
            )
        
        now = datetime.utcnow()
        
        # Update status and timestamps
        assignment.status = new_status_enum
        
        if new_status_enum == CourseStatusEnum.IN_PROGRESS:
            assignment.started_at = now
        elif new_status_enum == CourseStatusEnum.COMPLETED:
            assignment.completed_at = now
            if certificate_url:
                assignment.certificate_url = certificate_url
        
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment


def get_course_assignment_service(db: Session) -> CourseAssignmentService:
    """Factory function to create CourseAssignmentService instance."""
    return CourseAssignmentService(db)

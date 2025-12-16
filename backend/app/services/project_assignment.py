"""Project Assignment Management Service.

This service manages employee-project relationships, validates allocations,
and detects conflicts in assignments.
"""
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import Employee, Project, EmployeeProjectAssignment


class AllocationError(Exception):
    """Exception raised for allocation constraint violations."""
    pass


class ConflictError(Exception):
    """Exception raised for assignment conflicts."""
    pass


class AssignmentCreate(BaseModel):
    """Data for creating a new assignment."""
    employee_id: int
    project_id: int
    is_primary: bool = False
    percentage_allocation: Optional[int] = None
    line_manager_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AssignmentConflict(BaseModel):
    """Represents an assignment conflict."""
    employee_id: int
    conflict_type: str  # over_allocation, multiple_primary, date_overlap
    details: str
    affected_projects: List[int]


class AllocationValidator:
    """Validates allocation constraints for project assignments."""
    
    MAX_TOTAL_ALLOCATION = 100
    
    def validate_allocation(
        self,
        employee_id: int,
        new_allocation: int,
        existing_allocations: List[int],
        exclude_assignment_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validate that new allocation doesn't exceed 100%.
        
        Args:
            employee_id: Employee ID
            new_allocation: New allocation percentage
            existing_allocations: List of existing allocation percentages
            exclude_assignment_id: Assignment ID to exclude (for updates)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if new_allocation is None:
            return True, ""
        
        if new_allocation < 0 or new_allocation > 100:
            return False, f"Allocation must be between 0 and 100, got {new_allocation}"
        
        total = sum(a for a in existing_allocations if a is not None) + new_allocation
        
        if total > self.MAX_TOTAL_ALLOCATION:
            return False, f"Total allocation would be {total}%, exceeds maximum of {self.MAX_TOTAL_ALLOCATION}%"
        
        return True, ""
    
    def validate_primary_assignment(
        self,
        employee_id: int,
        is_primary: bool,
        existing_primary_count: int
    ) -> Tuple[bool, str]:
        """
        Validate primary assignment constraint (only one primary per employee).
        
        Args:
            employee_id: Employee ID
            is_primary: Whether new assignment is primary
            existing_primary_count: Count of existing primary assignments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if is_primary and existing_primary_count > 0:
            return False, "Employee already has a primary assignment"
        
        return True, ""


class ConflictDetector:
    """Detects conflicts in project assignments."""
    
    def detect_over_allocation(
        self,
        employee_id: int,
        allocations: List[Dict]
    ) -> Optional[AssignmentConflict]:
        """
        Detect if employee is over-allocated.
        
        Args:
            employee_id: Employee ID
            allocations: List of allocation dicts with project_id and percentage
            
        Returns:
            AssignmentConflict if over-allocated, None otherwise
        """
        total = sum(a.get('percentage', 0) or 0 for a in allocations)
        
        if total > 100:
            return AssignmentConflict(
                employee_id=employee_id,
                conflict_type="over_allocation",
                details=f"Total allocation is {total}%, exceeds 100%",
                affected_projects=[a['project_id'] for a in allocations]
            )
        
        return None
    
    def detect_multiple_primary(
        self,
        employee_id: int,
        assignments: List[Dict]
    ) -> Optional[AssignmentConflict]:
        """
        Detect if employee has multiple primary assignments.
        
        Args:
            employee_id: Employee ID
            assignments: List of assignment dicts with project_id and is_primary
            
        Returns:
            AssignmentConflict if multiple primaries, None otherwise
        """
        primary_projects = [a['project_id'] for a in assignments if a.get('is_primary')]
        
        if len(primary_projects) > 1:
            return AssignmentConflict(
                employee_id=employee_id,
                conflict_type="multiple_primary",
                details=f"Employee has {len(primary_projects)} primary assignments",
                affected_projects=primary_projects
            )
        
        return None
    
    def detect_date_overlap(
        self,
        employee_id: int,
        assignments: List[Dict]
    ) -> List[AssignmentConflict]:
        """
        Detect overlapping date ranges for same project.
        
        Args:
            employee_id: Employee ID
            assignments: List of assignment dicts with dates
            
        Returns:
            List of AssignmentConflicts for overlaps
        """
        conflicts = []
        # Group by project
        by_project = {}
        for a in assignments:
            pid = a['project_id']
            if pid not in by_project:
                by_project[pid] = []
            by_project[pid].append(a)
        
        for project_id, project_assignments in by_project.items():
            if len(project_assignments) > 1:
                # Check for overlaps
                for i, a1 in enumerate(project_assignments):
                    for a2 in project_assignments[i+1:]:
                        if self._dates_overlap(a1, a2):
                            conflicts.append(AssignmentConflict(
                                employee_id=employee_id,
                                conflict_type="date_overlap",
                                details=f"Overlapping assignments for project {project_id}",
                                affected_projects=[project_id]
                            ))
        
        return conflicts
    
    def _dates_overlap(self, a1: Dict, a2: Dict) -> bool:
        """Check if two assignments have overlapping dates."""
        start1 = a1.get('start_date')
        end1 = a1.get('end_date')
        start2 = a2.get('start_date')
        end2 = a2.get('end_date')
        
        # If no dates, assume they overlap
        if not start1 and not start2:
            return True
        
        # If one has no end date, it's ongoing
        if start1 and start2:
            if end1 is None:
                end1 = datetime.max
            if end2 is None:
                end2 = datetime.max
            
            return start1 <= end2 and start2 <= end1
        
        return False


class ProjectAssignmentService:
    """
    Service for managing project assignments.
    
    Handles creation, validation, and conflict detection for
    employee-project relationships.
    """
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.validator = AllocationValidator()
        self.conflict_detector = ConflictDetector()
    
    def create_assignment(
        self,
        data: AssignmentCreate
    ) -> EmployeeProjectAssignment:
        """
        Create a new project assignment.
        
        Args:
            data: Assignment creation data
            
        Returns:
            Created assignment
            
        Raises:
            AllocationError: If allocation constraints violated
        """
        # Get existing allocations
        existing = self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == data.employee_id
        ).all()
        
        existing_allocations = [a.percentage_allocation for a in existing]
        existing_primary_count = sum(1 for a in existing if a.is_primary)
        
        # Validate allocation
        if data.percentage_allocation:
            valid, error = self.validator.validate_allocation(
                data.employee_id,
                data.percentage_allocation,
                existing_allocations
            )
            if not valid:
                raise AllocationError(error)
        
        # Validate primary
        valid, error = self.validator.validate_primary_assignment(
            data.employee_id,
            data.is_primary,
            existing_primary_count
        )
        if not valid:
            raise AllocationError(error)
        
        # Create assignment
        assignment = EmployeeProjectAssignment(
            employee_id=data.employee_id,
            project_id=data.project_id,
            is_primary=data.is_primary,
            percentage_allocation=data.percentage_allocation,
            line_manager_id=data.line_manager_id,
            start_date=data.start_date,
            end_date=data.end_date
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def get_employee_assignments(
        self,
        employee_id: int
    ) -> List[EmployeeProjectAssignment]:
        """Get all assignments for an employee."""
        return self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == employee_id
        ).all()
    
    def detect_conflicts(
        self,
        employee_id: int
    ) -> List[AssignmentConflict]:
        """
        Detect all conflicts for an employee's assignments.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of detected conflicts
        """
        assignments = self.get_employee_assignments(employee_id)
        
        assignment_dicts = [
            {
                'project_id': a.project_id,
                'percentage': a.percentage_allocation,
                'is_primary': a.is_primary,
                'start_date': a.start_date,
                'end_date': a.end_date
            }
            for a in assignments
        ]
        
        conflicts = []
        
        # Check over-allocation
        over_alloc = self.conflict_detector.detect_over_allocation(
            employee_id, assignment_dicts
        )
        if over_alloc:
            conflicts.append(over_alloc)
        
        # Check multiple primary
        multi_primary = self.conflict_detector.detect_multiple_primary(
            employee_id, assignment_dicts
        )
        if multi_primary:
            conflicts.append(multi_primary)
        
        # Check date overlaps
        overlaps = self.conflict_detector.detect_date_overlap(
            employee_id, assignment_dicts
        )
        conflicts.extend(overlaps)
        
        return conflicts


# Factory function
def get_project_assignment_service(db: Session) -> ProjectAssignmentService:
    """Create a ProjectAssignmentService instance."""
    return ProjectAssignmentService(db)

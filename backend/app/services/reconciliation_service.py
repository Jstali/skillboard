"""Reconciliation Service for comparing skill board vs HRMS assignments.

This service compares employee assignments between the skill board and HRMS
systems, identifying discrepancies without exposing financial data.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import Employee, EmployeeProjectAssignment, HRMSProjectAssignment, Project, HRMSProject
from app.services.financial_filter import financial_filter


class AssignmentInfo(BaseModel):
    """Assignment information (no financial data)."""
    project_name: str
    allocation_percentage: Optional[float]
    is_primary: bool
    start_date: Optional[str]
    end_date: Optional[str]


class Discrepancy(BaseModel):
    """Assignment discrepancy."""
    employee_id: str
    employee_name: str
    discrepancy_type: str  # Missing, Extra, Allocation_Mismatch
    skill_board_value: Optional[str]
    hrms_value: Optional[str]
    field: str


class ReconciliationResult(BaseModel):
    """Reconciliation comparison result."""
    employee_id: str
    employee_name: str
    skill_board_assignments: List[AssignmentInfo]
    hrms_assignments: List[AssignmentInfo]
    discrepancies: List[Discrepancy]
    match_status: str  # Match, Partial, Mismatch


class ReconciliationReport(BaseModel):
    """Reconciliation report summary."""
    generated_at: str
    total_employees: int
    employees_matched: int
    employees_with_discrepancies: int
    total_discrepancies: int
    discrepancy_breakdown: Dict[str, int]
    results: List[ReconciliationResult]


class ReconciliationService:
    """
    Service for reconciling skill board and HRMS assignments.
    
    Compares assignments between systems and identifies discrepancies
    without exposing financial data.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def compare_assignments(
        self,
        skill_board_assignments: List[AssignmentInfo],
        hrms_assignments: List[AssignmentInfo],
        employee_id: str,
        employee_name: str
    ) -> ReconciliationResult:
        """
        Compare assignments between skill board and HRMS.
        
        Args:
            skill_board_assignments: Assignments from skill board
            hrms_assignments: Assignments from HRMS
            employee_id: Employee ID
            employee_name: Employee name
            
        Returns:
            ReconciliationResult with discrepancies
        """
        discrepancies = []
        
        # Create lookup by project name
        sb_by_project = {a.project_name: a for a in skill_board_assignments}
        hrms_by_project = {a.project_name: a for a in hrms_assignments}
        
        # Find missing in HRMS (extra in skill board)
        for project_name, sb_assignment in sb_by_project.items():
            if project_name not in hrms_by_project:
                discrepancies.append(Discrepancy(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    discrepancy_type="Extra",
                    skill_board_value=project_name,
                    hrms_value=None,
                    field="project_assignment"
                ))
            else:
                # Check allocation mismatch
                hrms_assignment = hrms_by_project[project_name]
                if sb_assignment.allocation_percentage != hrms_assignment.allocation_percentage:
                    discrepancies.append(Discrepancy(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        discrepancy_type="Allocation_Mismatch",
                        skill_board_value=str(sb_assignment.allocation_percentage),
                        hrms_value=str(hrms_assignment.allocation_percentage),
                        field="allocation_percentage"
                    ))
        
        # Find missing in skill board
        for project_name in hrms_by_project:
            if project_name not in sb_by_project:
                discrepancies.append(Discrepancy(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    discrepancy_type="Missing",
                    skill_board_value=None,
                    hrms_value=project_name,
                    field="project_assignment"
                ))
        
        # Determine match status
        if not discrepancies:
            match_status = "Match"
        elif len(discrepancies) < len(skill_board_assignments) + len(hrms_assignments):
            match_status = "Partial"
        else:
            match_status = "Mismatch"
        
        return ReconciliationResult(
            employee_id=employee_id,
            employee_name=employee_name,
            skill_board_assignments=skill_board_assignments,
            hrms_assignments=hrms_assignments,
            discrepancies=discrepancies,
            match_status=match_status
        )
    
    def detect_discrepancies(
        self,
        skill_board_assignments: List[AssignmentInfo],
        hrms_assignments: List[AssignmentInfo]
    ) -> List[Dict[str, Any]]:
        """
        Detect discrepancies between two assignment lists.
        
        Args:
            skill_board_assignments: Assignments from skill board
            hrms_assignments: Assignments from HRMS
            
        Returns:
            List of discrepancy details
        """
        discrepancies = []
        
        sb_projects = {a.project_name for a in skill_board_assignments}
        hrms_projects = {a.project_name for a in hrms_assignments}
        
        # Missing in skill board
        for project in hrms_projects - sb_projects:
            discrepancies.append({
                "type": "Missing",
                "project": project,
                "source": "HRMS"
            })
        
        # Extra in skill board
        for project in sb_projects - hrms_projects:
            discrepancies.append({
                "type": "Extra",
                "project": project,
                "source": "SkillBoard"
            })
        
        return discrepancies

    
    def generate_reconciliation_report(
        self,
        results: List[ReconciliationResult]
    ) -> ReconciliationReport:
        """
        Generate a reconciliation report from results.
        
        Args:
            results: List of reconciliation results
            
        Returns:
            ReconciliationReport with summary and details
        """
        total_employees = len(results)
        employees_matched = sum(1 for r in results if r.match_status == "Match")
        employees_with_discrepancies = total_employees - employees_matched
        
        # Count discrepancies by type
        discrepancy_breakdown = {"Missing": 0, "Extra": 0, "Allocation_Mismatch": 0}
        total_discrepancies = 0
        
        for result in results:
            for disc in result.discrepancies:
                discrepancy_breakdown[disc.discrepancy_type] = \
                    discrepancy_breakdown.get(disc.discrepancy_type, 0) + 1
                total_discrepancies += 1
        
        return ReconciliationReport(
            generated_at=datetime.utcnow().isoformat(),
            total_employees=total_employees,
            employees_matched=employees_matched,
            employees_with_discrepancies=employees_with_discrepancies,
            total_discrepancies=total_discrepancies,
            discrepancy_breakdown=discrepancy_breakdown,
            results=results
        )
    
    def export_reconciliation_data(
        self,
        report: ReconciliationReport
    ) -> List[Dict[str, Any]]:
        """
        Export reconciliation data with financial fields filtered.
        
        Args:
            report: Reconciliation report to export
            
        Returns:
            Sanitized export data
        """
        export_data = []
        
        for result in report.results:
            record = {
                "employee_id": result.employee_id,
                "employee_name": result.employee_name,
                "match_status": result.match_status,
                "skill_board_projects": [a.project_name for a in result.skill_board_assignments],
                "hrms_projects": [a.project_name for a in result.hrms_assignments],
                "discrepancy_count": len(result.discrepancies),
                "discrepancies": [
                    {
                        "type": d.discrepancy_type,
                        "field": d.field,
                        "skill_board_value": d.skill_board_value,
                        "hrms_value": d.hrms_value
                    }
                    for d in result.discrepancies
                ]
            }
            export_data.append(record)
        
        # Ensure no financial data in export
        return financial_filter.sanitize_for_export(export_data)
    
    def get_employee_reconciliation(self, employee_id: str) -> Optional[ReconciliationResult]:
        """
        Get reconciliation result for a specific employee from database.
        
        Args:
            employee_id: Employee ID to reconcile
            
        Returns:
            ReconciliationResult or None if employee not found
        """
        if not self.db:
            return None
        
        employee = self.db.query(Employee).filter(
            Employee.employee_id == employee_id
        ).first()
        
        if not employee:
            return None
        
        # Get skill board assignments
        sb_assignments = []
        for assignment in self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == employee.id
        ).all():
            project = self.db.query(Project).filter(Project.id == assignment.project_id).first()
            if project:
                sb_assignments.append(AssignmentInfo(
                    project_name=project.name,
                    allocation_percentage=float(assignment.percentage_allocation) if assignment.percentage_allocation else None,
                    is_primary=assignment.is_primary,
                    start_date=assignment.start_date.isoformat() if assignment.start_date else None,
                    end_date=assignment.end_date.isoformat() if assignment.end_date else None
                ))
        
        # Get HRMS assignments
        hrms_assignments = []
        for assignment in self.db.query(HRMSProjectAssignment).filter(
            HRMSProjectAssignment.employee_id == employee.id
        ).all():
            project = self.db.query(HRMSProject).filter(HRMSProject.id == assignment.project_id).first()
            if project:
                hrms_assignments.append(AssignmentInfo(
                    project_name=project.project_name,
                    allocation_percentage=assignment.allocation_percentage,
                    is_primary=assignment.is_primary,
                    start_date=None,  # HRMS uses month-based tracking
                    end_date=None
                ))
        
        return self.compare_assignments(
            sb_assignments, hrms_assignments,
            employee.employee_id, employee.name
        )


# Factory function
def get_reconciliation_service(db: Session) -> ReconciliationService:
    """Create a ReconciliationService instance."""
    return ReconciliationService(db)

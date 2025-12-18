"""Authority Validator Service for Manager-Driven Skill Assessment.

Validates whether a manager has authority to assess an employee's skills.
Authority is granted through:
1. Direct report relationship (employee.line_manager_id == manager.id)
2. Project assignment relationship (manager is line_manager on a project assignment)
"""
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import Employee, EmployeeProjectAssignment, User
from app.core.permissions import RoleID


class AuthorityValidator:
    """Validates manager authority over employees for skill assessment."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_assess(
        self,
        assessor_id: int,
        assessor_role_id: int,
        target_employee_id: int
    ) -> Tuple[bool, str]:
        """
        Check if assessor has authority to assess target employee's skills.
        
        Args:
            assessor_id: The employee ID of the assessor (from employees table)
            assessor_role_id: The role_id of the assessor (from users table)
            target_employee_id: The ID of the employee to be assessed
            
        Returns:
            Tuple of (is_authorized, reason)
        """
        # Only Line Managers (5) and Delivery Managers (4) can assess
        if assessor_role_id not in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
            return False, "Only Line Managers and Delivery Managers can assess skills"
        
        # Get the assessor's employee record
        assessor_emp = self.db.query(Employee).filter(Employee.id == assessor_id).first()
        if not assessor_emp:
            return False, "Assessor employee record not found"
        
        # Get the target employee
        target_emp = self.db.query(Employee).filter(Employee.id == target_employee_id).first()
        if not target_emp:
            return False, "Target employee not found"
        
        # Check 1: Direct report relationship
        if target_emp.line_manager_id == assessor_id:
            return True, "Direct report relationship"
        
        # Check 2: Project assignment relationship
        # Manager is the line_manager on any project assignment for this employee
        project_assignment = self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == target_employee_id,
            EmployeeProjectAssignment.line_manager_id == assessor_id
        ).first()
        
        if project_assignment:
            return True, f"Project assignment relationship (Project ID: {project_assignment.project_id})"
        
        # Check 3: For Delivery Managers - location-based authority
        if assessor_role_id == RoleID.DELIVERY_MANAGER:
            if assessor_emp.location_id and target_emp.location_id:
                if assessor_emp.location_id == target_emp.location_id:
                    return True, "Same location (Delivery Manager authority)"
        
        return False, "No authority relationship found"
    
    def get_assessable_employees(
        self,
        manager_id: int,
        manager_role_id: int
    ) -> List[Employee]:
        """
        Get list of employees the manager can assess.
        
        Args:
            manager_id: The employee ID of the manager
            manager_role_id: The role_id of the manager
            
        Returns:
            List of Employee objects the manager can assess
        """
        if manager_role_id not in [RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER]:
            return []
        
        # Get the manager's employee record
        manager_emp = self.db.query(Employee).filter(Employee.id == manager_id).first()
        if not manager_emp:
            return []
        
        seen_ids = set()
        employees = []
        
        # 1. Direct reports
        direct_reports = self.db.query(Employee).filter(
            Employee.line_manager_id == manager_id,
            Employee.is_active == True
        ).all()
        
        for emp in direct_reports:
            if emp.id not in seen_ids:
                employees.append(emp)
                seen_ids.add(emp.id)
        
        # 2. Project-assigned employees
        project_assignments = self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.line_manager_id == manager_id
        ).all()
        
        for assignment in project_assignments:
            emp = self.db.query(Employee).filter(
                Employee.id == assignment.employee_id,
                Employee.is_active == True
            ).first()
            if emp and emp.id not in seen_ids:
                employees.append(emp)
                seen_ids.add(emp.id)
        
        # 3. For Delivery Managers - location-based employees
        if manager_role_id == RoleID.DELIVERY_MANAGER and manager_emp.location_id:
            location_employees = self.db.query(Employee).filter(
                Employee.location_id == manager_emp.location_id,
                Employee.is_active == True,
                Employee.id != manager_id  # Exclude self
            ).all()
            
            for emp in location_employees:
                if emp.id not in seen_ids:
                    employees.append(emp)
                    seen_ids.add(emp.id)
        
        return employees
    
    def get_manager_employee_id(self, user: User) -> Optional[int]:
        """
        Get the employee ID for a user (manager).
        
        Args:
            user: The User object
            
        Returns:
            Employee ID or None if not found
        """
        if not user.employee_id:
            return None
        
        emp = self.db.query(Employee).filter(
            Employee.employee_id == user.employee_id
        ).first()
        
        return emp.id if emp else None


def get_authority_validator(db: Session) -> AuthorityValidator:
    """Factory function to create AuthorityValidator instance."""
    return AuthorityValidator(db)

"""Property-based tests for Manager Authority Validation.

**Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
**Validates: Requirements 4.4, 4.5, 7.1, 7.2**

For any skill assessment submission by a user with role_id 4 (DM) or 5 (LM), 
the assessment should only succeed if the target employee is either a direct report 
(line_manager_id matches) OR assigned to a project managed by the assessor.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import Base, Employee, EmployeeProjectAssignment, Project
from app.services.authority_validator import AuthorityValidator
from app.core.permissions import RoleID


@contextmanager
def create_test_db():
    """Create a temporary test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_employee(db, employee_id: str, name: str, line_manager_id=None, location_id=None):
    """Helper to create an employee."""
    emp = Employee(
        employee_id=employee_id,
        name=name,
        company_email=f"{employee_id}@example.com",
        band="B",
        is_active=True,
        line_manager_id=line_manager_id,
        location_id=location_id
    )
    db.add(emp)
    db.flush()
    return emp


def create_project_assignment(db, employee_id: int, project_id: int, line_manager_id: int):
    """Helper to create a project assignment."""
    assignment = EmployeeProjectAssignment(
        employee_id=employee_id,
        project_id=project_id,
        line_manager_id=line_manager_id,
        percentage_allocation=100
    )
    db.add(assignment)
    db.flush()
    return assignment


def create_project(db, name: str):
    """Helper to create a project."""
    project = Project(
        name=name,
        description="Test project"
    )
    db.add(project)
    db.flush()
    return project


# Test strategies
role_strategy = st.sampled_from([RoleID.LINE_MANAGER, RoleID.DELIVERY_MANAGER])
non_manager_role_strategy = st.sampled_from([RoleID.EMPLOYEE, RoleID.HR, RoleID.CAPABILITY_PARTNER])


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_direct_report_grants_authority(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.4**
    
    For any manager, they should have authority over their direct reports.
    """
    with create_test_db() as db:
        # Create manager
        manager = create_employee(db, "MGR001", "Manager")
        
        # Create direct report
        report = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        is_authorized, reason = validator.can_assess(manager.id, role_id, report.id)
        
        assert is_authorized is True
        assert "Direct report" in reason


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_project_assignment_grants_authority(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.4**
    
    For any manager, they should have authority over employees assigned to their projects.
    """
    with create_test_db() as db:
        # Create manager and employee (not direct report)
        manager = create_employee(db, "MGR001", "Manager")
        employee = create_employee(db, "EMP001", "Employee")  # No line_manager_id
        
        # Create project and assignment
        project = create_project(db, "Test Project")
        create_project_assignment(db, employee.id, project.id, manager.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        is_authorized, reason = validator.can_assess(manager.id, role_id, employee.id)
        
        assert is_authorized is True
        assert "Project assignment" in reason


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_no_relationship_denies_authority(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.5**
    
    For any manager, they should NOT have authority over employees with no relationship.
    """
    with create_test_db() as db:
        # Create manager and unrelated employee
        manager = create_employee(db, "MGR001", "Manager", location_id=1)
        employee = create_employee(db, "EMP001", "Employee", location_id=2)  # Different location
        db.commit()
        
        validator = AuthorityValidator(db)
        
        # For LM, no relationship means no authority
        if role_id == RoleID.LINE_MANAGER:
            is_authorized, reason = validator.can_assess(manager.id, role_id, employee.id)
            assert is_authorized is False
            assert "No authority" in reason


@given(role_id=non_manager_role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_manager_roles_denied(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 7.1, 7.2**
    
    For any non-manager role, assessment authority should be denied.
    """
    with create_test_db() as db:
        # Create two employees
        assessor = create_employee(db, "EMP001", "Assessor")
        target = create_employee(db, "EMP002", "Target", line_manager_id=assessor.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        is_authorized, reason = validator.can_assess(assessor.id, role_id, target.id)
        
        assert is_authorized is False
        assert "Only Line Managers and Delivery Managers" in reason


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_dm_location_authority(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.2**
    
    Delivery Managers should have authority over employees in their location.
    """
    with create_test_db() as db:
        # Create DM and employee in same location
        dm = create_employee(db, "DM001", "Delivery Manager", location_id=1)
        employee = create_employee(db, "EMP001", "Employee", location_id=1)
        db.commit()
        
        validator = AuthorityValidator(db)
        
        if role_id == RoleID.DELIVERY_MANAGER:
            is_authorized, reason = validator.can_assess(dm.id, role_id, employee.id)
            assert is_authorized is True
            assert "location" in reason.lower()


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_assessable_employees_includes_direct_reports(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.1**
    
    get_assessable_employees should include all direct reports.
    """
    with create_test_db() as db:
        # Create manager with direct reports
        manager = create_employee(db, "MGR001", "Manager")
        report1 = create_employee(db, "EMP001", "Report 1", line_manager_id=manager.id)
        report2 = create_employee(db, "EMP002", "Report 2", line_manager_id=manager.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        assessable = validator.get_assessable_employees(manager.id, role_id)
        
        assessable_ids = {e.id for e in assessable}
        assert report1.id in assessable_ids
        assert report2.id in assessable_ids


@given(role_id=role_strategy)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_assessable_employees_includes_project_assigned(role_id):
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.1**
    
    get_assessable_employees should include project-assigned employees.
    """
    with create_test_db() as db:
        # Create manager and project-assigned employee
        manager = create_employee(db, "MGR001", "Manager")
        employee = create_employee(db, "EMP001", "Employee")
        
        project = create_project(db, "Test Project")
        create_project_assignment(db, employee.id, project.id, manager.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        assessable = validator.get_assessable_employees(manager.id, role_id)
        
        assessable_ids = {e.id for e in assessable}
        assert employee.id in assessable_ids


def test_assessable_employees_no_duplicates():
    """
    **Feature: manager-skill-assessment, Property 4: Manager Authority Validation**
    **Validates: Requirements 4.1**
    
    get_assessable_employees should not return duplicates.
    """
    with create_test_db() as db:
        # Create manager
        manager = create_employee(db, "MGR001", "Manager")
        
        # Create employee who is both direct report AND project-assigned
        employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
        
        project = create_project(db, "Test Project")
        create_project_assignment(db, employee.id, project.id, manager.id)
        db.commit()
        
        validator = AuthorityValidator(db)
        assessable = validator.get_assessable_employees(manager.id, RoleID.LINE_MANAGER)
        
        # Should only appear once
        assessable_ids = [e.id for e in assessable]
        assert assessable_ids.count(employee.id) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

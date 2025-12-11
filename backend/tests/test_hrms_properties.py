"""Property-based tests for HRMS integration functionality.

**Feature: hrms-integration, Property 1: HRMS Data Import Consistency**
**Validates: Requirements 1.2, 4.1, 4.2**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Employee, HRMSProject, HRMSProjectAssignment, HRMSImportLog
from contextlib import contextmanager
import tempfile
import os


@contextmanager
def create_test_db():
    """Create a temporary test database."""
    # Use in-memory SQLite database for simplicity
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


# Hypothesis strategies for generating test data
employee_strategy = st.builds(
    Employee,
    employee_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs"))),
    first_name=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),
    last_name=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),
    company_email=st.one_of(st.none(), st.emails()),
    department=st.one_of(st.none(), st.sampled_from(["Engineering", "HR", "Finance", "Marketing"])),
    role=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    team=st.one_of(st.none(), st.sampled_from(["consulting", "technical_delivery", "project_programming"])),
    band=st.one_of(st.none(), st.sampled_from(["A", "B", "C", "L1", "L2"])),
    hrms_employee_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    line_manager_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    home_capability=st.one_of(st.none(), st.sampled_from(["AWL", "Technical Delivery", "Corporate Functions"])),
    hire_date=st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
    location_id=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    is_active=st.booleans()
)

project_strategy = st.builds(
    HRMSProject,
    hrms_project_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    project_name=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs", "Nd"))),
    client_name=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    status=st.sampled_from(["Active", "Completed", "On Hold"]),
    start_date=st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
    end_date=st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2026, 12, 31))),
    project_manager_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    project_manager_name=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)


@given(employee_data=employee_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_employee_import_consistency(employee_data):
    """
    **Feature: hrms-integration, Property 1: HRMS Data Import Consistency**
    **Validates: Requirements 1.2, 4.1, 4.2**
    
    For any valid HRMS employee data, importing then querying the data 
    should return equivalent employee information.
    """
    with create_test_db() as test_db:
        # Import employee data
        test_db.add(employee_data)
        test_db.commit()
        
        # Query the imported data
        retrieved_employee = test_db.query(Employee).filter(
            Employee.employee_id == employee_data.employee_id
        ).first()
    
        # Verify consistency
        assert retrieved_employee is not None
        assert retrieved_employee.employee_id == employee_data.employee_id
        assert retrieved_employee.name == employee_data.name
        assert retrieved_employee.first_name == employee_data.first_name
        assert retrieved_employee.last_name == employee_data.last_name
        assert retrieved_employee.company_email == employee_data.company_email
        assert retrieved_employee.department == employee_data.department
        assert retrieved_employee.role == employee_data.role
        assert retrieved_employee.team == employee_data.team
        assert retrieved_employee.band == employee_data.band
        assert retrieved_employee.hrms_employee_id == employee_data.hrms_employee_id
        assert retrieved_employee.line_manager_id == employee_data.line_manager_id
        assert retrieved_employee.home_capability == employee_data.home_capability
        assert retrieved_employee.hire_date == employee_data.hire_date
        assert retrieved_employee.location_id == employee_data.location_id
        assert retrieved_employee.is_active == employee_data.is_active


@given(project_data=project_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_project_import_consistency(project_data):
    """
    **Feature: hrms-integration, Property 1: HRMS Data Import Consistency**
    **Validates: Requirements 1.2, 4.1, 4.2**
    
    For any valid HRMS project data, importing then querying the data 
    should return equivalent project information.
    """
    with create_test_db() as test_db:
        # Import project data
        test_db.add(project_data)
        test_db.commit()
        
        # Query the imported data
        retrieved_project = test_db.query(HRMSProject).filter(
            HRMSProject.hrms_project_id == project_data.hrms_project_id
        ).first()
        
        # Verify consistency
        assert retrieved_project is not None
        assert retrieved_project.hrms_project_id == project_data.hrms_project_id
        assert retrieved_project.project_name == project_data.project_name
        assert retrieved_project.client_name == project_data.client_name
        assert retrieved_project.status == project_data.status
        assert retrieved_project.start_date == project_data.start_date
        assert retrieved_project.end_date == project_data.end_date
        assert retrieved_project.project_manager_id == project_data.project_manager_id
        assert retrieved_project.project_manager_name == project_data.project_manager_name


@given(
    employee_data=employee_strategy,
    project_data=project_strategy,
    allocation_percentage=st.floats(min_value=0.0, max_value=100.0),
    allocated_days=st.floats(min_value=0.0, max_value=30.0),
    month=st.sampled_from(["2025-01", "2025-02", "2025-03", "2025-04"])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_project_assignment_consistency(employee_data, project_data, allocation_percentage, allocated_days, month):
    """
    **Feature: hrms-integration, Property 1: HRMS Data Import Consistency**
    **Validates: Requirements 1.2, 4.1, 4.2**
    
    For any valid HRMS project assignment data, importing then querying 
    should return equivalent assignment relationships.
    """
    with create_test_db() as test_db:
        # Import employee and project first
        test_db.add(employee_data)
        test_db.add(project_data)
        test_db.commit()
        
        # Create project assignment
        assignment = HRMSProjectAssignment(
            employee_id=employee_data.id,
            project_id=project_data.id,
            allocation_percentage=allocation_percentage,
            allocated_days=allocated_days,
            consumed_days=0.0,
            remaining_days=allocated_days,
            month=month,
            is_primary=True
        )
        
        test_db.add(assignment)
        test_db.commit()
        
        # Query the imported assignment
        retrieved_assignment = test_db.query(HRMSProjectAssignment).filter(
            HRMSProjectAssignment.employee_id == employee_data.id,
            HRMSProjectAssignment.project_id == project_data.id,
            HRMSProjectAssignment.month == month
        ).first()
        
        # Verify consistency
        assert retrieved_assignment is not None
        assert retrieved_assignment.employee_id == employee_data.id
        assert retrieved_assignment.project_id == project_data.id
        assert retrieved_assignment.allocation_percentage == allocation_percentage
        assert retrieved_assignment.allocated_days == allocated_days
        assert retrieved_assignment.month == month
        assert retrieved_assignment.is_primary == True
        
        # Verify relationships work
        assert retrieved_assignment.employee.employee_id == employee_data.employee_id
        assert retrieved_assignment.project.hrms_project_id == project_data.hrms_project_id


@given(
    import_type=st.sampled_from(["employees", "projects", "assignments", "attendance"]),
    records_processed=st.integers(min_value=0, max_value=1000),
    records_created=st.integers(min_value=0, max_value=1000),
    records_updated=st.integers(min_value=0, max_value=1000),
    records_failed=st.integers(min_value=0, max_value=100),
    status=st.sampled_from(["success", "failed", "partial"])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_import_log_consistency(import_type, records_processed, records_created, records_updated, records_failed, status):
    """
    **Feature: hrms-integration, Property 1: HRMS Data Import Consistency**
    **Validates: Requirements 1.2, 4.1, 4.2**
    
    For any valid HRMS import log data, storing then retrieving 
    should return equivalent import statistics.
    """
    with create_test_db() as test_db:
        # Create import log
        import_log = HRMSImportLog(
            import_type=import_type,
            records_processed=records_processed,
            records_created=records_created,
            records_updated=records_updated,
            records_failed=records_failed,
            status=status,
            processing_time_seconds=1.5,
            data_quality_score=95.0
        )
        
        test_db.add(import_log)
        test_db.commit()
        
        # Query the import log
        retrieved_log = test_db.query(HRMSImportLog).filter(
            HRMSImportLog.import_type == import_type
        ).first()
        
        # Verify consistency
        assert retrieved_log is not None
        assert retrieved_log.import_type == import_type
        assert retrieved_log.records_processed == records_processed
        assert retrieved_log.records_created == records_created
        assert retrieved_log.records_updated == records_updated
        assert retrieved_log.records_failed == records_failed
        assert retrieved_log.status == status
        assert retrieved_log.processing_time_seconds == 1.5
        assert retrieved_log.data_quality_score == 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
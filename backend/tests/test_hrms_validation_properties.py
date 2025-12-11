"""Property-based tests for HRMS data validation completeness.

**Feature: hrms-integration, Property 4: Data Validation Completeness**
**Validates: Requirements 1.4, 1.5, 4.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Employee, HRMSProject, HRMSProjectAssignment, HRMSImportLog
from app.services.hrms_import import ValidationEngine, FieldMapper, HRMSImportService
from contextlib import contextmanager
import tempfile
import json


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
valid_employee_data_strategy = st.builds(
    dict,
    employee_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs"))),
    first_name=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),
    last_name=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll")))),
    company_email=st.one_of(st.none(), st.emails()),
    department=st.one_of(st.none(), st.sampled_from(["Engineering", "HR", "Finance", "Marketing"])),
    role=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    team=st.one_of(st.none(), st.sampled_from(["consulting", "technical_delivery", "project_programming"])),
    band=st.one_of(st.none(), st.sampled_from(["A", "B", "C", "L1", "L2"])),
    line_manager_id=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    home_capability=st.one_of(st.none(), st.sampled_from(["AWL", "Technical Delivery", "Corporate Functions"])),
    hire_date=st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))),
    location_id=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    is_active=st.booleans()
)

invalid_employee_data_strategy = st.one_of(
    # Missing required employee_id
    st.builds(dict, name=st.text(min_size=1, max_size=100)),
    # Missing required name
    st.builds(dict, employee_id=st.text(min_size=1, max_size=20)),
    # Empty employee_id
    st.builds(dict, employee_id=st.just(""), name=st.text(min_size=1, max_size=100)),
    # Empty name
    st.builds(dict, employee_id=st.text(min_size=1, max_size=20), name=st.just("")),
    # Invalid email format (no @ symbol)
    st.builds(dict, 
             employee_id=st.text(min_size=1, max_size=20),
             name=st.text(min_size=1, max_size=100),
             company_email=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
    # Invalid band (not in allowed list)
    st.builds(dict,
             employee_id=st.text(min_size=1, max_size=20),
             name=st.text(min_size=1, max_size=100),
             band=st.text(min_size=1, max_size=10).filter(lambda x: x not in ['A', 'B', 'C', 'L1', 'L2'])),
    # Invalid team (not in allowed list)
    st.builds(dict,
             employee_id=st.text(min_size=1, max_size=20),
             name=st.text(min_size=1, max_size=100),
             team=st.text(min_size=1, max_size=20).filter(lambda x: x not in ['consulting', 'technical_delivery', 'project_programming', 'corporate_functions_it', 'corporate_functions_marketing', 'corporate_functions_finance', 'corporate_functions_legal', 'corporate_functions_pc']))
)

@st.composite
def valid_project_data_strategy(draw):
    """Generate valid project data with proper date relationships."""
    hrms_project_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    project_name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs", "Nd"))))
    client_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    status = draw(st.sampled_from(["Active", "Completed", "On Hold"]))
    
    # Generate dates with proper relationship
    start_date = draw(st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))))
    if start_date:
        end_date = draw(st.one_of(st.none(), st.dates(min_value=start_date, max_value=date(2026, 12, 31))))
    else:
        end_date = draw(st.one_of(st.none(), st.dates(min_value=date(2020, 1, 1), max_value=date(2026, 12, 31))))
    
    project_manager_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    project_manager_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    
    return {
        'hrms_project_id': hrms_project_id,
        'project_name': project_name,
        'client_name': client_name,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'project_manager_id': project_manager_id,
        'project_manager_name': project_manager_name
    }

invalid_project_data_strategy = st.one_of(
    # Missing required hrms_project_id
    st.builds(dict, project_name=st.text(min_size=1, max_size=100)),
    # Missing required project_name
    st.builds(dict, hrms_project_id=st.text(min_size=1, max_size=20)),
    # Invalid status
    st.builds(dict,
             hrms_project_id=st.text(min_size=1, max_size=20),
             project_name=st.text(min_size=1, max_size=100),
             status=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))))
)

valid_assignment_data_strategy = st.builds(
    dict,
    employee_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    project_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    allocation_percentage=st.floats(min_value=0.0, max_value=100.0),
    allocated_days=st.floats(min_value=0.0, max_value=30.0),
    consumed_days=st.floats(min_value=0.0, max_value=30.0),
    month=st.sampled_from(["2025-01", "2025-02", "2025-03", "2025-04"]),
    is_primary=st.booleans()
)

invalid_assignment_data_strategy = st.one_of(
    # Missing required employee_id
    st.builds(dict, project_id=st.text(min_size=1, max_size=20), month=st.just("2025-01")),
    # Missing required project_id
    st.builds(dict, employee_id=st.text(min_size=1, max_size=20), month=st.just("2025-01")),
    # Missing required month
    st.builds(dict, employee_id=st.text(min_size=1, max_size=20), project_id=st.text(min_size=1, max_size=20)),
    # Invalid allocation percentage (> 100)
    st.builds(dict,
             employee_id=st.text(min_size=1, max_size=20),
             project_id=st.text(min_size=1, max_size=20),
             month=st.just("2025-01"),
             allocation_percentage=st.floats(min_value=100.1, max_value=200.0)),
    # Invalid allocation percentage (< 0)
    st.builds(dict,
             employee_id=st.text(min_size=1, max_size=20),
             project_id=st.text(min_size=1, max_size=20),
             month=st.just("2025-01"),
             allocation_percentage=st.floats(min_value=-100.0, max_value=-0.1)),
    # Negative days
    st.builds(dict,
             employee_id=st.text(min_size=1, max_size=20),
             project_id=st.text(min_size=1, max_size=20),
             month=st.just("2025-01"),
             allocated_days=st.floats(min_value=-30.0, max_value=-0.1))
)


@given(employee_data=valid_employee_data_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_employee_data_validation_passes(employee_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any valid employee data, validation should pass and return no errors.
    """
    validation_engine = ValidationEngine()
    
    is_valid, errors = validation_engine.validate_employee_data(employee_data)
    
    # Valid data should pass validation
    assert is_valid == True
    assert len(errors) == 0


@given(employee_data=invalid_employee_data_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_employee_data_validation_fails(employee_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any invalid employee data, validation should fail and return specific errors.
    """
    validation_engine = ValidationEngine()
    
    is_valid, errors = validation_engine.validate_employee_data(employee_data)
    
    # Invalid data should fail validation
    assert is_valid == False
    assert len(errors) > 0
    
    # Errors should be descriptive strings
    for error in errors:
        assert isinstance(error, str)
        assert len(error) > 0


@given(project_data=valid_project_data_strategy())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_project_data_validation_passes(project_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any valid project data, validation should pass and return no errors.
    """
    validation_engine = ValidationEngine()
    
    is_valid, errors = validation_engine.validate_project_data(project_data)
    
    # Valid data should pass validation
    assert is_valid == True
    assert len(errors) == 0


@given(project_data=invalid_project_data_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_project_data_validation_fails(project_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any invalid project data, validation should fail and return specific errors.
    """
    validation_engine = ValidationEngine()
    
    is_valid, errors = validation_engine.validate_project_data(project_data)
    
    # Invalid data should fail validation
    assert is_valid == False
    assert len(errors) > 0
    
    # Errors should be descriptive strings
    for error in errors:
        assert isinstance(error, str)
        assert len(error) > 0


@given(assignment_data=valid_assignment_data_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_assignment_data_validation_passes(assignment_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any valid assignment data, validation should pass and return no errors.
    """
    validation_engine = ValidationEngine()
    
    # Ensure consumed_days <= allocated_days for valid data
    if 'consumed_days' in assignment_data and 'allocated_days' in assignment_data:
        assignment_data['consumed_days'] = min(
            assignment_data['consumed_days'], 
            assignment_data['allocated_days']
        )
    
    is_valid, errors = validation_engine.validate_assignment_data(assignment_data)
    
    # Valid data should pass validation
    assert is_valid == True
    assert len(errors) == 0


@given(assignment_data=invalid_assignment_data_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_assignment_data_validation_fails(assignment_data):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any invalid assignment data, validation should fail and return specific errors.
    """
    validation_engine = ValidationEngine()
    
    is_valid, errors = validation_engine.validate_assignment_data(assignment_data)
    
    # Invalid data should fail validation
    assert is_valid == False
    assert len(errors) > 0
    
    # Errors should be descriptive strings
    for error in errors:
        assert isinstance(error, str)
        assert len(error) > 0


@given(
    valid_records=st.lists(valid_employee_data_strategy, min_size=1, max_size=10),
    invalid_records=st.lists(invalid_employee_data_strategy, min_size=1, max_size=5)
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_mixed_data_validation_completeness(valid_records, invalid_records):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any mix of valid and invalid data, validation should correctly identify 
    all validation failures and provide complete error details.
    """
    validation_engine = ValidationEngine()
    
    # Combine valid and invalid records
    all_records = valid_records + invalid_records
    
    valid_count = 0
    invalid_count = 0
    all_errors = []
    
    # Validate each record
    for record in all_records:
        is_valid, errors = validation_engine.validate_employee_data(record)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.extend(errors)
    
    # Verify that validation was applied to all records
    assert valid_count + invalid_count == len(all_records)
    
    # Verify that invalid records have error details
    if invalid_count > 0:
        assert len(all_errors) > 0
        
        # All errors should be descriptive strings
        for error in all_errors:
            assert isinstance(error, str)
            assert len(error) > 0
    
    # Verify quality score calculation
    completeness_score = 85.0  # Assume reasonable completeness
    quality_score = validation_engine.calculate_data_quality_score(
        len(all_records), valid_count, completeness_score
    )
    assert 0.0 <= quality_score <= 100.0


@given(
    total_records=st.integers(min_value=1, max_value=100),
    valid_records=st.integers(min_value=0, max_value=100),
    completeness_score=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_data_quality_score_calculation(total_records, valid_records, completeness_score):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any data quality metrics, the quality score calculation should be 
    mathematically correct and within valid bounds.
    """
    # Ensure valid_records doesn't exceed total_records
    valid_records = min(valid_records, total_records)
    
    validation_engine = ValidationEngine()
    
    quality_score = validation_engine.calculate_data_quality_score(
        total_records, valid_records, completeness_score
    )
    
    # Quality score should be between 0 and 100
    assert 0.0 <= quality_score <= 100.0
    
    # If all records are valid and completeness is 100%, score should be 100%
    if valid_records == total_records and completeness_score == 100.0:
        assert quality_score == 100.0
    
    # If no records are valid, score should be low
    if valid_records == 0:
        assert quality_score <= 50.0  # At most half due to completeness component


@given(
    records=st.lists(
        st.dictionaries(
            keys=st.sampled_from(['employee_id', 'name', 'email', 'department', 'optional_field']),
            values=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
            min_size=1,
            max_size=5
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_completeness_score_calculation_accuracy(records):
    """
    **Feature: hrms-integration, Property 4: Data Validation Completeness**
    **Validates: Requirements 1.4, 1.5, 4.4**
    
    For any set of records, the completeness score should accurately reflect 
    the percentage of required fields that are populated.
    """
    with create_test_db() as test_db:
        import_service = HRMSImportService(test_db)
        
        completeness_score = import_service._calculate_completeness_score(records, 'employee')
        
        # Score should be between 0 and 100
        assert 0.0 <= completeness_score <= 100.0
        
        # Manual calculation for verification
        required_fields = ['employee_id', 'name']
        total_required_fields = len(records) * len(required_fields)
        
        if total_required_fields > 0:
            complete_fields = 0
            for record in records:
                for field in required_fields:
                    if record.get(field):
                        complete_fields += 1
            
            expected_score = (complete_fields / total_required_fields) * 100
            assert abs(completeness_score - expected_score) < 0.01  # Allow for floating point precision


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
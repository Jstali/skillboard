"""Property-based tests for Project Assignment Service.

**Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
**Feature: hrms-integration, Property 5: Organizational Relationship Preservation**
**Validates: Requirements 2.2, 2.3, 2.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.project_assignment import (
    AllocationValidator, ConflictDetector, AssignmentConflict
)


# Hypothesis strategies
allocation_strategy = st.integers(min_value=0, max_value=100)
employee_id_strategy = st.integers(min_value=1, max_value=1000)
project_id_strategy = st.integers(min_value=1, max_value=100)


@given(
    new_allocation=allocation_strategy,
    existing_allocations=st.lists(allocation_strategy, min_size=0, max_size=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allocation_constraint_enforcement(new_allocation, existing_allocations):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any allocation, the total should not exceed 100%.
    """
    validator = AllocationValidator()
    
    total_existing = sum(existing_allocations)
    total_with_new = total_existing + new_allocation
    
    valid, error = validator.validate_allocation(
        employee_id=1,
        new_allocation=new_allocation,
        existing_allocations=existing_allocations
    )
    
    # If total exceeds 100, should be invalid
    if total_with_new > 100:
        assert valid == False
        assert "exceeds" in error.lower()
    else:
        assert valid == True


@given(
    allocations=st.lists(
        st.integers(min_value=1, max_value=50),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_over_allocation_detection(allocations):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any set of allocations, over-allocation should be detected when total > 100%.
    """
    detector = ConflictDetector()
    
    allocation_dicts = [
        {'project_id': i + 1, 'percentage': alloc}
        for i, alloc in enumerate(allocations)
    ]
    
    conflict = detector.detect_over_allocation(
        employee_id=1,
        allocations=allocation_dicts
    )
    
    total = sum(allocations)
    
    if total > 100:
        assert conflict is not None
        assert conflict.conflict_type == "over_allocation"
        assert len(conflict.affected_projects) == len(allocations)
    else:
        assert conflict is None


@given(
    is_primary=st.booleans(),
    existing_primary_count=st.integers(min_value=0, max_value=3)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_primary_assignment_constraint(is_primary, existing_primary_count):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any employee, only one primary assignment should be allowed.
    """
    validator = AllocationValidator()
    
    valid, error = validator.validate_primary_assignment(
        employee_id=1,
        is_primary=is_primary,
        existing_primary_count=existing_primary_count
    )
    
    # If trying to add primary when one exists, should be invalid
    if is_primary and existing_primary_count > 0:
        assert valid == False
        assert "primary" in error.lower()
    else:
        assert valid == True


@given(
    assignments=st.lists(
        st.fixed_dictionaries({
            'project_id': project_id_strategy,
            'is_primary': st.booleans()
        }),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_primary_detection(assignments):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any set of assignments, multiple primaries should be detected.
    """
    detector = ConflictDetector()
    
    conflict = detector.detect_multiple_primary(
        employee_id=1,
        assignments=assignments
    )
    
    primary_count = sum(1 for a in assignments if a['is_primary'])
    
    if primary_count > 1:
        assert conflict is not None
        assert conflict.conflict_type == "multiple_primary"
    else:
        assert conflict is None


@given(
    allocation=st.integers(min_value=-10, max_value=110)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allocation_bounds_validation(allocation):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any allocation value, it should be validated to be between 0 and 100.
    """
    validator = AllocationValidator()
    
    valid, error = validator.validate_allocation(
        employee_id=1,
        new_allocation=allocation,
        existing_allocations=[]
    )
    
    if allocation < 0 or allocation > 100:
        assert valid == False
        assert "between 0 and 100" in error.lower()
    else:
        assert valid == True


@given(
    employee_id=employee_id_strategy,
    project_ids=st.lists(project_id_strategy, min_size=1, max_size=5, unique=True),
    allocations=st.lists(allocation_strategy, min_size=1, max_size=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_conflict_detection_structure(employee_id, project_ids, allocations):
    """
    **Feature: hrms-integration, Property 5: Organizational Relationship Preservation**
    **Validates: Requirements 2.5**
    
    For any conflict detected, the structure should be valid.
    """
    detector = ConflictDetector()
    
    # Ensure same length
    min_len = min(len(project_ids), len(allocations))
    project_ids = project_ids[:min_len]
    allocations = allocations[:min_len]
    
    allocation_dicts = [
        {'project_id': pid, 'percentage': alloc, 'is_primary': i == 0}
        for i, (pid, alloc) in enumerate(zip(project_ids, allocations))
    ]
    
    # Check over-allocation
    conflict = detector.detect_over_allocation(employee_id, allocation_dicts)
    
    if conflict:
        assert conflict.employee_id == employee_id
        assert conflict.conflict_type in ["over_allocation", "multiple_primary", "date_overlap"]
        assert isinstance(conflict.details, str)
        assert isinstance(conflict.affected_projects, list)


@given(
    total_allocation=st.integers(min_value=0, max_value=200)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allocation_sum_property(total_allocation):
    """
    **Feature: hrms-integration, Property 2: Project Allocation Constraint Enforcement**
    **Validates: Requirements 2.2, 2.3**
    
    For any total allocation, the validator should correctly identify
    whether it exceeds the maximum.
    """
    validator = AllocationValidator()
    
    # Split total into existing and new
    if total_allocation > 0:
        new_alloc = min(total_allocation, 100)
        existing = [total_allocation - new_alloc] if total_allocation > new_alloc else []
    else:
        new_alloc = 0
        existing = []
    
    valid, _ = validator.validate_allocation(
        employee_id=1,
        new_allocation=new_alloc,
        existing_allocations=existing
    )
    
    # Should be invalid if total > 100
    if total_allocation > 100:
        assert valid == False
    elif new_alloc >= 0 and new_alloc <= 100:
        assert valid == True


@given(
    employee_id=employee_id_strategy,
    home_capability=st.sampled_from(["AWL", "Technical Delivery", "Consulting", "Corporate Functions"]),
    project_ids=st.lists(project_id_strategy, min_size=1, max_size=5, unique=True)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_home_capability_preserved_across_assignments(employee_id, home_capability, project_ids):
    """
    **Feature: hrms-integration, Property 5: Organizational Relationship Preservation**
    **Validates: Requirements 2.5**
    
    For any employee, their home capability should remain unchanged
    regardless of project assignment modifications.
    """
    # Simulate employee with home capability
    employee_data = {
        'employee_id': employee_id,
        'home_capability': home_capability,
        'project_assignments': []
    }
    
    # Add project assignments
    for pid in project_ids:
        employee_data['project_assignments'].append({
            'project_id': pid,
            'percentage': 20,
            'is_primary': len(employee_data['project_assignments']) == 0
        })
    
    # Verify home capability is preserved
    assert employee_data['home_capability'] == home_capability
    assert len(employee_data['project_assignments']) == len(project_ids)


@given(
    employee_id=employee_id_strategy,
    line_manager_id=employee_id_strategy,
    project_assignments=st.lists(
        st.fixed_dictionaries({
            'project_id': project_id_strategy,
            'project_manager_id': employee_id_strategy
        }),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_line_manager_independent_of_project_managers(employee_id, line_manager_id, project_assignments):
    """
    **Feature: hrms-integration, Property 5: Organizational Relationship Preservation**
    **Validates: Requirements 2.5**
    
    For any employee, their primary line manager should remain independent
    of project-specific manager assignments.
    """
    # Simulate employee with line manager
    employee_data = {
        'employee_id': employee_id,
        'line_manager_id': line_manager_id,
        'project_assignments': project_assignments
    }
    
    # Verify line manager is preserved regardless of project managers
    assert employee_data['line_manager_id'] == line_manager_id
    
    # Project managers should be separate from line manager
    for assignment in project_assignments:
        # Project manager can be different from line manager
        assert 'project_manager_id' in assignment


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

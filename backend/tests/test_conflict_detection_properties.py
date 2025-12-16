"""Property-based tests for Conflict Detection and Investment Project Classification.

**Feature: hrms-integration, Property 7: Conflict Detection Accuracy**
**Feature: hrms-integration, Property 15: Investment Project Classification**
**Validates: Requirements 3.5, 6.2, 6.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.project_assignment import ConflictDetector, AssignmentConflict
from app.services.investment_project import (
    InvestmentProjectService, ProjectClassification, ProjectType
)


# Hypothesis strategies
employee_id_strategy = st.integers(min_value=1, max_value=1000)
project_id_strategy = st.integers(min_value=1, max_value=100)
allocation_strategy = st.integers(min_value=0, max_value=100)


# ============================================================================
# Conflict Detection Tests (Property 7)
# ============================================================================

@given(
    allocations=st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_over_allocation_detection_accuracy(allocations):
    """
    **Feature: hrms-integration, Property 7: Conflict Detection Accuracy**
    **Validates: Requirements 3.5, 6.2**
    
    For any set of allocations, over-allocation should be accurately detected.
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
        assert "exceeds" in conflict.details.lower() or str(total) in conflict.details
    else:
        assert conflict is None


@given(
    assignments=st.lists(
        st.fixed_dictionaries({
            'project_id': project_id_strategy,
            'is_primary': st.booleans()
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_primary_detection_accuracy(assignments):
    """
    **Feature: hrms-integration, Property 7: Conflict Detection Accuracy**
    **Validates: Requirements 3.5, 6.2**
    
    For any set of assignments, multiple primary assignments should be detected.
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
        assert len(conflict.affected_projects) == primary_count
    else:
        assert conflict is None


@given(
    employee_id=employee_id_strategy,
    num_conflicts=st.integers(min_value=0, max_value=3)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_conflict_structure_validity(employee_id, num_conflicts):
    """
    **Feature: hrms-integration, Property 7: Conflict Detection Accuracy**
    **Validates: Requirements 3.5, 6.2**
    
    For any detected conflict, the structure should be valid.
    """
    # Create a conflict manually to test structure
    if num_conflicts > 0:
        conflict = AssignmentConflict(
            employee_id=employee_id,
            conflict_type="over_allocation",
            details="Test conflict",
            affected_projects=[1, 2, 3][:num_conflicts]
        )
        
        assert conflict.employee_id == employee_id
        assert conflict.conflict_type in ["over_allocation", "multiple_primary", "date_overlap"]
        assert isinstance(conflict.details, str)
        assert isinstance(conflict.affected_projects, list)
        assert len(conflict.affected_projects) == num_conflicts


@given(
    allocations=st.lists(
        st.integers(min_value=0, max_value=50),
        min_size=2,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_no_false_positive_conflicts(allocations):
    """
    **Feature: hrms-integration, Property 7: Conflict Detection Accuracy**
    **Validates: Requirements 3.5, 6.2**
    
    For any valid allocation set (total <= 100), no conflict should be detected.
    """
    detector = ConflictDetector()
    
    # Ensure total is <= 100
    total = sum(allocations)
    if total > 100:
        # Scale down allocations
        scale = 100 / total
        allocations = [int(a * scale) for a in allocations]
    
    allocation_dicts = [
        {'project_id': i + 1, 'percentage': alloc}
        for i, alloc in enumerate(allocations)
    ]
    
    conflict = detector.detect_over_allocation(
        employee_id=1,
        allocations=allocation_dicts
    )
    
    # Should not detect false positive
    if sum(allocations) <= 100:
        assert conflict is None


# ============================================================================
# Investment Project Classification Tests (Property 15)
# ============================================================================

@given(
    project_id=project_id_strategy,
    project_name=st.sampled_from([
        "INV-Research Project",
        "R&D Innovation",
        "Internal Training",
        "POC-New Feature",
        "Bench Assignment",
        "Investment Initiative"
    ])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_investment_project_detection(project_id, project_name):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any project with investment keywords, it should be classified as investment.
    """
    service = InvestmentProjectService()
    
    classification = service.classify_project(project_id, project_name)
    
    assert classification.is_investment == True
    assert classification.project_type in [
        ProjectType.INVESTMENT,
        ProjectType.INTERNAL,
        ProjectType.TRAINING,
        ProjectType.BENCH
    ]
    # Assignment should always be visible
    assert classification.assignment_visible == True


@given(
    project_id=project_id_strategy,
    project_name=st.sampled_from([
        "Client Project Alpha",
        "Customer Implementation",
        "External Delivery",
        "Production Support",
        "Consulting Engagement"
    ])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_billable_project_detection(project_id, project_name):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any project without investment keywords, it should be classified as billable.
    """
    service = InvestmentProjectService()
    
    classification = service.classify_project(project_id, project_name)
    
    assert classification.is_investment == False
    assert classification.project_type == ProjectType.BILLABLE
    assert classification.assignment_visible == True


@given(
    project_data=st.fixed_dictionaries({
        'project_id': project_id_strategy,
        'project_name': st.text(min_size=1, max_size=50),
        'budget': st.floats(min_value=0, max_value=1000000),
        'revenue': st.floats(min_value=0, max_value=1000000),
        'cost': st.floats(min_value=0, max_value=1000000),
        'description': st.text(min_size=0, max_size=100)
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_financial_data_filtered_from_project(project_data):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any project data, financial fields should be filtered out.
    """
    service = InvestmentProjectService()
    
    filtered = service.filter_financial_from_project(project_data)
    
    # Financial fields should be removed
    assert 'budget' not in filtered
    assert 'revenue' not in filtered
    assert 'cost' not in filtered
    
    # Non-financial fields should be preserved
    assert 'project_id' in filtered
    assert 'project_name' in filtered
    assert 'description' in filtered


@given(
    project_name=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_classification_always_has_visibility(project_name):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any project classification, assignment visibility should always be true.
    """
    service = InvestmentProjectService()
    
    classification = service.classify_project(1, project_name)
    
    # Assignments should always be visible regardless of project type
    assert classification.assignment_visible == True


@given(
    type_hint=st.sampled_from([
        "investment",
        "r&d",
        "internal",
        "non-billable",
        None
    ])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_type_hint_classification(type_hint):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any type hint, classification should respect the hint.
    """
    service = InvestmentProjectService()
    
    # Use a neutral project name
    classification = service.classify_project(
        1,
        "Generic Project",
        project_type_hint=type_hint
    )
    
    if type_hint and type_hint.lower() in ["investment", "r&d", "internal", "non-billable"]:
        assert classification.is_investment == True
    else:
        # Without hint, neutral name should be billable
        assert classification.is_investment == False


@given(
    project_id=project_id_strategy,
    project_name=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_classification_structure_validity(project_id, project_name):
    """
    **Feature: hrms-integration, Property 15: Investment Project Classification**
    **Validates: Requirements 6.3**
    
    For any classification, the structure should be valid.
    """
    service = InvestmentProjectService()
    
    classification = service.classify_project(project_id, project_name)
    
    assert classification.project_id == project_id
    assert classification.project_name == project_name
    assert classification.project_type in list(ProjectType)
    assert isinstance(classification.is_investment, bool)
    assert isinstance(classification.assignment_visible, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

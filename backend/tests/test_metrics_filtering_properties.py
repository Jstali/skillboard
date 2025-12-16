"""Property-based tests for Metrics Filtering Service.

**Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
**Validates: Requirements 5.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.metrics_filtering import (
    MetricsFilteringService, FilterCriteria, FilteredResult, metrics_filter
)


# Hypothesis strategies
capability_strategy = st.sampled_from([
    "Technical Delivery", "Consulting", "AWL", "Corporate Functions"
])

team_strategy = st.sampled_from([
    "consulting", "technical_delivery", "project_programming", "corporate_functions_it"
])

band_strategy = st.sampled_from(["A", "B", "C", "L1", "L2"])


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    ),
    filter_capability=capability_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_capability_filter_correctness(records, filter_capability):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For any capability filter, all filtered results should match the capability.
    """
    service = MetricsFilteringService()
    
    filtered = service.filter_by_capability(records, filter_capability)
    
    # All filtered records should match the capability
    for record in filtered:
        assert record['capability'].lower() == filter_capability.lower()
    
    # Filtered count should not exceed original
    assert len(filtered) <= len(records)


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    ),
    filter_team=team_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_team_filter_correctness(records, filter_team):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For any team filter, all filtered results should match the team.
    """
    service = MetricsFilteringService()
    
    filtered = service.filter_by_team(records, filter_team)
    
    # All filtered records should match the team
    for record in filtered:
        assert record['team'].lower() == filter_team.lower()
    
    # Filtered count should not exceed original
    assert len(filtered) <= len(records)


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'band': band_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    ),
    filter_capability=st.one_of(st.none(), capability_strategy),
    filter_team=st.one_of(st.none(), team_strategy)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_combined_filter_correctness(records, filter_capability, filter_team):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For any combination of filters, all filtered results should match
    all applied criteria.
    """
    service = MetricsFilteringService()
    
    criteria = FilterCriteria(
        capability=filter_capability,
        team=filter_team
    )
    
    result = service.filter_by_criteria(records, criteria)
    
    # Verify result structure
    assert result.original_count == len(records)
    assert result.filtered_count == len(result.data)
    assert result.filtered_count <= result.original_count
    
    # All filtered records should match all criteria
    for record in result.data:
        if filter_capability:
            assert record['capability'].lower() == filter_capability.lower()
        if filter_team:
            assert record['team'].lower() == filter_team.lower()


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=0,
        max_size=20
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_empty_filter_returns_all(records):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For no filter criteria, all records should be returned.
    """
    service = MetricsFilteringService()
    
    criteria = FilterCriteria()  # No filters
    result = service.filter_by_criteria(records, criteria)
    
    # All records should be returned
    assert result.filtered_count == result.original_count
    assert len(result.data) == len(records)


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'band': band_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    ),
    criteria=st.fixed_dictionaries({
        'capability': st.one_of(st.none(), capability_strategy),
        'team': st.one_of(st.none(), team_strategy),
        'band': st.one_of(st.none(), band_strategy)
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filter_validation(records, criteria):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For any filter result, validation should confirm all records match criteria.
    """
    service = MetricsFilteringService()
    
    filter_criteria = FilterCriteria(**criteria)
    result = service.filter_by_criteria(records, filter_criteria)
    
    # Validation should pass for filtered results
    is_valid = service.validate_filter_result(records, result.data, filter_criteria)
    assert is_valid == True


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_unique_values(records):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    For any dataset, get_unique_values should return all distinct values.
    """
    service = MetricsFilteringService()
    
    unique_capabilities = service.get_unique_values(records, 'capability')
    unique_teams = service.get_unique_values(records, 'team')
    
    # Unique values should be subset of all values
    all_capabilities = set(r['capability'] for r in records)
    all_teams = set(r['team'] for r in records)
    
    assert set(unique_capabilities) == all_capabilities
    assert set(unique_teams) == all_teams


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'capability': capability_strategy,
            'team': team_strategy,
            'skill_count': st.integers(min_value=0, max_value=50)
        }),
        min_size=1,
        max_size=20
    ),
    filter_capability=capability_strategy,
    filter_team=team_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filter_order_independence(records, filter_capability, filter_team):
    """
    **Feature: skill-board-views, Property 8: Metrics Filtering Correctness**
    **Validates: Requirements 5.5**
    
    Applying filters in different orders should produce the same result.
    """
    service = MetricsFilteringService()
    
    # Filter capability first, then team
    result1 = service.filter_by_capability(records, filter_capability)
    result1 = service.filter_by_team(result1, filter_team)
    
    # Filter team first, then capability
    result2 = service.filter_by_team(records, filter_team)
    result2 = service.filter_by_capability(result2, filter_capability)
    
    # Results should be the same
    assert len(result1) == len(result2)
    
    # Convert to comparable format
    result1_set = {frozenset(r.items()) for r in result1}
    result2_set = {frozenset(r.items()) for r in result2}
    
    assert result1_set == result2_set


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Property-based tests for Data Anonymization Service.

**Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
**Validates: Requirements 5.2, 5.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.data_anonymization import (
    DataAnonymizationService, AnonymizedMetrics, anonymization_service
)


# Hypothesis strategies
non_personal_field_strategy = st.sampled_from([
    'skill_name', 'proficiency', 'rating', 'category', 'team',
    'capability', 'department', 'years_experience', 'skill_count',
    'coverage_percentage', 'alignment_score', 'gap_value'
])

personal_field_strategy = st.sampled_from([
    'employee_id', 'name', 'first_name', 'last_name', 'email',
    'company_email', 'phone', 'address', 'user_id', 'manager_name',
    'line_manager_id', 'hrms_employee_id'
])

value_strategy = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False),
    st.booleans(),
    st.none()
)


@given(
    non_personal_data=st.dictionaries(
        keys=non_personal_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_personal_data_preserved(non_personal_data):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any data containing only non-personal fields, all data should
    be preserved after anonymization.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    anonymized = service.remove_personal_identifiers(non_personal_data)
    
    # All non-personal fields should be preserved
    assert set(anonymized.keys()) == set(non_personal_data.keys())
    
    # Values should be unchanged
    for key in non_personal_data:
        assert anonymized[key] == non_personal_data[key]
    
    # Validation should pass
    assert service.validate_no_personal_data(anonymized) == True


@given(
    personal_data=st.dictionaries(
        keys=personal_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_personal_data_removed(personal_data):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any data containing personal fields, all personal fields should
    be removed after anonymization.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    anonymized = service.remove_personal_identifiers(personal_data)
    
    # All personal fields should be removed
    assert len(anonymized) == 0
    
    # Validation should pass on anonymized data
    assert service.validate_no_personal_data(anonymized) == True
    
    # Original data should fail validation
    assert service.validate_no_personal_data(personal_data) == False


@given(
    non_personal=st.dictionaries(
        keys=non_personal_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    ),
    personal=st.dictionaries(
        keys=personal_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_mixed_data_anonymization(non_personal, personal):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any data containing both personal and non-personal fields,
    only personal fields should be removed.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    mixed_data = {**non_personal, **personal}
    anonymized = service.remove_personal_identifiers(mixed_data)
    
    # Only non-personal fields should remain
    for key in anonymized:
        assert key in non_personal
        assert key not in personal
    
    # All non-personal fields should be preserved
    for key in non_personal:
        assert key in anonymized
        assert anonymized[key] == non_personal[key]
    
    # Validation should pass
    assert service.validate_no_personal_data(anonymized) == True


@given(
    nested_data=st.fixed_dictionaries({
        'metrics': st.fixed_dictionaries({
            'skill_count': st.integers(min_value=0, max_value=100),
            'coverage': st.floats(min_value=0, max_value=100, allow_nan=False)
        }),
        'personal': st.fixed_dictionaries({
            'employee_id': st.text(min_size=1, max_size=20),
            'name': st.text(min_size=1, max_size=50)
        })
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_nested_personal_data_removed(nested_data):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any nested data structure, personal fields should be removed
    at all levels.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    anonymized = service.remove_personal_identifiers(nested_data)
    
    # Personal section should be empty (all fields removed)
    assert 'personal' in anonymized
    assert len(anonymized['personal']) == 0
    
    # Metrics section should be preserved
    assert 'metrics' in anonymized
    assert 'skill_count' in anonymized['metrics']
    assert 'coverage' in anonymized['metrics']
    
    # Validation should pass
    assert service.validate_no_personal_data(anonymized) == True


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'employee_id': st.text(min_size=1, max_size=20),
            'skill_count': st.integers(min_value=0, max_value=50),
            'proficiency': st.floats(min_value=1, max_value=5, allow_nan=False)
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_aggregate_without_individuals(records):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any list of records, aggregation should remove individual
    identifiers while maintaining statistical accuracy.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    result = service.aggregate_without_individuals(
        records,
        aggregate_fields=['skill_count', 'proficiency']
    )
    
    # Should have correct count
    assert result['count'] == len(records)
    
    # Aggregates should be present
    assert 'aggregates' in result
    
    # Verify statistical accuracy for skill_count
    if 'skill_count' in result['aggregates']:
        agg = result['aggregates']['skill_count']
        expected_sum = sum(r['skill_count'] for r in records)
        expected_avg = expected_sum / len(records)
        
        assert agg['sum'] == expected_sum
        assert abs(agg['avg'] - expected_avg) < 0.01
        assert agg['count'] == len(records)


@given(field_name=personal_field_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_personal_field_detection(field_name):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any personal field name, it should be correctly identified.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    assert service._is_personal_field(field_name) == True


@given(field_name=non_personal_field_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_personal_field_detection(field_name):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any non-personal field name, it should not be identified as personal.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    assert service._is_personal_field(field_name) == False


@given(
    metric_type=st.text(min_size=1, max_size=30),
    record_count=st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_anonymized_metrics_creation(metric_type, record_count):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any anonymized metrics, the structure should be valid.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    data = {
        'skill_count': 10,
        'employee_id': 'EMP001',  # Should be removed
        'coverage': 85.5
    }
    
    metrics = service.create_anonymized_metrics(metric_type, data, record_count)
    
    # Should have correct structure
    assert metrics.metric_type == metric_type
    assert metrics.record_count == record_count
    assert metrics.is_anonymized == True
    
    # Personal data should be removed
    assert 'employee_id' not in metrics.data
    assert 'skill_count' in metrics.data
    assert 'coverage' in metrics.data


@given(
    data=st.fixed_dictionaries({
        'employee_id': st.text(min_size=1, max_size=20),
        'nested': st.fixed_dictionaries({
            'name': st.text(min_size=1, max_size=50),
            'skill': st.text(min_size=1, max_size=30)
        })
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_personal_fields_in_data(data):
    """
    **Feature: skill-board-views, Property 5: Data Anonymization for Aggregate Metrics**
    **Validates: Requirements 5.2, 5.4**
    
    For any data with personal fields, get_personal_fields_in_data should
    correctly identify all personal field paths.
    """
    service = DataAnonymizationService(strict_mode=False)
    
    personal_fields = service.get_personal_fields_in_data(data)
    
    # Should find employee_id and nested.name
    assert 'employee_id' in personal_fields
    assert 'nested.name' in personal_fields
    
    # Should not include non-personal fields
    assert 'nested.skill' not in personal_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

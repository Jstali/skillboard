"""Property-based tests for Financial Data Filter Service.

**Feature: skill-board-views, Property 4: Financial Data Exclusion**
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.financial_filter import FinancialDataFilter, financial_filter


# Hypothesis strategies for generating test data
non_financial_field_strategy = st.sampled_from([
    'employee_id', 'name', 'first_name', 'last_name', 'email',
    'department', 'team', 'role', 'skill_name', 'proficiency',
    'rating', 'years_experience', 'capability', 'project_name',
    'allocation_percentage', 'start_date', 'end_date', 'status',
    'category', 'description', 'notes', 'created_at', 'updated_at'
])

financial_field_strategy = st.sampled_from([
    'billing_rate', 'revenue', 'cost', 'profit', 'salary',
    'budget', 'invoice', 'compensation', 'wage', 'bill_rate',
    'total_revenue', 'labor_cost', 'profit_margin', 'base_salary',
    'hourly_rate', 'daily_rate', 'unbilled', 'billed', 'financial_status'
])

value_strategy = st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(min_value=-1000000, max_value=1000000, allow_nan=False),
    st.booleans(),
    st.none()
)


@given(
    non_financial_fields=st.dictionaries(
        keys=non_financial_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_financial_data_passes_through(non_financial_fields):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any data containing only non-financial fields, the filter should 
    pass all data through unchanged.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Filter the data
    filtered_data = filter_service.filter_response(non_financial_fields)
    
    # All non-financial fields should be preserved
    assert set(filtered_data.keys()) == set(non_financial_fields.keys())
    
    # Values should be unchanged
    for key in non_financial_fields:
        assert filtered_data[key] == non_financial_fields[key]
    
    # Validation should pass
    assert filter_service.validate_no_financial_data(filtered_data) == True


@given(
    financial_fields=st.dictionaries(
        keys=financial_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_financial_data_is_removed(financial_fields):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any data containing financial fields, the filter should remove 
    all financial fields from the response.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Filter the data
    filtered_data = filter_service.filter_response(financial_fields)
    
    # All financial fields should be removed
    assert len(filtered_data) == 0
    
    # Validation should pass on filtered data
    assert filter_service.validate_no_financial_data(filtered_data) == True
    
    # Original data should fail validation
    assert filter_service.validate_no_financial_data(financial_fields) == False


@given(
    non_financial_fields=st.dictionaries(
        keys=non_financial_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    ),
    financial_fields=st.dictionaries(
        keys=financial_field_strategy,
        values=value_strategy,
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_mixed_data_filters_correctly(non_financial_fields, financial_fields):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any data containing both financial and non-financial fields, 
    the filter should remove only financial fields while preserving others.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Combine financial and non-financial data
    mixed_data = {**non_financial_fields, **financial_fields}
    
    # Filter the data
    filtered_data = filter_service.filter_response(mixed_data)
    
    # Only non-financial fields should remain
    for key in filtered_data:
        assert key in non_financial_fields
        assert key not in financial_fields
    
    # All non-financial fields should be preserved
    for key in non_financial_fields:
        assert key in filtered_data
        assert filtered_data[key] == non_financial_fields[key]
    
    # Validation should pass on filtered data
    assert filter_service.validate_no_financial_data(filtered_data) == True


@given(
    nested_data=st.fixed_dictionaries({
        'employee': st.fixed_dictionaries({
            'name': st.text(min_size=1, max_size=50),
            'skills': st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5)
        }),
        'financial': st.fixed_dictionaries({
            'billing_rate': st.floats(min_value=0, max_value=1000),
            'revenue': st.floats(min_value=0, max_value=100000)
        })
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_nested_financial_data_is_removed(nested_data):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any nested data structure containing financial fields at any level,
    the filter should remove all financial fields recursively.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Filter the data
    filtered_data = filter_service.filter_response(nested_data)
    
    # Financial section should be removed
    assert 'financial' not in filtered_data
    
    # Employee section should be preserved
    assert 'employee' in filtered_data
    assert 'name' in filtered_data['employee']
    assert 'skills' in filtered_data['employee']
    
    # Validation should pass on filtered data
    assert filter_service.validate_no_financial_data(filtered_data) == True


@given(
    records=st.lists(
        st.fixed_dictionaries({
            'employee_id': st.text(min_size=1, max_size=20),
            'name': st.text(min_size=1, max_size=50),
            'billing_rate': st.floats(min_value=0, max_value=1000),
            'revenue': st.floats(min_value=0, max_value=100000)
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_export_sanitization(records):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any list of records being exported, the sanitize_for_export method
    should remove all financial fields from every record.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Sanitize for export
    sanitized = filter_service.sanitize_for_export(records)
    
    # Same number of records
    assert len(sanitized) == len(records)
    
    # Each record should have no financial fields
    for record in sanitized:
        assert 'billing_rate' not in record
        assert 'revenue' not in record
        assert 'employee_id' in record
        assert 'name' in record
        
        # Validation should pass
        assert filter_service.validate_no_financial_data(record) == True


@given(field_name=financial_field_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_schema_validation_rejects_financial_fields(field_name):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any financial field name, the schema validation should reject it.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Financial fields should be rejected
    assert filter_service.validate_schema_field(field_name) == False


@given(field_name=non_financial_field_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_schema_validation_accepts_non_financial_fields(field_name):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any non-financial field name, the schema validation should accept it.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Non-financial fields should be accepted
    assert filter_service.validate_schema_field(field_name) == True


@given(
    data=st.fixed_dictionaries({
        'employee_id': st.text(min_size=1, max_size=20),
        'billing_rate': st.floats(min_value=0, max_value=1000),
        'nested': st.fixed_dictionaries({
            'revenue': st.floats(min_value=0, max_value=100000),
            'skill': st.text(min_size=1, max_size=20)
        })
    })
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_financial_fields_in_data(data):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any data with financial fields, get_financial_fields_in_data should
    correctly identify all financial field paths.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Get financial fields
    financial_fields = filter_service.get_financial_fields_in_data(data)
    
    # Should find billing_rate and nested.revenue
    assert 'billing_rate' in financial_fields
    assert 'nested.revenue' in financial_fields
    
    # Should not include non-financial fields
    assert 'employee_id' not in financial_fields
    assert 'nested.skill' not in financial_fields


@given(
    data=st.one_of(
        st.none(),
        st.lists(st.none(), min_size=0, max_size=5),
        st.dictionaries(
            keys=non_financial_field_strategy,
            values=st.none(),
            min_size=0,
            max_size=5
        )
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filter_handles_empty_and_null_data(data):
    """
    **Feature: skill-board-views, Property 4: Financial Data Exclusion**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 4.3, 4.5**
    
    For any empty or null data, the filter should handle it gracefully
    without errors.
    """
    filter_service = FinancialDataFilter(strict_mode=False)
    
    # Should not raise any exceptions
    filtered = filter_service.filter_response(data)
    
    # Validation should pass
    assert filter_service.validate_no_financial_data(filtered) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
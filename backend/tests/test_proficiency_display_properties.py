"""Property-based tests for Proficiency Display Service.

**Feature: skill-board-views, Property 7: Proficiency Display Consistency**
**Validates: Requirements 1.2**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.proficiency_display import ProficiencyDisplayService, ProficiencyDisplay


# Hypothesis strategies
valid_proficiency_strategy = st.sampled_from([
    "Beginner", "Developing", "Intermediate", "Advanced", "Expert"
])

alias_strategy = st.sampled_from([
    "beginner", "developing", "intermediate", "advanced", "expert",
    "1", "2", "3", "4", "5",
    "basic", "novice", "junior", "mid", "senior", "lead", "master"
])


@given(rating=valid_proficiency_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_proficiency_returns_correct_display(rating):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any valid proficiency rating, the display mapping should return
    the correct visual indicator with all required fields.
    """
    service = ProficiencyDisplayService()
    
    display = service.get_proficiency_display(rating)
    
    # Should return a ProficiencyDisplay object
    assert isinstance(display, ProficiencyDisplay)
    
    # Level should match the input
    assert display.level == rating
    
    # All required fields should be present and valid
    assert display.color.startswith("#")
    assert len(display.color) == 7  # Hex color format
    assert display.icon is not None
    assert 1 <= display.numeric_value <= 5
    assert display.description is not None
    assert display.css_class is not None


@given(alias=alias_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_aliases_map_to_valid_proficiency(alias):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any proficiency alias, the display mapping should return a valid
    proficiency display.
    """
    service = ProficiencyDisplayService()
    
    display = service.get_proficiency_display(alias)
    
    # Should return a valid ProficiencyDisplay
    assert isinstance(display, ProficiencyDisplay)
    assert display.level in ["Beginner", "Developing", "Intermediate", "Advanced", "Expert"]
    assert 1 <= display.numeric_value <= 5


@given(rating=valid_proficiency_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_numeric_value_ordering(rating):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any proficiency rating, the numeric value should correctly reflect
    the ordering (Beginner=1 through Expert=5).
    """
    service = ProficiencyDisplayService()
    
    expected_values = {
        "Beginner": 1,
        "Developing": 2,
        "Intermediate": 3,
        "Advanced": 4,
        "Expert": 5
    }
    
    numeric_value = service.get_numeric_value(rating)
    
    assert numeric_value == expected_values[rating]


@given(
    rating1=valid_proficiency_strategy,
    rating2=valid_proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_comparison_consistency(rating1, rating2):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any two proficiency ratings, the comparison should be consistent
    with their numeric values.
    """
    service = ProficiencyDisplayService()
    
    val1 = service.get_numeric_value(rating1)
    val2 = service.get_numeric_value(rating2)
    comparison = service.compare_proficiency(rating1, rating2)
    
    if val1 < val2:
        assert comparison == -1
    elif val1 > val2:
        assert comparison == 1
    else:
        assert comparison == 0


@given(
    actual=valid_proficiency_strategy,
    required=valid_proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_meets_requirement_consistency(actual, required):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any actual and required proficiency, meets_requirement should be
    consistent with numeric comparison.
    """
    service = ProficiencyDisplayService()
    
    actual_val = service.get_numeric_value(actual)
    required_val = service.get_numeric_value(required)
    meets = service.meets_requirement(actual, required)
    
    assert meets == (actual_val >= required_val)


@given(
    actual=valid_proficiency_strategy,
    required=valid_proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_gap_calculation_accuracy(actual, required):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any actual and required proficiency, the gap calculation should
    be mathematically correct.
    """
    service = ProficiencyDisplayService()
    
    actual_val = service.get_numeric_value(actual)
    required_val = service.get_numeric_value(required)
    gap = service.calculate_gap(actual, required)
    
    # Gap should be required - actual
    assert gap == required_val - actual_val
    
    # Positive gap means below requirement
    if gap > 0:
        assert actual_val < required_val
    # Zero gap means meets requirement
    elif gap == 0:
        assert actual_val == required_val
    # Negative gap means exceeds requirement
    else:
        assert actual_val > required_val


@given(rating=valid_proficiency_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_color_uniqueness(rating):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any proficiency rating, the color should be unique to that level.
    """
    service = ProficiencyDisplayService()
    
    display = service.get_proficiency_display(rating)
    
    # Get all other colors
    other_colors = [
        service.get_proficiency_display(level).color
        for level in service.get_all_levels()
        if level != rating
    ]
    
    # This rating's color should not be in other colors
    assert display.color not in other_colors


@given(invalid_rating=st.text(min_size=0, max_size=50).filter(
    lambda x: x.lower().strip() not in [
        "beginner", "developing", "intermediate", "advanced", "expert",
        "1", "2", "3", "4", "5", "basic", "novice", "junior", "mid",
        "senior", "lead", "master"
    ]
))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_rating_defaults_to_beginner(invalid_rating):
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    For any invalid proficiency rating, the system should default to Beginner.
    """
    service = ProficiencyDisplayService()
    
    display = service.get_proficiency_display(invalid_rating)
    
    # Should default to Beginner
    assert display.level == "Beginner"
    assert display.numeric_value == 1


def test_all_levels_are_ordered():
    """
    **Feature: skill-board-views, Property 7: Proficiency Display Consistency**
    **Validates: Requirements 1.2**
    
    All proficiency levels should be in correct order.
    """
    service = ProficiencyDisplayService()
    
    levels = service.get_all_levels()
    
    assert levels == ["Beginner", "Developing", "Intermediate", "Advanced", "Expert"]
    
    # Verify numeric values are in order
    for i, level in enumerate(levels):
        assert service.get_numeric_value(level) == i + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Property-based tests for Capability Alignment Service.

**Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
**Validates: Requirements 1.3, 1.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.capability_alignment import (
    CapabilityAlignmentCalculator, SkillComparison, AlignmentResult
)
from app.services.proficiency_display import proficiency_service


# Hypothesis strategies
proficiency_strategy = st.sampled_from([
    "Beginner", "Developing", "Intermediate", "Advanced", "Expert"
])

skill_id_strategy = st.integers(min_value=1, max_value=100)


@given(
    employee_skills=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=1,
        max_size=10
    ),
    requirements=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_alignment_score_bounds(employee_skills, requirements):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any set of employee skills and requirements, the alignment score
    should always be between 0 and 100.
    """
    calculator = CapabilityAlignmentCalculator()
    
    comparisons = calculator.compare_skills_to_requirements(employee_skills, requirements)
    score, met, total = calculator.calculate_alignment_score(comparisons)
    
    # Score should be between 0 and 100
    assert 0 <= score <= 100
    
    # Met should not exceed total
    assert met <= total
    
    # Total should match requirements count
    assert total == len(requirements)


@given(
    skill_id=skill_id_strategy,
    actual_level=proficiency_strategy,
    required_level=proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_comparison_accuracy(skill_id, actual_level, required_level):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any skill comparison, the meets_requirement flag should correctly
    reflect whether actual >= required.
    """
    calculator = CapabilityAlignmentCalculator()
    
    employee_skills = {skill_id: actual_level}
    requirements = {skill_id: required_level}
    
    comparisons = calculator.compare_skills_to_requirements(employee_skills, requirements)
    
    assert len(comparisons) == 1
    comp = comparisons[0]
    
    actual_numeric = proficiency_service.get_numeric_value(actual_level)
    required_numeric = proficiency_service.get_numeric_value(required_level)
    
    # meets_requirement should be True if actual >= required
    expected_meets = actual_numeric >= required_numeric
    assert comp.meets_requirement == expected_meets
    
    # Gap should be required - actual
    expected_gap = required_numeric - actual_numeric
    assert comp.gap == expected_gap


@given(
    requirements=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_missing_skills_create_gaps(requirements):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any requirements where employee has no skills, all requirements
    should show as gaps.
    """
    calculator = CapabilityAlignmentCalculator()
    
    # Employee has no skills
    employee_skills = {}
    
    comparisons = calculator.compare_skills_to_requirements(employee_skills, requirements)
    gaps = calculator.identify_skill_gaps(comparisons)
    
    # All requirements should be gaps since employee has no skills
    assert len(gaps) == len(requirements)
    
    # All comparisons should not meet requirement
    for comp in comparisons:
        assert comp.meets_requirement == False
        assert comp.gap > 0


@given(
    requirements=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_expert_skills_meet_all_requirements(requirements):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any requirements, if employee has Expert level in all skills,
    all requirements should be met.
    """
    calculator = CapabilityAlignmentCalculator()
    
    # Employee has Expert in all required skills
    employee_skills = {skill_id: "Expert" for skill_id in requirements.keys()}
    
    comparisons = calculator.compare_skills_to_requirements(employee_skills, requirements)
    gaps = calculator.identify_skill_gaps(comparisons)
    
    # No gaps should exist
    assert len(gaps) == 0
    
    # All comparisons should meet requirement
    for comp in comparisons:
        assert comp.meets_requirement == True
        assert comp.gap <= 0
    
    # Alignment score should be 100%
    score, met, total = calculator.calculate_alignment_score(comparisons)
    assert score == 100.0
    assert met == total


@given(
    comparisons=st.lists(
        st.fixed_dictionaries({
            'skill_id': skill_id_strategy,
            'actual_level': st.one_of(st.none(), proficiency_strategy),
            'required_level': proficiency_strategy
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_average_proficiency_calculation(comparisons):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any set of skill comparisons, the average proficiency should be
    mathematically correct.
    """
    calculator = CapabilityAlignmentCalculator()
    
    # Build skill comparisons
    skill_comps = []
    for comp_data in comparisons:
        actual = comp_data['actual_level']
        required = comp_data['required_level']
        actual_numeric = proficiency_service.get_numeric_value(actual) if actual else 0
        required_numeric = proficiency_service.get_numeric_value(required)
        
        skill_comps.append(SkillComparison(
            skill_id=comp_data['skill_id'],
            skill_name=f"Skill_{comp_data['skill_id']}",
            category=None,
            required_level=required,
            actual_level=actual,
            required_numeric=required_numeric,
            actual_numeric=actual_numeric,
            meets_requirement=actual_numeric >= required_numeric if actual else False,
            gap=required_numeric - actual_numeric
        ))
    
    avg = calculator.calculate_average_proficiency(skill_comps)
    
    # Average should be between 0 and 5
    assert 0 <= avg <= 5
    
    # Calculate expected average
    rated = [c for c in skill_comps if c.actual_level is not None]
    if rated:
        expected = sum(c.actual_numeric for c in rated) / len(rated)
        assert abs(avg - round(expected, 2)) < 0.01


@given(
    capability=st.text(min_size=1, max_size=50),
    employee_skills=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=0,
        max_size=10
    ),
    requirements=st.dictionaries(
        keys=skill_id_strategy,
        values=proficiency_strategy,
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_alignment_result_consistency(capability, employee_skills, requirements):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any alignment result, the data should be internally consistent.
    """
    calculator = CapabilityAlignmentCalculator()
    
    result = calculator.get_alignment_result(capability, employee_skills, requirements)
    
    # Result should have correct capability
    assert result.capability == capability
    
    # Score should match met/total ratio
    if result.required_skills_total > 0:
        expected_score = result.required_skills_met / result.required_skills_total * 100
        assert abs(result.alignment_score - round(expected_score, 2)) < 0.01
    
    # Gaps should only contain skills with positive gap
    for gap in result.gaps:
        assert gap.gap > 0
        assert gap.meets_requirement == False
    
    # Number of gaps + met should equal total comparisons
    met_count = sum(1 for c in result.skill_comparisons if c.meets_requirement)
    assert met_count == result.required_skills_met


@given(
    skill_id=skill_id_strategy,
    required_level=proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_gap_identification_for_missing_skill(skill_id, required_level):
    """
    **Feature: skill-board-views, Property 2: Capability Alignment Accuracy**
    **Validates: Requirements 1.3, 1.4**
    
    For any required skill that employee doesn't have, it should be
    identified as a gap.
    """
    calculator = CapabilityAlignmentCalculator()
    
    employee_skills = {}  # No skills
    requirements = {skill_id: required_level}
    
    comparisons = calculator.compare_skills_to_requirements(employee_skills, requirements)
    gaps = calculator.identify_skill_gaps(comparisons)
    
    # Should have exactly one gap
    assert len(gaps) == 1
    assert gaps[0].skill_id == skill_id
    assert gaps[0].actual_level is None
    assert gaps[0].gap == proficiency_service.get_numeric_value(required_level)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

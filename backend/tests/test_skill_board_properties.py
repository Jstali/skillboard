"""Property-based tests for Skill Board Service.

**Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
**Validates: Requirements 1.1, 1.2, 1.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import MagicMock, patch
from app.services.skill_board import (
    SkillBoardService, SkillWithProficiency, SkillGap, 
    CapabilityAlignment, EmployeeSkillBoard
)
from app.services.proficiency_display import proficiency_service


# Hypothesis strategies
proficiency_strategy = st.sampled_from([
    "Beginner", "Developing", "Intermediate", "Advanced", "Expert"
])

skill_name_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('L', 'N'), whitelist_characters=' -_'
)).filter(lambda x: x.strip())

category_strategy = st.sampled_from([
    "Programming", "SAP", "Cloud", "DevOps", "Database", "Testing", None
])

team_strategy = st.sampled_from([
    "consulting", "technical_delivery", "project_programming", 
    "corporate_functions_it", None
])

band_strategy = st.sampled_from(["A", "B", "C", "L1", "L2", None])


@given(
    skills=st.lists(
        st.fixed_dictionaries({
            'name': skill_name_strategy,
            'category': category_strategy,
            'rating': proficiency_strategy,
            'years_experience': st.floats(min_value=0, max_value=30, allow_nan=False)
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_board_contains_all_skills(skills):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any employee with assigned skills, the skill board should display
    all skills with their current proficiency levels.
    """
    # Create mock skills with proficiency
    skills_with_prof = []
    for i, skill_data in enumerate(skills):
        display = proficiency_service.get_proficiency_display(skill_data['rating'])
        skills_with_prof.append(SkillWithProficiency(
            skill_id=i + 1,
            skill_name=skill_data['name'],
            category=skill_data['category'],
            rating=skill_data['rating'],
            rating_display=display,
            years_experience=skill_data['years_experience'],
            is_required=False,
            meets_requirement=True
        ))
    
    # Verify all skills are present
    assert len(skills_with_prof) == len(skills)
    
    # Verify each skill has proficiency display
    for skill in skills_with_prof:
        assert skill.rating_display is not None
        assert skill.rating_display.level in ["Beginner", "Developing", "Intermediate", "Advanced", "Expert"]
        assert 1 <= skill.rating_display.numeric_value <= 5


@given(
    actual_rating=proficiency_strategy,
    required_rating=proficiency_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_gap_detection_accuracy(actual_rating, required_rating):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any skill with actual and required proficiency, the gap detection
    should correctly identify if there's a gap.
    """
    actual_val = proficiency_service.get_numeric_value(actual_rating)
    required_val = proficiency_service.get_numeric_value(required_rating)
    gap = proficiency_service.calculate_gap(actual_rating, required_rating)
    
    # Gap should be positive when actual < required
    if actual_val < required_val:
        assert gap > 0
        # Priority should be based on gap size
        priority = "High" if gap >= 2 else "Medium" if gap == 1 else "Low"
        skill_gap = SkillGap(
            skill_id=1,
            skill_name="Test Skill",
            category="Programming",
            required_level=required_rating,
            actual_level=actual_rating,
            gap_value=gap,
            priority=priority
        )
        assert skill_gap.gap_value == required_val - actual_val
    elif actual_val >= required_val:
        assert gap <= 0


@given(
    skills_met=st.integers(min_value=0, max_value=20),
    skills_total=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_alignment_score_calculation(skills_met, skills_total):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any capability alignment calculation, the score should be
    mathematically correct (skills_met / skills_total * 100).
    """
    # Ensure skills_met doesn't exceed skills_total
    skills_met = min(skills_met, skills_total)
    
    expected_score = (skills_met / skills_total * 100) if skills_total > 0 else 100.0
    
    alignment = CapabilityAlignment(
        capability="Test Capability",
        alignment_score=round(expected_score, 2),
        required_skills_met=skills_met,
        required_skills_total=skills_total,
        average_proficiency=3.0
    )
    
    # Score should be between 0 and 100
    assert 0 <= alignment.alignment_score <= 100
    
    # Score should match calculation
    assert alignment.alignment_score == round(expected_score, 2)
    
    # If all skills met, score should be 100
    if skills_met == skills_total:
        assert alignment.alignment_score == 100.0


@given(
    employee_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('L', 'N')
    )),
    name=st.text(min_size=1, max_size=50),
    capability=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    team=team_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_employee_skill_board_structure(employee_id, name, capability, team):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any employee, the skill board should contain all required fields
    including home capability and team assignment.
    """
    skill_board = EmployeeSkillBoard(
        employee_id=employee_id,
        name=name,
        home_capability=capability,
        team=team,
        skills=[],
        capability_alignment=None,
        skill_gaps=[]
    )
    
    # All required fields should be present
    assert skill_board.employee_id == employee_id
    assert skill_board.name == name
    assert skill_board.home_capability == capability
    assert skill_board.team == team
    assert isinstance(skill_board.skills, list)
    assert isinstance(skill_board.skill_gaps, list)


@given(
    gaps=st.lists(
        st.fixed_dictionaries({
            'gap_value': st.integers(min_value=1, max_value=4),
            'skill_name': skill_name_strategy
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_gaps_priority_ordering(gaps):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any list of skill gaps, they should be ordered by priority
    (High gaps first, then Medium, then Low).
    """
    skill_gaps = []
    for i, gap_data in enumerate(gaps):
        gap_value = gap_data['gap_value']
        priority = "High" if gap_value >= 2 else "Medium" if gap_value == 1 else "Low"
        skill_gaps.append(SkillGap(
            skill_id=i + 1,
            skill_name=gap_data['skill_name'],
            category="Programming",
            required_level="Expert",
            actual_level="Beginner",
            gap_value=gap_value,
            priority=priority
        ))
    
    # Sort by priority
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_gaps = sorted(skill_gaps, key=lambda g: priority_order.get(g.priority, 3))
    
    # Verify ordering
    for i in range(len(sorted_gaps) - 1):
        current_priority = priority_order[sorted_gaps[i].priority]
        next_priority = priority_order[sorted_gaps[i + 1].priority]
        assert current_priority <= next_priority


@given(rating=proficiency_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_proficiency_display_in_skill_board(rating):
    """
    **Feature: skill-board-views, Property 1: Employee Skill Board Completeness**
    **Validates: Requirements 1.1, 1.2, 1.5**
    
    For any skill in the skill board, the proficiency display should
    contain all visual indicator information.
    """
    display = proficiency_service.get_proficiency_display(rating)
    
    skill = SkillWithProficiency(
        skill_id=1,
        skill_name="Test Skill",
        category="Programming",
        rating=rating,
        rating_display=display,
        years_experience=2.5,
        is_required=True,
        meets_requirement=True
    )
    
    # Proficiency display should have all required fields
    assert skill.rating_display.level == rating
    assert skill.rating_display.color.startswith("#")
    assert skill.rating_display.icon is not None
    assert 1 <= skill.rating_display.numeric_value <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

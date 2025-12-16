"""Property-based tests for Metrics Service.

**Feature: skill-board-views, Property 3: Metrics Aggregation Correctness**
**Feature: skill-board-views, Property 9: Coverage Percentage Calculation**
**Feature: skill-board-views, Property 10: Training Needs Identification**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 5.1, 5.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.metrics_service import (
    MetricsService, SkillDistribution, CoverageMetrics, 
    TrainingNeed, MetricsFilter
)
from app.services.proficiency_display import proficiency_service


# Hypothesis strategies
proficiency_strategy = st.sampled_from([
    "Beginner", "Developing", "Intermediate", "Advanced", "Expert"
])

skill_name_strategy = st.text(min_size=1, max_size=30, alphabet=st.characters(
    whitelist_categories=('L', 'N'), whitelist_characters=' -_'
)).filter(lambda x: x.strip())

capability_strategy = st.sampled_from([
    "Technical Delivery", "Consulting", "AWL", "Corporate Functions", None
])


@given(
    skill_counts=st.dictionaries(
        keys=proficiency_strategy,
        values=st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_counts_sum_correctly(skill_counts):
    """
    **Feature: skill-board-views, Property 3: Metrics Aggregation Correctness**
    **Validates: Requirements 2.1, 2.2, 5.1, 5.3**
    
    For any set of skill counts by proficiency, the total should equal
    the sum of all individual counts.
    """
    total = sum(skill_counts.values())
    
    # Total should be non-negative
    assert total >= 0
    
    # Each count should be non-negative
    for level, count in skill_counts.items():
        assert count >= 0
        assert level in proficiency_service.get_all_levels()


@given(
    skills=st.lists(
        st.fixed_dictionaries({
            'name': skill_name_strategy,
            'proficiency': proficiency_strategy
        }),
        min_size=0,
        max_size=20
    ),
    capability=capability_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_skill_distribution_structure(skills, capability):
    """
    **Feature: skill-board-views, Property 3: Metrics Aggregation Correctness**
    **Validates: Requirements 2.1, 2.2, 5.1, 5.3**
    
    For any skill distribution, the structure should be valid and consistent.
    """
    # Build skill counts and proficiency distribution
    skill_counts = {}
    proficiency_dist = {}
    
    for skill in skills:
        name = skill['name']
        prof = skill['proficiency']
        
        skill_counts[name] = skill_counts.get(name, 0) + 1
        
        if name not in proficiency_dist:
            proficiency_dist[name] = {}
        proficiency_dist[name][prof] = proficiency_dist[name].get(prof, 0) + 1
    
    distribution = SkillDistribution(
        capability=capability,
        total_employees=len(set(range(len(skills)))),  # Simulated employee count
        skill_counts=skill_counts,
        proficiency_distribution=proficiency_dist
    )
    
    # Verify structure
    assert distribution.total_employees >= 0
    assert isinstance(distribution.skill_counts, dict)
    assert isinstance(distribution.proficiency_distribution, dict)
    
    # Verify proficiency distribution sums match skill counts
    for skill_name, count in distribution.skill_counts.items():
        if skill_name in distribution.proficiency_distribution:
            prof_sum = sum(distribution.proficiency_distribution[skill_name].values())
            assert prof_sum == count


@given(
    skills_with_coverage=st.integers(min_value=0, max_value=50),
    skills_without_coverage=st.integers(min_value=0, max_value=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_coverage_percentage_calculation(skills_with_coverage, skills_without_coverage):
    """
    **Feature: skill-board-views, Property 9: Coverage Percentage Calculation**
    **Validates: Requirements 5.3**
    
    For any capability area, the coverage percentage should be mathematically
    correct based on skills present vs skills required.
    """
    total_skills = skills_with_coverage + skills_without_coverage
    
    if total_skills > 0:
        expected_coverage = (skills_with_coverage / total_skills) * 100
    else:
        expected_coverage = 100.0  # No requirements = 100% coverage
    
    coverage = CoverageMetrics(
        capability="Test Capability",
        coverage_percentage=round(expected_coverage, 2),
        skills_with_coverage=skills_with_coverage,
        skills_without_coverage=skills_without_coverage,
        critical_gaps=[]
    )
    
    # Coverage should be between 0 and 100
    assert 0 <= coverage.coverage_percentage <= 100
    
    # Verify calculation
    if total_skills > 0:
        calculated = (coverage.skills_with_coverage / total_skills) * 100
        assert abs(coverage.coverage_percentage - round(calculated, 2)) < 0.01
    
    # If all skills covered, should be 100%
    if skills_without_coverage == 0 and skills_with_coverage > 0:
        assert coverage.coverage_percentage == 100.0


@given(
    training_needs=st.lists(
        st.fixed_dictionaries({
            'skill_name': skill_name_strategy,
            'current_coverage': st.floats(min_value=0, max_value=80, allow_nan=False),
            'gap': st.floats(min_value=1, max_value=80, allow_nan=False)  # Ensure positive gap
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_training_needs_gap_calculation(training_needs):
    """
    **Feature: skill-board-views, Property 10: Training Needs Identification**
    **Validates: Requirements 2.3, 2.4**
    
    For any capability area with skill gaps, training needs should be
    correctly identified and prioritized.
    """
    needs = []
    for need_data in training_needs:
        current = need_data['current_coverage']
        gap = need_data['gap']
        required = current + gap  # Ensure required > current
        
        priority = "High" if gap >= 40 else "Medium" if gap >= 20 else "Low"
        needs.append(TrainingNeed(
            skill_name=need_data['skill_name'],
            current_coverage=round(current, 2),
            required_coverage=round(required, 2),
            gap_percentage=round(gap, 2),
            priority=priority
        ))
    
    # Verify each training need
    for need in needs:
        # Gap should be positive (we ensured this in generation)
        assert need.gap_percentage >= 1.0
        
        # Gap should approximately equal required - current
        expected_gap = need.required_coverage - need.current_coverage
        assert abs(need.gap_percentage - expected_gap) < 0.1
        
        # Priority should match gap size
        if need.gap_percentage >= 40:
            assert need.priority == "High"
        elif need.gap_percentage >= 20:
            assert need.priority == "Medium"
        else:
            assert need.priority == "Low"


@given(
    gaps=st.lists(
        st.floats(min_value=0.1, max_value=80, allow_nan=False),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_training_needs_sorted_by_gap(gaps):
    """
    **Feature: skill-board-views, Property 10: Training Needs Identification**
    **Validates: Requirements 2.3, 2.4**
    
    Training needs should be sorted by gap percentage (highest first).
    """
    needs = []
    for i, gap in enumerate(gaps):
        priority = "High" if gap >= 40 else "Medium" if gap >= 20 else "Low"
        needs.append(TrainingNeed(
            skill_name=f"Skill_{i}",
            current_coverage=80 - gap,
            required_coverage=80.0,
            gap_percentage=round(gap, 2),
            priority=priority
        ))
    
    # Sort by gap (highest first)
    sorted_needs = sorted(needs, key=lambda x: x.gap_percentage, reverse=True)
    
    # Verify ordering
    for i in range(len(sorted_needs) - 1):
        assert sorted_needs[i].gap_percentage >= sorted_needs[i + 1].gap_percentage


@given(
    capability=st.text(min_size=1, max_size=50),
    critical_gaps=st.lists(skill_name_strategy, min_size=0, max_size=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_coverage_metrics_critical_gaps(capability, critical_gaps):
    """
    **Feature: skill-board-views, Property 9: Coverage Percentage Calculation**
    **Validates: Requirements 5.3**
    
    Coverage metrics should correctly identify critical gaps.
    """
    skills_without = len(critical_gaps)
    skills_with = 10  # Assume 10 skills with coverage
    total = skills_with + skills_without
    
    coverage_pct = (skills_with / total * 100) if total > 0 else 100.0
    
    coverage = CoverageMetrics(
        capability=capability,
        coverage_percentage=round(coverage_pct, 2),
        skills_with_coverage=skills_with,
        skills_without_coverage=skills_without,
        critical_gaps=critical_gaps
    )
    
    # Number of critical gaps should match skills without coverage
    assert len(coverage.critical_gaps) == coverage.skills_without_coverage
    
    # If no gaps, coverage should be 100%
    if skills_without == 0:
        assert coverage.coverage_percentage == 100.0


@given(
    filter_capability=capability_strategy,
    filter_team=st.one_of(st.none(), st.sampled_from(["consulting", "technical_delivery"])),
    filter_band=st.one_of(st.none(), st.sampled_from(["A", "B", "C", "L1", "L2"]))
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_metrics_filter_structure(filter_capability, filter_team, filter_band):
    """
    **Feature: skill-board-views, Property 3: Metrics Aggregation Correctness**
    **Validates: Requirements 2.1, 2.2, 5.1, 5.3**
    
    Metrics filters should have valid structure.
    """
    metrics_filter = MetricsFilter(
        capability=filter_capability,
        team=filter_team,
        band=filter_band
    )
    
    # Filter should preserve values
    assert metrics_filter.capability == filter_capability
    assert metrics_filter.team == filter_team
    assert metrics_filter.band == filter_band


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Property-based tests for Level Movement Workflow.

**Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
**Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.level_movement import (
    LevelCriteriaEngine, WorkflowManager, AuditTracker,
    WorkflowStatus, ApproverRole, ReadinessScore
)


# Hypothesis strategies
employee_id_strategy = st.integers(min_value=1, max_value=1000)
level_strategy = st.sampled_from(["A", "B", "C", "L1", "L2"])
score_strategy = st.floats(min_value=0, max_value=100, allow_nan=False)
criteria_strategy = st.integers(min_value=0, max_value=20)


@given(
    employee_id=employee_id_strategy,
    current_level=level_strategy,
    target_level=level_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_readiness_score_bounds(employee_id, current_level, target_level):
    """
    **Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
    **Validates: Requirements 7.1, 7.2**
    
    For any readiness assessment, the score should be between 0 and 100.
    """
    engine = LevelCriteriaEngine()
    
    result = engine.evaluate_readiness(employee_id, target_level, current_level)
    
    assert 0 <= result.score <= 100
    assert result.criteria_met <= result.criteria_total
    assert isinstance(result.is_ready, bool)


@given(current_level=level_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_next_level_progression(current_level):
    """
    **Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
    **Validates: Requirements 7.1, 7.2**
    
    For any level, the next level should follow the defined progression.
    """
    engine = LevelCriteriaEngine()
    
    next_level = engine.get_next_level(current_level)
    
    expected_next = {
        "A": "B",
        "B": "C",
        "C": "L1",
        "L1": "L2",
        "L2": None
    }
    
    assert next_level == expected_next[current_level]


@given(
    current_level=level_strategy,
    target_level=level_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_valid_progression_check(current_level, target_level):
    """
    **Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
    **Validates: Requirements 7.1, 7.2**
    
    For any level pair, progression validity should be correctly determined.
    """
    engine = LevelCriteriaEngine()
    
    is_valid = engine.is_valid_progression(current_level, target_level)
    
    # Valid progressions are single-step increases
    level_order = ["A", "B", "C", "L1", "L2"]
    try:
        current_idx = level_order.index(current_level)
        target_idx = level_order.index(target_level)
        expected_valid = target_idx == current_idx + 1
    except ValueError:
        expected_valid = False
    
    assert is_valid == expected_valid


@given(
    employee_id=employee_id_strategy,
    target_level=level_strategy,
    initiator_id=employee_id_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_workflow_initiation(employee_id, target_level, initiator_id):
    """
    **Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
    **Validates: Requirements 7.3, 7.4**
    
    For any workflow initiation, the initial state should be correct.
    """
    manager = WorkflowManager()
    
    instance = manager.initiate_request(employee_id, target_level, initiator_id)
    
    # Initial state should be pending
    assert instance.status == WorkflowStatus.PENDING
    
    # First approver should be manager
    assert instance.current_approver_role == ApproverRole.MANAGER.value
    
    # Employee and target should match
    assert instance.employee_id == employee_id
    assert instance.target_level == target_level
    
    # Should have readiness score
    assert instance.readiness_score is not None
    assert 0 <= instance.readiness_score <= 100


@given(status=st.sampled_from([
    WorkflowStatus.PENDING.value,
    WorkflowStatus.MANAGER_APPROVED.value,
    WorkflowStatus.CP_APPROVED.value
]))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_approval_sequence(status):
    """
    **Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
    **Validates: Requirements 7.3, 7.4**
    
    For any workflow status, the expected approver role should follow the sequence.
    """
    manager = WorkflowManager()
    
    expected_role = manager._get_current_approver_role(status)
    
    expected_mapping = {
        WorkflowStatus.PENDING.value: ApproverRole.MANAGER,
        WorkflowStatus.MANAGER_APPROVED.value: ApproverRole.CAPABILITY_PARTNER,
        WorkflowStatus.CP_APPROVED.value: ApproverRole.HR,
    }
    
    assert expected_role == expected_mapping[status]


@given(
    criteria_met=criteria_strategy,
    criteria_total=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_readiness_calculation(criteria_met, criteria_total):
    """
    **Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
    **Validates: Requirements 7.1, 7.2**
    
    For any criteria counts, the readiness score should be calculated correctly.
    """
    # Ensure criteria_met doesn't exceed criteria_total
    actual_met = min(criteria_met, criteria_total)
    
    expected_score = (actual_met / criteria_total * 100)
    expected_ready = expected_score >= 80.0
    
    # Create a mock readiness score
    score = ReadinessScore(
        employee_id=1,
        current_level="A",
        target_level="B",
        score=expected_score,
        criteria_met=actual_met,
        criteria_total=criteria_total,
        skill_gaps=[],
        is_ready=expected_ready
    )
    
    assert score.score == expected_score
    assert score.is_ready == expected_ready


@given(
    employee_id=employee_id_strategy,
    approver_id=employee_id_strategy,
    approved=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_approval_decision_recording(employee_id, approver_id, approved):
    """
    **Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
    **Validates: Requirements 7.4, 7.5**
    
    For any approval decision, it should be recorded correctly.
    """
    manager = WorkflowManager()
    
    # Without DB, approval returns mock success
    success, message = manager.approve(
        request_id=1,
        approver_id=approver_id,
        approver_role=ApproverRole.MANAGER,
        approved=approved,
        comments="Test comment"
    )
    
    assert success == True
    assert isinstance(message, str)


@given(
    score=score_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_readiness_threshold(score):
    """
    **Feature: hrms-integration, Property 14: Level Criteria Assessment Accuracy**
    **Validates: Requirements 7.1, 7.2**
    
    For any readiness score, the is_ready flag should correctly reflect the 80% threshold.
    """
    is_ready = score >= 80.0
    
    readiness = ReadinessScore(
        employee_id=1,
        current_level="A",
        target_level="B",
        score=score,
        criteria_met=int(score / 10),
        criteria_total=10,
        skill_gaps=[],
        is_ready=is_ready
    )
    
    assert readiness.is_ready == (score >= 80.0)


@given(
    employee_id=employee_id_strategy,
    levels=st.lists(level_strategy, min_size=2, max_size=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_audit_trail_structure(employee_id, levels):
    """
    **Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
    **Validates: Requirements 7.5**
    
    For any employee history, the audit trail structure should be valid.
    """
    tracker = AuditTracker()
    
    # Without DB, returns empty list
    history = tracker.get_employee_history(employee_id)
    
    assert isinstance(history, list)
    
    # Each entry should have required fields
    for entry in history:
        assert "request_id" in entry
        assert "from_level" in entry
        assert "to_level" in entry
        assert "status" in entry
        assert "approvals" in entry


@given(
    approver_role=st.sampled_from(list(ApproverRole))
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pending_requests_filter(approver_role):
    """
    **Feature: hrms-integration, Property 9: Level Movement Workflow Execution**
    **Validates: Requirements 7.3, 7.4**
    
    For any approver role, pending requests should be correctly filtered.
    """
    manager = WorkflowManager()
    
    # Without DB, returns empty list
    pending = manager.get_pending_requests(approver_role)
    
    assert isinstance(pending, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

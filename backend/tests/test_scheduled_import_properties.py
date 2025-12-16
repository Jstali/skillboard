"""Property-based tests for Scheduled Import Service.

**Feature: hrms-integration, Property 13: Scheduled Import Execution**
**Validates: Requirements 1.3, 1.5**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from app.services.scheduled_import import (
    ImportScheduler, ImportExecutor, ImportMonitor, RetryPolicy,
    ImportJob, ScheduleConfig, ImportStatus, ScheduleInterval
)


# Hypothesis strategies
import_type_strategy = st.sampled_from(["employees", "projects", "assignments", "attendance"])
interval_strategy = st.sampled_from(list(ScheduleInterval))
retry_count_strategy = st.integers(min_value=0, max_value=10)
delay_strategy = st.floats(min_value=0.1, max_value=10.0, allow_nan=False)


@given(
    import_type=import_type_strategy,
    interval=interval_strategy,
    enabled=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_schedule_creation(import_type, interval, enabled):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any schedule configuration, it should be created with correct properties.
    """
    scheduler = ImportScheduler()
    
    config = ScheduleConfig(
        import_type=import_type,
        interval=interval,
        enabled=enabled
    )
    
    result = scheduler.add_schedule(config)
    
    assert result == True
    
    retrieved = scheduler.get_schedule(import_type)
    assert retrieved is not None
    assert retrieved.import_type == import_type
    assert retrieved.interval == interval
    assert retrieved.enabled == enabled
    assert retrieved.next_run is not None


@given(
    import_type=import_type_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_job_creation(import_type):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any import type, a job should be created with correct initial state.
    """
    scheduler = ImportScheduler()
    
    job = scheduler.create_job(import_type)
    
    assert job.id is not None
    assert job.import_type == import_type
    assert job.status == ImportStatus.PENDING
    assert job.retry_count == 0
    assert job.scheduled_at is not None


@given(
    attempt=retry_count_strategy,
    max_retries=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_retry_policy_should_retry(attempt, max_retries):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.5**
    
    For any attempt count, retry policy should correctly determine if retry is allowed.
    """
    policy = RetryPolicy(max_retries=max_retries)
    
    should_retry = policy.should_retry(attempt)
    
    expected = attempt < max_retries
    assert should_retry == expected


@given(
    attempt=retry_count_strategy,
    base_delay=delay_strategy,
    max_delay=st.floats(min_value=10.0, max_value=120.0, allow_nan=False)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_retry_delay_bounds(attempt, base_delay, max_delay):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.5**
    
    For any retry attempt, the delay should be within bounds.
    """
    policy = RetryPolicy(base_delay=base_delay, max_delay=max_delay)
    
    delay = policy.get_delay(attempt)
    
    assert delay >= 0
    assert delay <= max_delay


@given(
    attempt=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_exponential_backoff(attempt):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.5**
    
    For any retry attempt, the delay should follow exponential backoff.
    """
    base_delay = 1.0
    exponential_base = 2.0
    max_delay = 60.0
    
    policy = RetryPolicy(
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base
    )
    
    delay = policy.get_delay(attempt)
    
    expected = min(base_delay * (exponential_base ** attempt), max_delay)
    assert abs(delay - expected) < 0.001


@given(interval=interval_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_next_run_calculation(interval):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any interval, the next run time should be correctly calculated.
    """
    scheduler = ImportScheduler()
    
    now = datetime.utcnow()
    next_run = scheduler._calculate_next_run(interval, now)
    
    # Next run should be in the future
    assert next_run > now
    
    # Check interval-specific expectations
    if interval == ScheduleInterval.HOURLY:
        expected = now + timedelta(hours=1)
    elif interval == ScheduleInterval.DAILY:
        expected = now + timedelta(days=1)
    elif interval == ScheduleInterval.WEEKLY:
        expected = now + timedelta(weeks=1)
    elif interval == ScheduleInterval.MONTHLY:
        expected = now + timedelta(days=30)
    
    # Allow small time difference due to execution
    assert abs((next_run - expected).total_seconds()) < 1


@given(
    import_type=import_type_strategy,
    status=st.sampled_from(list(ImportStatus)),
    records_processed=st.integers(min_value=0, max_value=10000)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_job_status_update(import_type, status, records_processed):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any job status update, the job should reflect the new status.
    """
    scheduler = ImportScheduler()
    
    job = scheduler.create_job(import_type)
    
    result = scheduler.update_job_status(
        job.id,
        status,
        records_processed=records_processed
    )
    
    assert result == True
    
    updated_job = scheduler.get_job(job.id)
    assert updated_job.status == status
    assert updated_job.records_processed == records_processed


@given(
    num_schedules=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_get_all_schedules(num_schedules):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any number of schedules, get_all_schedules should return all of them.
    """
    scheduler = ImportScheduler()
    
    import_types = ["employees", "projects", "assignments", "attendance", "skills"][:num_schedules]
    
    for import_type in import_types:
        config = ScheduleConfig(
            import_type=import_type,
            interval=ScheduleInterval.DAILY,
            enabled=True
        )
        scheduler.add_schedule(config)
    
    all_schedules = scheduler.get_all_schedules()
    
    assert len(all_schedules) == num_schedules


@given(
    import_type=import_type_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_schedule_removal(import_type):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any schedule, removal should work correctly.
    """
    scheduler = ImportScheduler()
    
    config = ScheduleConfig(
        import_type=import_type,
        interval=ScheduleInterval.DAILY,
        enabled=True
    )
    scheduler.add_schedule(config)
    
    # Verify it exists
    assert scheduler.get_schedule(import_type) is not None
    
    # Remove it
    result = scheduler.remove_schedule(import_type)
    assert result == True
    
    # Verify it's gone
    assert scheduler.get_schedule(import_type) is None
    
    # Removing again should return False
    result = scheduler.remove_schedule(import_type)
    assert result == False


@given(
    num_jobs=st.integers(min_value=0, max_value=10),
    success_count=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_health_status_calculation(num_jobs, success_count):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any job distribution, health status should be calculated correctly.
    """
    scheduler = ImportScheduler()
    monitor = ImportMonitor(scheduler)
    
    # Create jobs with varying statuses
    actual_success = min(success_count, num_jobs)
    
    for i in range(num_jobs):
        job = scheduler.create_job("employees")
        if i < actual_success:
            scheduler.update_job_status(job.id, ImportStatus.SUCCESS)
        else:
            scheduler.update_job_status(job.id, ImportStatus.FAILED)
    
    health = monitor.get_health_status()
    
    assert health["total_jobs"] == num_jobs
    assert health["success"] == actual_success
    
    if num_jobs > 0:
        expected_rate = (actual_success / num_jobs * 100)
        assert abs(health["success_rate"] - expected_rate) < 0.01


@given(
    import_type=import_type_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_mark_schedule_executed(import_type):
    """
    **Feature: hrms-integration, Property 13: Scheduled Import Execution**
    **Validates: Requirements 1.3**
    
    For any schedule, marking as executed should update last_run and next_run.
    """
    scheduler = ImportScheduler()
    
    config = ScheduleConfig(
        import_type=import_type,
        interval=ScheduleInterval.DAILY,
        enabled=True
    )
    scheduler.add_schedule(config)
    
    # Mark as executed
    result = scheduler.mark_schedule_executed(import_type)
    assert result == True
    
    updated = scheduler.get_schedule(import_type)
    assert updated.last_run is not None
    assert updated.next_run is not None
    assert updated.next_run > updated.last_run


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

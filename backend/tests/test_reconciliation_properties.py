"""Property-based tests for Reconciliation Service.

**Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
**Validates: Requirements 4.1, 4.2, 4.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.reconciliation_service import (
    ReconciliationService, AssignmentInfo, Discrepancy, 
    ReconciliationResult, ReconciliationReport
)


# Hypothesis strategies
project_name_strategy = st.text(min_size=1, max_size=30, alphabet=st.characters(
    whitelist_categories=('L', 'N'), whitelist_characters=' -_'
)).filter(lambda x: x.strip())

allocation_strategy = st.floats(min_value=0, max_value=100, allow_nan=False)

employee_id_strategy = st.text(min_size=1, max_size=20, alphabet=st.characters(
    whitelist_categories=('L', 'N')
))


def assignment_strategy():
    return st.fixed_dictionaries({
        'project_name': project_name_strategy,
        'allocation_percentage': st.one_of(st.none(), allocation_strategy),
        'is_primary': st.booleans()
    })


@given(
    assignments=st.lists(assignment_strategy(), min_size=1, max_size=5),
    employee_id=employee_id_strategy,
    employee_name=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_identical_assignments_match(assignments, employee_id, employee_name):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any identical assignments in both systems, there should be no discrepancies.
    """
    service = ReconciliationService()
    
    # Create identical assignments for both systems
    sb_assignments = [
        AssignmentInfo(
            project_name=a['project_name'],
            allocation_percentage=a['allocation_percentage'],
            is_primary=a['is_primary'],
            start_date=None,
            end_date=None
        )
        for a in assignments
    ]
    
    hrms_assignments = [
        AssignmentInfo(
            project_name=a['project_name'],
            allocation_percentage=a['allocation_percentage'],
            is_primary=a['is_primary'],
            start_date=None,
            end_date=None
        )
        for a in assignments
    ]
    
    result = service.compare_assignments(
        sb_assignments, hrms_assignments,
        employee_id, employee_name
    )
    
    # Should have no discrepancies
    assert len(result.discrepancies) == 0
    assert result.match_status == "Match"


@given(
    sb_projects=st.lists(project_name_strategy, min_size=1, max_size=5, unique=True),
    hrms_projects=st.lists(project_name_strategy, min_size=1, max_size=5, unique=True),
    employee_id=employee_id_strategy,
    employee_name=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_missing_assignments_detected(sb_projects, hrms_projects, employee_id, employee_name):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any assignments missing in one system, discrepancies should be detected.
    """
    service = ReconciliationService()
    
    sb_assignments = [
        AssignmentInfo(
            project_name=p,
            allocation_percentage=50.0,
            is_primary=False,
            start_date=None,
            end_date=None
        )
        for p in sb_projects
    ]
    
    hrms_assignments = [
        AssignmentInfo(
            project_name=p,
            allocation_percentage=50.0,
            is_primary=False,
            start_date=None,
            end_date=None
        )
        for p in hrms_projects
    ]
    
    result = service.compare_assignments(
        sb_assignments, hrms_assignments,
        employee_id, employee_name
    )
    
    # Calculate expected discrepancies
    sb_set = set(sb_projects)
    hrms_set = set(hrms_projects)
    
    expected_missing = len(hrms_set - sb_set)  # In HRMS but not in SB
    expected_extra = len(sb_set - hrms_set)  # In SB but not in HRMS
    
    # Count actual discrepancies by type
    missing_count = sum(1 for d in result.discrepancies if d.discrepancy_type == "Missing")
    extra_count = sum(1 for d in result.discrepancies if d.discrepancy_type == "Extra")
    
    assert missing_count == expected_missing
    assert extra_count == expected_extra


@given(
    project_name=project_name_strategy,
    sb_allocation=allocation_strategy,
    hrms_allocation=allocation_strategy,
    employee_id=employee_id_strategy,
    employee_name=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allocation_mismatch_detected(project_name, sb_allocation, hrms_allocation, employee_id, employee_name):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any allocation percentage mismatch, a discrepancy should be detected.
    """
    service = ReconciliationService()
    
    sb_assignments = [
        AssignmentInfo(
            project_name=project_name,
            allocation_percentage=sb_allocation,
            is_primary=False,
            start_date=None,
            end_date=None
        )
    ]
    
    hrms_assignments = [
        AssignmentInfo(
            project_name=project_name,
            allocation_percentage=hrms_allocation,
            is_primary=False,
            start_date=None,
            end_date=None
        )
    ]
    
    result = service.compare_assignments(
        sb_assignments, hrms_assignments,
        employee_id, employee_name
    )
    
    # If allocations differ, should have mismatch discrepancy
    if sb_allocation != hrms_allocation:
        mismatch_count = sum(1 for d in result.discrepancies if d.discrepancy_type == "Allocation_Mismatch")
        assert mismatch_count == 1
    else:
        assert len(result.discrepancies) == 0


@given(
    results=st.lists(
        st.fixed_dictionaries({
            'employee_id': employee_id_strategy,
            'employee_name': st.text(min_size=1, max_size=50),
            'has_discrepancies': st.booleans()
        }),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_report_generation_accuracy(results):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any set of reconciliation results, the report should accurately
    summarize the data.
    """
    service = ReconciliationService()
    
    # Create reconciliation results
    recon_results = []
    for r in results:
        discrepancies = []
        if r['has_discrepancies']:
            discrepancies.append(Discrepancy(
                employee_id=r['employee_id'],
                employee_name=r['employee_name'],
                discrepancy_type="Missing",
                skill_board_value=None,
                hrms_value="Project X",
                field="project_assignment"
            ))
        
        recon_results.append(ReconciliationResult(
            employee_id=r['employee_id'],
            employee_name=r['employee_name'],
            skill_board_assignments=[],
            hrms_assignments=[],
            discrepancies=discrepancies,
            match_status="Mismatch" if discrepancies else "Match"
        ))
    
    report = service.generate_reconciliation_report(recon_results)
    
    # Verify report accuracy
    assert report.total_employees == len(results)
    
    expected_matched = sum(1 for r in results if not r['has_discrepancies'])
    assert report.employees_matched == expected_matched
    
    expected_with_disc = sum(1 for r in results if r['has_discrepancies'])
    assert report.employees_with_discrepancies == expected_with_disc


@given(
    sb_assignments=st.lists(assignment_strategy(), min_size=0, max_size=5),
    hrms_assignments=st.lists(assignment_strategy(), min_size=0, max_size=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_detect_discrepancies_structure(sb_assignments, hrms_assignments):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any pair of assignment lists, detect_discrepancies should return
    valid discrepancy structures.
    """
    service = ReconciliationService()
    
    sb_list = [
        AssignmentInfo(
            project_name=a['project_name'],
            allocation_percentage=a['allocation_percentage'],
            is_primary=a['is_primary'],
            start_date=None,
            end_date=None
        )
        for a in sb_assignments
    ]
    
    hrms_list = [
        AssignmentInfo(
            project_name=a['project_name'],
            allocation_percentage=a['allocation_percentage'],
            is_primary=a['is_primary'],
            start_date=None,
            end_date=None
        )
        for a in hrms_assignments
    ]
    
    discrepancies = service.detect_discrepancies(sb_list, hrms_list)
    
    # Each discrepancy should have valid structure
    for disc in discrepancies:
        assert 'type' in disc
        assert disc['type'] in ['Missing', 'Extra']
        assert 'project' in disc
        assert 'source' in disc


@given(
    results=st.lists(
        st.fixed_dictionaries({
            'employee_id': employee_id_strategy,
            'employee_name': st.text(min_size=1, max_size=50),
            'projects': st.lists(project_name_strategy, min_size=0, max_size=3)
        }),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_export_data_no_financial_fields(results):
    """
    **Feature: skill-board-views, Property 6: Reconciliation Comparison Accuracy**
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    For any exported reconciliation data, no financial fields should be present.
    """
    service = ReconciliationService()
    
    # Create reconciliation results
    recon_results = []
    for r in results:
        recon_results.append(ReconciliationResult(
            employee_id=r['employee_id'],
            employee_name=r['employee_name'],
            skill_board_assignments=[
                AssignmentInfo(
                    project_name=p,
                    allocation_percentage=50.0,
                    is_primary=False,
                    start_date=None,
                    end_date=None
                )
                for p in r['projects']
            ],
            hrms_assignments=[],
            discrepancies=[],
            match_status="Match"
        ))
    
    report = service.generate_reconciliation_report(recon_results)
    export_data = service.export_reconciliation_data(report)
    
    # Verify no financial fields in export
    financial_fields = ['billing_rate', 'revenue', 'cost', 'salary', 'budget']
    
    for record in export_data:
        for field in financial_fields:
            assert field not in record


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

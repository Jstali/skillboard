"""Property-based tests for Assessment History.

**Feature: manager-skill-assessment, Property 5: Assessment History Immutability**
**Validates: Requirements 5.1, 5.2, 5.5**

**Feature: manager-skill-assessment, Property 6: Assessment History Completeness**
**Validates: Requirements 5.2, 4.7**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import (
    Base, Employee, Skill, SkillAssessment, AssessmentHistory,
    PathwaySkill, RatingEnum, AssessmentTypeEnum, AssessorRoleEnum
)
from app.services.assessment_service import AssessmentService
from app.services.baseline_service import BaselineService
from app.core.permissions import RoleID


@contextmanager
def create_test_db():
    """Create a temporary test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def setup_manager_employee_skill(db):
    """Set up manager, employee, and skill for testing."""
    # Create manager
    manager = Employee(
        employee_id="MGR001",
        name="Test Manager",
        company_email="manager@example.com",
        band="C",
        is_active=True
    )
    db.add(manager)
    db.flush()
    
    # Create employee (direct report)
    employee = Employee(
        employee_id="EMP001",
        name="Test Employee",
        company_email="employee@example.com",
        band="B",
        pathway="Technical",
        is_active=True,
        line_manager_id=manager.id
    )
    db.add(employee)
    db.flush()
    
    # Create skill
    skill = Skill(
        name="Test Skill",
        category="Technical"
    )
    db.add(skill)
    db.flush()
    
    db.commit()
    return manager, employee, skill


# Test strategies
rating_strategy = st.sampled_from([
    RatingEnum.BEGINNER, RatingEnum.DEVELOPING, RatingEnum.INTERMEDIATE,
    RatingEnum.ADVANCED, RatingEnum.EXPERT
])


@given(level=rating_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_assessment_creates_history_record(level):
    """
    **Feature: manager-skill-assessment, Property 5: Assessment History Immutability**
    **Validates: Requirements 5.1**
    
    For any skill assessment creation, an assessment_history record should be created.
    """
    with create_test_db() as db:
        manager, employee, skill = setup_manager_employee_skill(db)
        
        service = AssessmentService(db)
        assessment, is_new = service.create_assessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=level,
            assessor_id=manager.id,
            assessor_role_id=RoleID.LINE_MANAGER,
            comments="Test assessment"
        )
        
        # Check history record was created
        history = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id,
            AssessmentHistory.skill_id == skill.id
        ).all()
        
        assert len(history) == 1
        assert history[0].new_level == level


@given(
    first_level=rating_strategy,
    second_level=rating_strategy
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_assessment_update_captures_previous_level(first_level, second_level):
    """
    **Feature: manager-skill-assessment, Property 5: Assessment History Immutability**
    **Validates: Requirements 5.2, 4.7**
    
    For any skill assessment update, the history should capture the previous level.
    """
    with create_test_db() as db:
        manager, employee, skill = setup_manager_employee_skill(db)
        
        service = AssessmentService(db)
        
        # First assessment
        service.create_assessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=first_level,
            assessor_id=manager.id,
            assessor_role_id=RoleID.LINE_MANAGER
        )
        
        # Second assessment (update)
        service.create_assessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=second_level,
            assessor_id=manager.id,
            assessor_role_id=RoleID.LINE_MANAGER
        )
        
        # Check history records
        history = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id,
            AssessmentHistory.skill_id == skill.id
        ).order_by(AssessmentHistory.assessed_at).all()
        
        assert len(history) == 2
        
        # First record should have no previous level
        assert history[0].previous_level is None
        assert history[0].new_level == first_level
        
        # Second record should have previous level
        assert history[1].previous_level == first_level
        assert history[1].new_level == second_level


@given(level=rating_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_history_record_completeness(level):
    """
    **Feature: manager-skill-assessment, Property 6: Assessment History Completeness**
    **Validates: Requirements 5.2**
    
    For any assessment_history record, it should contain all required fields.
    """
    with create_test_db() as db:
        manager, employee, skill = setup_manager_employee_skill(db)
        
        service = AssessmentService(db)
        service.create_assessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=level,
            assessor_id=manager.id,
            assessor_role_id=RoleID.LINE_MANAGER,
            comments="Test comment"
        )
        
        history = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id
        ).first()
        
        # Required fields must not be null
        assert history.employee_id is not None
        assert history.skill_id is not None
        assert history.new_level is not None
        assert history.assessor_role is not None
        assert history.assessed_at is not None
        assert history.assessment_type is not None


@given(level=rating_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_history_captures_assessor_info(level):
    """
    **Feature: manager-skill-assessment, Property 6: Assessment History Completeness**
    **Validates: Requirements 5.2, 4.7**
    
    For any manager assessment, history should capture assessor_id and assessor_role.
    """
    with create_test_db() as db:
        manager, employee, skill = setup_manager_employee_skill(db)
        
        service = AssessmentService(db)
        service.create_assessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=level,
            assessor_id=manager.id,
            assessor_role_id=RoleID.LINE_MANAGER
        )
        
        history = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id
        ).first()
        
        assert history.assessor_id == manager.id
        assert history.assessor_role == AssessorRoleEnum.LINE_MANAGER
        assert history.assessment_type == AssessmentTypeEnum.MANAGER


def test_baseline_history_has_system_assessor():
    """
    **Feature: manager-skill-assessment, Property 6: Assessment History Completeness**
    **Validates: Requirements 2.7, 5.2**
    
    For baseline assessments, history should have SYSTEM as assessor_role and None as assessor_id.
    """
    with create_test_db() as db:
        # Create employee
        employee = Employee(
            employee_id="EMP001",
            name="Test Employee",
            company_email="employee@example.com",
            band="B",
            pathway="Technical",
            is_active=True
        )
        db.add(employee)
        db.flush()
        
        # Create skill and pathway_skill
        skill = Skill(name="Test Skill", category="Technical")
        db.add(skill)
        db.flush()
        
        pathway_skill = PathwaySkill(
            pathway="Technical",
            skill_id=skill.id,
            is_core=True
        )
        db.add(pathway_skill)
        db.commit()
        
        # Assign baseline
        service = BaselineService(db)
        service.assign_baseline(employee.id, "B", "Technical")
        
        # Check history
        history = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id
        ).first()
        
        assert history.assessor_id is None
        assert history.assessor_role == AssessorRoleEnum.SYSTEM
        assert history.assessment_type == AssessmentTypeEnum.BASELINE


def test_history_ordered_by_timestamp():
    """
    **Feature: manager-skill-assessment, Property 5: Assessment History Immutability**
    **Validates: Requirements 5.3**
    
    Assessment history should be retrievable in chronological order.
    """
    with create_test_db() as db:
        manager, employee, skill = setup_manager_employee_skill(db)
        
        service = AssessmentService(db)
        
        # Create multiple assessments
        levels = [RatingEnum.BEGINNER, RatingEnum.DEVELOPING, RatingEnum.INTERMEDIATE]
        for level in levels:
            service.create_assessment(
                employee_id=employee.id,
                skill_id=skill.id,
                level=level,
                assessor_id=manager.id,
                assessor_role_id=RoleID.LINE_MANAGER
            )
        
        # Get history
        history = service.get_assessment_history(employee.id)
        
        # Should be ordered by assessed_at DESC (most recent first)
        assert len(history) == 3
        
        # Verify descending order
        for i in range(len(history) - 1):
            assert history[i].assessed_at >= history[i + 1].assessed_at


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

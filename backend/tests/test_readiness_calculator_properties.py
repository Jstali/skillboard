"""Property-based tests for Readiness Score Calculation.

**Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
**Validates: Requirements 6.1, 6.2, 6.5**

For any employee with band B and pathway P, the readiness_score for target band B' 
should equal (sum of skills meeting B' requirements / total required skills for B') * 100.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import (
    Base, Employee, Skill, SkillAssessment, RoleRequirement,
    RatingEnum, AssessmentTypeEnum, AssessorRoleEnum
)
from app.services.readiness_calculator import ReadinessCalculator, RATING_VALUES


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


def create_employee_with_assessments(db, band: str, assessments: list):
    """Create employee with specified assessments."""
    employee = Employee(
        employee_id=f"EMP{datetime.now().timestamp()}",
        name="Test Employee",
        company_email="test@example.com",
        band=band,
        pathway="Technical",
        is_active=True
    )
    db.add(employee)
    db.flush()
    
    for skill_name, level in assessments:
        skill = Skill(name=skill_name, category="Technical")
        db.add(skill)
        db.flush()
        
        assessment = SkillAssessment(
            employee_id=employee.id,
            skill_id=skill.id,
            level=level,
            assessment_type=AssessmentTypeEnum.MANAGER,
            assessor_role=AssessorRoleEnum.LINE_MANAGER,
            assessed_at=datetime.utcnow()
        )
        db.add(assessment)
    
    db.commit()
    return employee


def create_band_requirements(db, band: str, requirements: list):
    """Create role requirements for a band."""
    for skill_name, required_level in requirements:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if not skill:
            skill = Skill(name=skill_name, category="Technical")
            db.add(skill)
            db.flush()
        
        req = RoleRequirement(
            band=band,
            skill_id=skill.id,
            required_rating=required_level,
            is_required=True
        )
        db.add(req)
    
    db.commit()


# Test strategies
band_strategy = st.sampled_from(["A", "B", "C", "L1"])
rating_strategy = st.sampled_from([
    RatingEnum.BEGINNER, RatingEnum.DEVELOPING, RatingEnum.INTERMEDIATE,
    RatingEnum.ADVANCED, RatingEnum.EXPERT
])


def test_readiness_score_bounds():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1**
    
    Readiness score should always be between 0 and 100.
    """
    with create_test_db() as db:
        # Create employee with no assessments
        employee = create_employee_with_assessments(db, "B", [])
        
        # Create requirements for next band
        create_band_requirements(db, "C", [
            ("Skill1", RatingEnum.INTERMEDIATE),
            ("Skill2", RatingEnum.INTERMEDIATE)
        ])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "C")
        
        assert 0 <= result.readiness_score <= 100


def test_readiness_100_when_all_requirements_met():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1, 6.5**
    
    When all requirements are met, readiness score should be 100.
    """
    with create_test_db() as db:
        # Create employee with assessments meeting requirements
        employee = create_employee_with_assessments(db, "B", [
            ("Skill1", RatingEnum.ADVANCED),
            ("Skill2", RatingEnum.ADVANCED)
        ])
        
        # Create requirements (lower than assessments)
        create_band_requirements(db, "C", [
            ("Skill1", RatingEnum.INTERMEDIATE),
            ("Skill2", RatingEnum.INTERMEDIATE)
        ])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "C")
        
        assert result.readiness_score == 100.0
        assert result.skills_meeting_requirement == 2
        assert result.skills_below_requirement == 0


def test_readiness_0_when_no_requirements_met():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1, 6.5**
    
    When no requirements are met, readiness score should be 0.
    """
    with create_test_db() as db:
        # Create employee with low assessments
        employee = create_employee_with_assessments(db, "A", [
            ("Skill1", RatingEnum.BEGINNER),
            ("Skill2", RatingEnum.BEGINNER)
        ])
        
        # Create requirements (higher than assessments)
        create_band_requirements(db, "B", [
            ("Skill1", RatingEnum.ADVANCED),
            ("Skill2", RatingEnum.ADVANCED)
        ])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "B")
        
        assert result.readiness_score == 0.0
        assert result.skills_meeting_requirement == 0
        assert result.skills_below_requirement == 2


def test_readiness_partial_when_some_requirements_met():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1, 6.2**
    
    When some requirements are met, readiness score should be proportional.
    """
    with create_test_db() as db:
        # Create employee with mixed assessments
        employee = create_employee_with_assessments(db, "B", [
            ("Skill1", RatingEnum.ADVANCED),  # Meets requirement
            ("Skill2", RatingEnum.BEGINNER)   # Below requirement
        ])
        
        # Create requirements
        create_band_requirements(db, "C", [
            ("Skill1", RatingEnum.INTERMEDIATE),
            ("Skill2", RatingEnum.INTERMEDIATE)
        ])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "C")
        
        # 1 out of 2 requirements met = 50%
        assert result.readiness_score == 50.0
        assert result.skills_meeting_requirement == 1
        assert result.skills_below_requirement == 1


def test_skill_gaps_identifies_missing_skills():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 3.4, 6.5**
    
    Skill gaps should identify skills below requirement.
    """
    with create_test_db() as db:
        # Create employee with one skill below requirement
        employee = create_employee_with_assessments(db, "B", [
            ("Skill1", RatingEnum.ADVANCED),
            ("Skill2", RatingEnum.BEGINNER)
        ])
        
        create_band_requirements(db, "C", [
            ("Skill1", RatingEnum.INTERMEDIATE),
            ("Skill2", RatingEnum.INTERMEDIATE)
        ])
        
        calculator = ReadinessCalculator(db)
        gaps = calculator.get_skill_gaps(employee.id, "C")
        
        # Should only return skills below requirement
        assert len(gaps) == 1
        assert gaps[0].skill_name == "Skill2"
        assert gaps[0].meets_requirement is False


def test_gap_value_calculation():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.5**
    
    Gap value should be current_level - required_level.
    """
    with create_test_db() as db:
        employee = create_employee_with_assessments(db, "B", [
            ("Skill1", RatingEnum.BEGINNER)  # Value = 1
        ])
        
        create_band_requirements(db, "C", [
            ("Skill1", RatingEnum.ADVANCED)  # Value = 4
        ])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "C")
        
        # Gap = 1 - 4 = -3
        assert len(result.skill_gaps) == 1
        assert result.skill_gaps[0].gap_value == -3


def test_next_band_calculation():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1**
    
    Next band should follow the progression: A -> B -> C -> L1 -> L2.
    """
    with create_test_db() as db:
        calculator = ReadinessCalculator(db)
        
        assert calculator.get_next_band("A") == "B"
        assert calculator.get_next_band("B") == "C"
        assert calculator.get_next_band("C") == "L1"
        assert calculator.get_next_band("L1") == "L2"
        assert calculator.get_next_band("L2") is None  # Already at highest


def test_readiness_100_at_highest_band():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1**
    
    Employees at highest band should have 100% readiness (no next band).
    """
    with create_test_db() as db:
        employee = create_employee_with_assessments(db, "L2", [])
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id)
        
        assert result.readiness_score == 100.0
        assert result.target_band == "L2"


def test_readiness_with_no_requirements_defined():
    """
    **Feature: manager-skill-assessment, Property 7: Readiness Score Calculation**
    **Validates: Requirements 6.1**
    
    When no requirements are defined for target band, readiness should be 100%.
    """
    with create_test_db() as db:
        employee = create_employee_with_assessments(db, "A", [])
        
        # No requirements created for band B
        
        calculator = ReadinessCalculator(db)
        result = calculator.calculate_readiness(employee.id, "B")
        
        assert result.readiness_score == 100.0
        assert result.total_required_skills == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

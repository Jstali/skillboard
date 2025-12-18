"""Property-based tests for Baseline Proficiency Mapping.

**Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

For any employee assigned a Band B and Pathway P, all skills in pathway P should 
receive baseline assessments with proficiency level equal to BAND_BASELINE_MAP[B], 
assessor_role "SYSTEM", and assessment_type "baseline".
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
from app.services.baseline_service import BaselineService


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


# Test data strategies
band_strategy = st.sampled_from(["A", "B", "C", "L1", "L2"])
pathway_strategy = st.sampled_from(["Technical", "SAP", "Cloud", "Data", "Consulting"])


def setup_test_data(db, pathway: str, num_skills: int = 3):
    """Set up test employee, skills, and pathway_skills."""
    # Create employee
    employee = Employee(
        employee_id=f"EMP{datetime.now().timestamp()}",
        name="Test Employee",
        company_email="test@example.com",
        band="A",
        pathway=pathway,
        is_active=True
    )
    db.add(employee)
    db.flush()
    
    # Create skills and pathway_skills
    skills = []
    for i in range(num_skills):
        skill = Skill(
            name=f"Skill {i} for {pathway}",
            category=pathway
        )
        db.add(skill)
        db.flush()
        skills.append(skill)
        
        pathway_skill = PathwaySkill(
            pathway=pathway,
            skill_id=skill.id,
            is_core=True,
            display_order=i
        )
        db.add(pathway_skill)
    
    db.commit()
    return employee, skills


@given(band=band_strategy, pathway=pathway_strategy)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_baseline_level_matches_band(band, pathway):
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**
    
    For any band, the baseline level should match the BAND_BASELINE_MAP.
    """
    with create_test_db() as db:
        service = BaselineService(db)
        
        expected_level = service.BAND_BASELINE_MAP.get(band)
        actual_level = service.get_baseline_level(band)
        
        assert actual_level == expected_level
        assert actual_level is not None


@given(band=band_strategy, pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_baseline_assignment_creates_assessments_for_all_pathway_skills(band, pathway):
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.1, 2.7**
    
    For any employee with band and pathway, baseline assignment should create
    assessments for ALL skills in the pathway.
    """
    with create_test_db() as db:
        employee, skills = setup_test_data(db, pathway, num_skills=3)
        
        service = BaselineService(db)
        assessments = service.assign_baseline(
            employee_id=employee.id,
            band=band,
            pathway=pathway
        )
        
        # Should create assessment for each pathway skill
        assert len(assessments) == len(skills)
        
        # Verify all skills are covered
        assessed_skill_ids = {a.skill_id for a in assessments}
        expected_skill_ids = {s.id for s in skills}
        assert assessed_skill_ids == expected_skill_ids


@given(band=band_strategy, pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_baseline_assessment_has_correct_attributes(band, pathway):
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.7**
    
    For any baseline assessment, it should have:
    - assessor_role = "SYSTEM"
    - assessment_type = "baseline"
    - assessor_id = None
    """
    with create_test_db() as db:
        employee, skills = setup_test_data(db, pathway, num_skills=2)
        
        service = BaselineService(db)
        assessments = service.assign_baseline(
            employee_id=employee.id,
            band=band,
            pathway=pathway
        )
        
        expected_level = service.BAND_BASELINE_MAP[band]
        
        for assessment in assessments:
            assert assessment.assessor_role == AssessorRoleEnum.SYSTEM
            assert assessment.assessment_type == AssessmentTypeEnum.BASELINE
            assert assessment.assessor_id is None
            assert assessment.level == expected_level


@given(band=band_strategy, pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_baseline_creates_history_records(band, pathway):
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.7, 5.1**
    
    For any baseline assignment, history records should be created for each assessment.
    """
    with create_test_db() as db:
        employee, skills = setup_test_data(db, pathway, num_skills=2)
        
        service = BaselineService(db)
        assessments = service.assign_baseline(
            employee_id=employee.id,
            band=band,
            pathway=pathway
        )
        
        # Check history records
        history_records = db.query(AssessmentHistory).filter(
            AssessmentHistory.employee_id == employee.id
        ).all()
        
        assert len(history_records) == len(assessments)
        
        for record in history_records:
            assert record.previous_level is None  # First assessment
            assert record.assessment_type == AssessmentTypeEnum.BASELINE
            assert record.assessor_role == AssessorRoleEnum.SYSTEM


@given(band=band_strategy, pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_baseline_skips_existing_assessments(band, pathway):
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.8**
    
    When skip_existing=True, baseline assignment should not overwrite existing assessments.
    """
    with create_test_db() as db:
        employee, skills = setup_test_data(db, pathway, num_skills=3)
        
        # Create an existing assessment for the first skill
        existing = SkillAssessment(
            employee_id=employee.id,
            skill_id=skills[0].id,
            level=RatingEnum.EXPERT,  # Different from baseline
            assessment_type=AssessmentTypeEnum.MANAGER,
            assessor_id=None,
            assessor_role=AssessorRoleEnum.LINE_MANAGER,
            assessed_at=datetime.utcnow()
        )
        db.add(existing)
        db.commit()
        
        service = BaselineService(db)
        assessments = service.assign_baseline(
            employee_id=employee.id,
            band=band,
            pathway=pathway,
            skip_existing=True
        )
        
        # Should only create assessments for skills without existing assessments
        assert len(assessments) == len(skills) - 1
        
        # Verify existing assessment was not modified
        db.refresh(existing)
        assert existing.level == RatingEnum.EXPERT
        assert existing.assessment_type == AssessmentTypeEnum.MANAGER


def test_band_baseline_map_completeness():
    """
    **Feature: manager-skill-assessment, Property 2: Baseline Proficiency Mapping**
    **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**
    
    The BAND_BASELINE_MAP should have entries for all valid bands.
    """
    expected_bands = ["A", "B", "C", "L1", "L2"]
    expected_levels = [
        RatingEnum.BEGINNER,
        RatingEnum.DEVELOPING,
        RatingEnum.INTERMEDIATE,
        RatingEnum.ADVANCED,
        RatingEnum.EXPERT
    ]
    
    with create_test_db() as db:
        service = BaselineService(db)
        
        for band, expected_level in zip(expected_bands, expected_levels):
            actual_level = service.get_baseline_level(band)
            assert actual_level == expected_level, f"Band {band} should map to {expected_level}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

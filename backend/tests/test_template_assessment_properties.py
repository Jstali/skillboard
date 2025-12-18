"""Property-based tests for Template Assessment Service.

Tests for template-based skill assessments by managers.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import json

from app.db.models import (
    Base, Employee, Skill, SkillTemplate, SkillAssessment,
    TemplateAssessmentLog, RatingEnum, AssessmentTypeEnum, AssessorRoleEnum,
    Project, EmployeeProjectAssignment
)
from app.services.template_assessment import TemplateAssessmentService, SkillAssessmentInput
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


def create_employee(db, employee_id: str, name: str, line_manager_id=None):
    """Helper to create an employee."""
    emp = Employee(
        employee_id=employee_id,
        name=name,
        company_email=f"{employee_id}@example.com",
        band="B",
        is_active=True,
        line_manager_id=line_manager_id
    )
    db.add(emp)
    db.flush()
    return emp


def create_skill(db, name: str, category: str = None):
    """Helper to create a skill."""
    skill = Skill(
        name=name,
        description=f"Description for {name}",
        category=category
    )
    db.add(skill)
    db.flush()
    return skill


def create_template(db, name: str, skills: list):
    """Helper to create a skill template with skills.
    
    Args:
        db: Database session
        name: Template name
        skills: List of dicts with skill_name and required_level
    """
    content = json.dumps(skills)
    template = SkillTemplate(
        template_name=name,
        file_name=f"{name}.xlsx",
        content=content,
        created_at=datetime.utcnow()
    )
    db.add(template)
    db.flush()
    return template


def create_assessment(db, employee_id: int, skill_id: int, level: RatingEnum, assessor_id: int = None):
    """Helper to create a skill assessment."""
    assessment = SkillAssessment(
        employee_id=employee_id,
        skill_id=skill_id,
        level=level,
        assessment_type=AssessmentTypeEnum.MANAGER,
        assessor_id=assessor_id,
        assessor_role=AssessorRoleEnum.LINE_MANAGER,
        assessed_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(assessment)
    db.flush()
    return assessment


def create_project(db, name: str):
    """Helper to create a project."""
    project = Project(
        name=name,
        description="Test project"
    )
    db.add(project)
    db.flush()
    return project


def create_project_assignment(db, employee_id: int, project_id: int, line_manager_id: int):
    """Helper to create a project assignment."""
    assignment = EmployeeProjectAssignment(
        employee_id=employee_id,
        project_id=project_id,
        line_manager_id=line_manager_id,
        percentage_allocation=100
    )
    db.add(assignment)
    db.flush()
    return assignment


# Strategies for generating test data
skill_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters=' -_'),
    min_size=3,
    max_size=30
).filter(lambda x: x.strip())

rating_strategy = st.sampled_from(list(RatingEnum))

num_skills_strategy = st.integers(min_value=1, max_value=10)


class TestTemplateSkillsRetrieval:
    """
    **Feature: manager-template-assessment, Property 1: Template Skills Retrieval**
    **Validates: Requirements 1.1, 1.2**
    
    For any skill template T and employee E, when a manager requests template 
    assessment view, the system should return all skills defined in T with E's 
    current assessment levels (or null if not assessed).
    """
    
    @given(num_skills=num_skills_strategy)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_all_template_skills(self, num_skills):
        """
        **Feature: manager-template-assessment, Property 1: Template Skills Retrieval**
        **Validates: Requirements 1.1, 1.2**
        
        For any template with N skills, get_template_for_assessment should return 
        exactly N skills in the result.
        """
        with create_test_db() as db:
            # Create employee
            employee = create_employee(db, "EMP001", "Test Employee")
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(num_skills):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            db.commit()
            
            # Get template for assessment
            service = TemplateAssessmentService(db)
            result = service.get_template_for_assessment(template.id, employee.id)
            
            # Verify all skills are returned
            assert result.total_skills == num_skills
            assert len(result.skills) == num_skills
    
    @given(num_assessed=st.integers(min_value=0, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_current_levels_for_assessed_skills(self, num_assessed):
        """
        **Feature: manager-template-assessment, Property 1: Template Skills Retrieval**
        **Validates: Requirements 1.1, 1.2**
        
        For any employee with M assessed skills from template, the result should 
        show current levels for those M skills and null for unassessed skills.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create 5 skills total
            total_skills = 5
            skills = []
            template_skills = []
            for i in range(total_skills):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            
            # Create assessments for first num_assessed skills
            for i in range(min(num_assessed, total_skills)):
                create_assessment(db, employee.id, skills[i].id, RatingEnum.INTERMEDIATE, manager.id)
            
            db.commit()
            
            # Get template for assessment
            service = TemplateAssessmentService(db)
            result = service.get_template_for_assessment(template.id, employee.id)
            
            # Count assessed skills in result
            assessed_in_result = sum(1 for s in result.skills if s.is_assessed)
            
            assert assessed_in_result == min(num_assessed, total_skills)
            assert result.assessed_skills == min(num_assessed, total_skills)
            
            # Verify assessed skills have current_level set
            for skill_view in result.skills:
                if skill_view.is_assessed:
                    assert skill_view.current_level is not None
                else:
                    assert skill_view.current_level is None
    
    def test_returns_required_levels_from_template(self):
        """
        **Feature: manager-template-assessment, Property 1: Template Skills Retrieval**
        **Validates: Requirements 1.2**
        
        The result should include required levels from the template for each skill.
        """
        with create_test_db() as db:
            # Create employee
            employee = create_employee(db, "EMP001", "Test Employee")
            
            # Create skills with different required levels
            skill1 = create_skill(db, "Python", "Programming")
            skill2 = create_skill(db, "Java", "Programming")
            skill3 = create_skill(db, "AWS", "Cloud")
            
            template_skills = [
                {"skill_name": "Python", "required_level": "Expert"},
                {"skill_name": "Java", "required_level": "Advanced"},
                {"skill_name": "AWS", "required_level": "Intermediate"}
            ]
            
            template = create_template(db, "Dev Template", template_skills)
            db.commit()
            
            service = TemplateAssessmentService(db)
            result = service.get_template_for_assessment(template.id, employee.id)
            
            # Verify required levels are returned
            skill_levels = {s.skill_name: s.required_level for s in result.skills}
            assert skill_levels.get("Python") == "Expert"
            assert skill_levels.get("Java") == "Advanced"
            assert skill_levels.get("AWS") == "Intermediate"
    
    def test_handles_missing_skills_gracefully(self):
        """
        **Feature: manager-template-assessment, Property 1: Template Skills Retrieval**
        **Validates: Requirements 1.1**
        
        If a skill in the template doesn't exist in the database, it should still 
        be included in the result with skill_id=0.
        """
        with create_test_db() as db:
            # Create employee
            employee = create_employee(db, "EMP001", "Test Employee")
            
            # Create only one skill in database
            skill1 = create_skill(db, "Python", "Programming")
            
            # Template references both existing and non-existing skills
            template_skills = [
                {"skill_name": "Python", "required_level": "Expert"},
                {"skill_name": "NonExistentSkill", "required_level": "Advanced"}
            ]
            
            template = create_template(db, "Mixed Template", template_skills)
            db.commit()
            
            service = TemplateAssessmentService(db)
            result = service.get_template_for_assessment(template.id, employee.id)
            
            # Should return both skills
            assert result.total_skills == 2
            
            # Find the non-existent skill
            non_existent = next((s for s in result.skills if s.skill_name == "NonExistentSkill"), None)
            assert non_existent is not None
            assert non_existent.skill_id == 0
            assert non_existent.is_assessed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestTemplateAssessmentCompleteness:
    """
    **Feature: manager-template-assessment, Property 2: Template Assessment Completeness**
    **Validates: Requirements 1.3, 1.4**
    
    For any template assessment submission with N skill assessments, the system 
    should create or update exactly N skill_assessment records and create one 
    template_assessment_log record.
    """
    
    @given(num_assessments=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_creates_correct_number_of_assessments(self, num_assessments):
        """
        **Feature: manager-template-assessment, Property 2: Template Assessment Completeness**
        **Validates: Requirements 1.3, 1.4**
        
        For any submission with N assessments, exactly N skill_assessment records 
        should be created or updated.
        """
        with create_test_db() as db:
            # Create manager and employee (direct report)
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(num_assessments):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            db.commit()
            
            # Prepare assessment inputs
            assessment_inputs = [
                SkillAssessmentInput(
                    skill_id=skill.id,
                    level=RatingEnum.INTERMEDIATE.value,
                    comments=f"Assessment for {skill.name}"
                )
                for skill in skills
            ]
            
            # Submit assessments
            service = TemplateAssessmentService(db)
            result = service.submit_template_assessment(
                template_id=template.id,
                employee_id=employee.id,
                assessor_id=manager.id,
                assessor_role_id=RoleID.LINE_MANAGER,
                assessments=assessment_inputs
            )
            
            # Verify correct number of assessments created
            assert result.skills_assessed == num_assessments
            
            # Verify assessments in database
            db_assessments = db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee.id
            ).all()
            assert len(db_assessments) == num_assessments
    
    @given(num_assessments=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_creates_single_log_record(self, num_assessments):
        """
        **Feature: manager-template-assessment, Property 2: Template Assessment Completeness**
        **Validates: Requirements 1.4**
        
        For any template assessment submission, exactly one template_assessment_log 
        record should be created.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(num_assessments):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            db.commit()
            
            # Count existing logs
            initial_log_count = db.query(TemplateAssessmentLog).count()
            
            # Prepare assessment inputs
            assessment_inputs = [
                SkillAssessmentInput(
                    skill_id=skill.id,
                    level=RatingEnum.INTERMEDIATE.value
                )
                for skill in skills
            ]
            
            # Submit assessments
            service = TemplateAssessmentService(db)
            result = service.submit_template_assessment(
                template_id=template.id,
                employee_id=employee.id,
                assessor_id=manager.id,
                assessor_role_id=RoleID.LINE_MANAGER,
                assessments=assessment_inputs
            )
            
            # Verify exactly one log record created
            final_log_count = db.query(TemplateAssessmentLog).count()
            assert final_log_count == initial_log_count + 1
            
            # Verify log record has correct data
            log = db.query(TemplateAssessmentLog).filter(
                TemplateAssessmentLog.id == result.log_id
            ).first()
            assert log is not None
            assert log.template_id == template.id
            assert log.employee_id == employee.id
            assert log.assessor_id == manager.id
            assert log.skills_assessed == num_assessments
    
    def test_updates_existing_assessments(self):
        """
        **Feature: manager-template-assessment, Property 2: Template Assessment Completeness**
        **Validates: Requirements 1.3**
        
        When submitting assessments for skills that already have assessments, 
        the existing records should be updated (not duplicated).
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill
            skill = create_skill(db, "Python", "Programming")
            template_skills = [{"skill_name": "Python", "required_level": "Expert"}]
            template = create_template(db, "Dev Template", template_skills)
            
            # Create initial assessment
            create_assessment(db, employee.id, skill.id, RatingEnum.BEGINNER, manager.id)
            db.commit()
            
            # Verify initial state
            initial_count = db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee.id,
                SkillAssessment.skill_id == skill.id
            ).count()
            assert initial_count == 1
            
            # Submit new assessment (update)
            service = TemplateAssessmentService(db)
            result = service.submit_template_assessment(
                template_id=template.id,
                employee_id=employee.id,
                assessor_id=manager.id,
                assessor_role_id=RoleID.LINE_MANAGER,
                assessments=[
                    SkillAssessmentInput(
                        skill_id=skill.id,
                        level=RatingEnum.ADVANCED.value,
                        comments="Updated assessment"
                    )
                ]
            )
            
            # Verify no duplicate created
            final_count = db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee.id,
                SkillAssessment.skill_id == skill.id
            ).count()
            assert final_count == 1
            
            # Verify level was updated
            assessment = db.query(SkillAssessment).filter(
                SkillAssessment.employee_id == employee.id,
                SkillAssessment.skill_id == skill.id
            ).first()
            assert assessment.level == RatingEnum.ADVANCED
    
    def test_rejects_unauthorized_assessor(self):
        """
        **Feature: manager-template-assessment, Property 2: Template Assessment Completeness**
        **Validates: Requirements 1.3**
        
        Assessment submission should fail if assessor lacks authority over employee.
        """
        with create_test_db() as db:
            # Create two unrelated employees
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee")  # No line_manager_id
            
            # Create skill and template
            skill = create_skill(db, "Python", "Programming")
            template_skills = [{"skill_name": "Python", "required_level": "Expert"}]
            template = create_template(db, "Dev Template", template_skills)
            db.commit()
            
            # Attempt to submit assessment
            service = TemplateAssessmentService(db)
            
            with pytest.raises(PermissionError) as exc_info:
                service.submit_template_assessment(
                    template_id=template.id,
                    employee_id=employee.id,
                    assessor_id=manager.id,
                    assessor_role_id=RoleID.LINE_MANAGER,
                    assessments=[
                        SkillAssessmentInput(
                            skill_id=skill.id,
                            level=RatingEnum.INTERMEDIATE.value
                        )
                    ]
                )
            
            assert "not authorized" in str(exc_info.value).lower()


class TestAssessmentProgressCalculation:
    """
    **Feature: manager-template-assessment, Property 3: Assessment Progress Calculation**
    **Validates: Requirements 1.5**
    
    For any template T with N skills and employee E with M assessed skills from T, 
    the progress percentage should equal (M / N) * 100.
    """
    
    @given(
        total_skills=st.integers(min_value=1, max_value=10),
        assessed_ratio=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_progress_percentage_calculation(self, total_skills, assessed_ratio):
        """
        **Feature: manager-template-assessment, Property 3: Assessment Progress Calculation**
        **Validates: Requirements 1.5**
        
        For any template with N skills and M assessed skills, 
        progress = (M / N) * 100.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(total_skills):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            
            # Calculate how many skills to assess based on ratio
            num_assessed = int(total_skills * assessed_ratio)
            
            # Create assessments for first num_assessed skills
            for i in range(num_assessed):
                create_assessment(db, employee.id, skills[i].id, RatingEnum.INTERMEDIATE, manager.id)
            
            db.commit()
            
            # Get progress
            service = TemplateAssessmentService(db)
            progress = service.get_assessment_progress(template.id, employee.id)
            
            # Verify calculation
            expected_percentage = (num_assessed / total_skills) * 100
            assert progress.total_skills == total_skills
            assert progress.assessed_skills == num_assessed
            assert abs(progress.completion_percentage - expected_percentage) < 0.01
    
    def test_zero_skills_returns_zero_percentage(self):
        """
        **Feature: manager-template-assessment, Property 3: Assessment Progress Calculation**
        **Validates: Requirements 1.5**
        
        For a template with no skills, progress should be 0%.
        """
        with create_test_db() as db:
            # Create employee
            employee = create_employee(db, "EMP001", "Test Employee")
            
            # Create empty template
            template = create_template(db, "Empty Template", [])
            db.commit()
            
            service = TemplateAssessmentService(db)
            progress = service.get_assessment_progress(template.id, employee.id)
            
            assert progress.total_skills == 0
            assert progress.assessed_skills == 0
            assert progress.completion_percentage == 0.0
    
    def test_all_skills_assessed_returns_100_percent(self):
        """
        **Feature: manager-template-assessment, Property 3: Assessment Progress Calculation**
        **Validates: Requirements 1.5**
        
        When all skills are assessed, progress should be 100%.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(5):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template
            template = create_template(db, "Test Template", template_skills)
            
            # Assess all skills
            for skill in skills:
                create_assessment(db, employee.id, skill.id, RatingEnum.INTERMEDIATE, manager.id)
            
            db.commit()
            
            service = TemplateAssessmentService(db)
            progress = service.get_assessment_progress(template.id, employee.id)
            
            assert progress.total_skills == 5
            assert progress.assessed_skills == 5
            assert progress.completion_percentage == 100.0
    
    def test_no_skills_assessed_returns_zero_percent(self):
        """
        **Feature: manager-template-assessment, Property 3: Assessment Progress Calculation**
        **Validates: Requirements 1.5**
        
        When no skills are assessed, progress should be 0%.
        """
        with create_test_db() as db:
            # Create employee
            employee = create_employee(db, "EMP001", "Test Employee")
            
            # Create skills
            skills = []
            template_skills = []
            for i in range(5):
                skill = create_skill(db, f"Skill_{i}", "Technical")
                skills.append(skill)
                template_skills.append({
                    "skill_name": skill.name,
                    "required_level": "Intermediate"
                })
            
            # Create template (no assessments)
            template = create_template(db, "Test Template", template_skills)
            db.commit()
            
            service = TemplateAssessmentService(db)
            progress = service.get_assessment_progress(template.id, employee.id)
            
            assert progress.total_skills == 5
            assert progress.assessed_skills == 0
            assert progress.completion_percentage == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

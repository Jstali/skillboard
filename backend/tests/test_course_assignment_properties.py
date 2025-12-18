"""Property-based tests for Course Assignment Service.

Tests for course assignments by managers.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import (
    Base, Employee, Skill, Course, CourseAssignment, CourseStatusEnum,
    Project, EmployeeProjectAssignment
)
from app.services.course_assignment import CourseAssignmentService
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


def create_employee(db, employee_id: str, name: str, line_manager_id=None, location_id=None):
    """Helper to create an employee."""
    emp = Employee(
        employee_id=employee_id,
        name=name,
        company_email=f"{employee_id}@example.com",
        band="B",
        is_active=True,
        line_manager_id=line_manager_id,
        location_id=location_id
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


def create_course(db, title: str, skill_id: int = None, is_mandatory: bool = False):
    """Helper to create a course."""
    course = Course(
        title=title,
        description=f"Description for {title}",
        skill_id=skill_id,
        external_url=f"https://example.com/courses/{title.lower().replace(' ', '-')}",
        is_mandatory=is_mandatory,
        created_at=datetime.utcnow()
    )
    db.add(course)
    db.flush()
    return course


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
num_courses_strategy = st.integers(min_value=0, max_value=10)


class TestCourseSkillAssociation:
    """
    **Feature: manager-template-assessment, Property 4: Course-Skill Association**
    **Validates: Requirements 2.1, 2.2, 4.1**
    
    For any skill S with associated courses, querying courses for S should return 
    all courses where course.skill_id = S.id, with complete course details 
    (title, description, external_url, is_mandatory).
    """
    
    @given(num_courses=num_courses_strategy)
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_all_courses_for_skill(self, num_courses):
        """
        **Feature: manager-template-assessment, Property 4: Course-Skill Association**
        **Validates: Requirements 2.1, 2.2, 4.1**
        
        For any skill with N associated courses, get_courses_for_skill should 
        return exactly N courses.
        """
        with create_test_db() as db:
            # Create skill
            skill = create_skill(db, "Python", "Programming")
            
            # Create courses for this skill
            for i in range(num_courses):
                create_course(db, f"Python Course {i}", skill_id=skill.id)
            
            # Create some courses for other skills (should not be returned)
            other_skill = create_skill(db, "Java", "Programming")
            create_course(db, "Java Course", skill_id=other_skill.id)
            
            db.commit()
            
            # Get courses for skill
            service = CourseAssignmentService(db)
            result = service.get_courses_for_skill(skill.id)
            
            # Verify correct number of courses returned
            assert len(result) == num_courses
            
            # Verify all returned courses are for the correct skill
            for course in result:
                assert course.skill_id == skill.id
    
    @given(num_courses=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_complete_course_details(self, num_courses):
        """
        **Feature: manager-template-assessment, Property 4: Course-Skill Association**
        **Validates: Requirements 2.1, 2.2**
        
        For any course returned, all required fields should be present:
        title, description, external_url, is_mandatory.
        """
        with create_test_db() as db:
            # Create skill
            skill = create_skill(db, "AWS", "Cloud")
            
            # Create courses with various properties
            for i in range(num_courses):
                create_course(
                    db, 
                    f"AWS Course {i}", 
                    skill_id=skill.id,
                    is_mandatory=(i % 2 == 0)
                )
            
            db.commit()
            
            # Get courses for skill
            service = CourseAssignmentService(db)
            result = service.get_courses_for_skill(skill.id)
            
            # Verify all courses have complete details
            for course in result:
                assert course.id is not None
                assert course.title is not None
                assert course.description is not None
                assert course.external_url is not None
                assert course.is_mandatory is not None
                assert course.skill_id == skill.id
                assert course.skill_name == "AWS"
    
    def test_returns_empty_list_for_skill_with_no_courses(self):
        """
        **Feature: manager-template-assessment, Property 4: Course-Skill Association**
        **Validates: Requirements 2.3**
        
        For a skill with no associated courses, should return empty list.
        """
        with create_test_db() as db:
            # Create skill with no courses
            skill = create_skill(db, "Rust", "Programming")
            db.commit()
            
            service = CourseAssignmentService(db)
            result = service.get_courses_for_skill(skill.id)
            
            assert len(result) == 0
    
    def test_filters_by_skill_id_correctly(self):
        """
        **Feature: manager-template-assessment, Property 4: Course-Skill Association**
        **Validates: Requirements 2.1, 4.1**
        
        Courses for different skills should not be mixed.
        """
        with create_test_db() as db:
            # Create multiple skills
            skill1 = create_skill(db, "Python", "Programming")
            skill2 = create_skill(db, "Java", "Programming")
            skill3 = create_skill(db, "AWS", "Cloud")
            
            # Create courses for each skill
            create_course(db, "Python Basics", skill_id=skill1.id)
            create_course(db, "Python Advanced", skill_id=skill1.id)
            create_course(db, "Java Fundamentals", skill_id=skill2.id)
            create_course(db, "AWS Solutions Architect", skill_id=skill3.id)
            create_course(db, "AWS Developer", skill_id=skill3.id)
            create_course(db, "AWS DevOps", skill_id=skill3.id)
            
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Verify each skill returns only its courses
            python_courses = service.get_courses_for_skill(skill1.id)
            assert len(python_courses) == 2
            assert all(c.skill_id == skill1.id for c in python_courses)
            
            java_courses = service.get_courses_for_skill(skill2.id)
            assert len(java_courses) == 1
            assert all(c.skill_id == skill2.id for c in java_courses)
            
            aws_courses = service.get_courses_for_skill(skill3.id)
            assert len(aws_courses) == 3
            assert all(c.skill_id == skill3.id for c in aws_courses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestCourseAssignmentAuthority:
    """
    **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
    **Validates: Requirements 3.1, 3.2**
    
    For any course assignment request by manager M for employee E, the assignment 
    should succeed only if AuthorityValidator.can_assess(M, E) returns true. 
    Otherwise, HTTP 403 should be returned.
    """
    
    def test_direct_report_can_be_assigned_course(self):
        """
        **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
        **Validates: Requirements 3.1, 3.2**
        
        Manager can assign course to direct report.
        """
        with create_test_db() as db:
            # Create manager and direct report
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            # Assign course
            service = CourseAssignmentService(db)
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Verify assignment created
            assert assignment is not None
            assert assignment.course_id == course.id
            assert assignment.employee_id == employee.id
            assert assignment.assigned_by == manager.id
    
    def test_project_manager_can_assign_course(self):
        """
        **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
        **Validates: Requirements 3.1, 3.2**
        
        Manager can assign course to employee on their project.
        """
        with create_test_db() as db:
            # Create manager and employee (not direct report)
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee")
            
            # Create project assignment with manager
            project = create_project(db, "Test Project")
            create_project_assignment(db, employee.id, project.id, manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            # Assign course
            service = CourseAssignmentService(db)
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Verify assignment created
            assert assignment is not None
            assert assignment.course_id == course.id
            assert assignment.employee_id == employee.id
    
    def test_unauthorized_manager_cannot_assign_course(self):
        """
        **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
        **Validates: Requirements 3.1, 3.2**
        
        Manager without authority over employee should get PermissionError.
        """
        with create_test_db() as db:
            # Create manager and unrelated employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee")  # No relationship
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            # Attempt to assign course
            service = CourseAssignmentService(db)
            
            with pytest.raises(PermissionError) as exc_info:
                service.assign_course(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=manager.id,
                    assigned_by_role_id=RoleID.LINE_MANAGER
                )
            
            assert "not authorized" in str(exc_info.value).lower()
    
    def test_non_manager_role_cannot_assign_course(self):
        """
        **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
        **Validates: Requirements 3.1, 3.2**
        
        Non-manager roles should not be able to assign courses.
        """
        with create_test_db() as db:
            # Create two employees (one trying to assign to another)
            employee1 = create_employee(db, "EMP001", "Employee 1")
            employee2 = create_employee(db, "EMP002", "Employee 2")
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            # Attempt to assign course with employee role
            service = CourseAssignmentService(db)
            
            with pytest.raises(PermissionError) as exc_info:
                service.assign_course(
                    course_id=course.id,
                    employee_id=employee2.id,
                    assigned_by=employee1.id,
                    assigned_by_role_id=RoleID.EMPLOYEE  # Not a manager role
                )
            
            assert "only line managers" in str(exc_info.value).lower()
    
    @given(has_authority=st.booleans())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_authority_determines_assignment_success(self, has_authority):
        """
        **Feature: manager-template-assessment, Property 5: Course Assignment Authority**
        **Validates: Requirements 3.1, 3.2**
        
        For any manager-employee pair, assignment succeeds iff authority exists.
        """
        with create_test_db() as db:
            # Create manager
            manager = create_employee(db, "MGR001", "Manager")
            
            # Create employee with or without authority relationship
            if has_authority:
                employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            else:
                employee = create_employee(db, "EMP001", "Employee")
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            if has_authority:
                # Should succeed
                assignment = service.assign_course(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=manager.id,
                    assigned_by_role_id=RoleID.LINE_MANAGER
                )
                assert assignment is not None
            else:
                # Should fail
                with pytest.raises(PermissionError):
                    service.assign_course(
                        course_id=course.id,
                        employee_id=employee.id,
                        assigned_by=manager.id,
                        assigned_by_role_id=RoleID.LINE_MANAGER
                    )



class TestCourseAssignmentIdempotency:
    """
    **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
    **Validates: Requirements 3.4**
    
    For any course C and employee E, attempting to assign C to E when an assignment 
    already exists should not create a duplicate record and should return an 
    appropriate error message.
    """
    
    def test_duplicate_assignment_raises_error(self):
        """
        **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
        **Validates: Requirements 3.4**
        
        Assigning the same course twice should raise ValueError.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # First assignment should succeed
            assignment1 = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            assert assignment1 is not None
            
            # Second assignment should fail
            with pytest.raises(ValueError) as exc_info:
                service.assign_course(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=manager.id,
                    assigned_by_role_id=RoleID.LINE_MANAGER
                )
            
            assert "already assigned" in str(exc_info.value).lower()
    
    def test_no_duplicate_records_created(self):
        """
        **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
        **Validates: Requirements 3.4**
        
        After duplicate assignment attempt, only one record should exist.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # First assignment
            service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Count assignments
            initial_count = db.query(CourseAssignment).filter(
                CourseAssignment.course_id == course.id,
                CourseAssignment.employee_id == employee.id
            ).count()
            assert initial_count == 1
            
            # Attempt duplicate assignment
            try:
                service.assign_course(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=manager.id,
                    assigned_by_role_id=RoleID.LINE_MANAGER
                )
            except ValueError:
                pass  # Expected
            
            # Count should still be 1
            final_count = db.query(CourseAssignment).filter(
                CourseAssignment.course_id == course.id,
                CourseAssignment.employee_id == employee.id
            ).count()
            assert final_count == 1
    
    @given(num_attempts=st.integers(min_value=2, max_value=5))
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_duplicate_attempts_still_single_record(self, num_attempts):
        """
        **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
        **Validates: Requirements 3.4**
        
        For any number of duplicate assignment attempts, only one record exists.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # First assignment should succeed
            service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Multiple duplicate attempts
            for _ in range(num_attempts - 1):
                try:
                    service.assign_course(
                        course_id=course.id,
                        employee_id=employee.id,
                        assigned_by=manager.id,
                        assigned_by_role_id=RoleID.LINE_MANAGER
                    )
                except ValueError:
                    pass  # Expected
            
            # Should still have exactly one record
            count = db.query(CourseAssignment).filter(
                CourseAssignment.course_id == course.id,
                CourseAssignment.employee_id == employee.id
            ).count()
            assert count == 1
    
    def test_different_courses_can_be_assigned_to_same_employee(self):
        """
        **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
        **Validates: Requirements 3.4**
        
        Different courses can be assigned to the same employee.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and multiple courses
            skill = create_skill(db, "Python", "Programming")
            course1 = create_course(db, "Python Basics", skill_id=skill.id)
            course2 = create_course(db, "Python Advanced", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Both assignments should succeed
            assignment1 = service.assign_course(
                course_id=course1.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            assignment2 = service.assign_course(
                course_id=course2.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            assert assignment1 is not None
            assert assignment2 is not None
            assert assignment1.course_id != assignment2.course_id
    
    def test_same_course_can_be_assigned_to_different_employees(self):
        """
        **Feature: manager-template-assessment, Property 6: Course Assignment Idempotency**
        **Validates: Requirements 3.4**
        
        Same course can be assigned to different employees.
        """
        with create_test_db() as db:
            # Create manager and multiple employees
            manager = create_employee(db, "MGR001", "Manager")
            employee1 = create_employee(db, "EMP001", "Employee 1", line_manager_id=manager.id)
            employee2 = create_employee(db, "EMP002", "Employee 2", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Both assignments should succeed
            assignment1 = service.assign_course(
                course_id=course.id,
                employee_id=employee1.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            assignment2 = service.assign_course(
                course_id=course.id,
                employee_id=employee2.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            assert assignment1 is not None
            assert assignment2 is not None
            assert assignment1.employee_id != assignment2.employee_id



class TestManagerAssignmentFiltering:
    """
    **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any manager M, querying their assignments should return only CourseAssignment 
    records where assigned_by = M.employee_id, with correct filtering by status, 
    employee, and course when specified.
    """
    
    def test_returns_only_manager_assignments(self):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.1, 5.2**
        
        Should return only assignments made by the specified manager.
        """
        with create_test_db() as db:
            # Create two managers
            manager1 = create_employee(db, "MGR001", "Manager 1")
            manager2 = create_employee(db, "MGR002", "Manager 2")
            
            # Create employees for each manager
            emp1 = create_employee(db, "EMP001", "Employee 1", line_manager_id=manager1.id)
            emp2 = create_employee(db, "EMP002", "Employee 2", line_manager_id=manager2.id)
            
            # Create skill and courses
            skill = create_skill(db, "Python", "Programming")
            course1 = create_course(db, "Python Basics", skill_id=skill.id)
            course2 = create_course(db, "Python Advanced", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Manager 1 assigns course to their employee
            service.assign_course(
                course_id=course1.id,
                employee_id=emp1.id,
                assigned_by=manager1.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Manager 2 assigns course to their employee
            service.assign_course(
                course_id=course2.id,
                employee_id=emp2.id,
                assigned_by=manager2.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Get manager 1's assignments
            manager1_assignments = service.get_manager_assignments(manager1.id)
            
            # Should only see manager 1's assignments
            assert len(manager1_assignments) == 1
            assert all(a.assigned_by == manager1.id for a in manager1_assignments)
            
            # Get manager 2's assignments
            manager2_assignments = service.get_manager_assignments(manager2.id)
            
            # Should only see manager 2's assignments
            assert len(manager2_assignments) == 1
            assert all(a.assigned_by == manager2.id for a in manager2_assignments)
    
    def test_filters_by_status(self):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.3**
        
        Should filter assignments by status correctly.
        """
        with create_test_db() as db:
            # Create manager and employees
            manager = create_employee(db, "MGR001", "Manager")
            emp1 = create_employee(db, "EMP001", "Employee 1", line_manager_id=manager.id)
            emp2 = create_employee(db, "EMP002", "Employee 2", line_manager_id=manager.id)
            emp3 = create_employee(db, "EMP003", "Employee 3", line_manager_id=manager.id)
            
            # Create skill and courses
            skill = create_skill(db, "Python", "Programming")
            course1 = create_course(db, "Course 1", skill_id=skill.id)
            course2 = create_course(db, "Course 2", skill_id=skill.id)
            course3 = create_course(db, "Course 3", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignments
            a1 = service.assign_course(course_id=course1.id, employee_id=emp1.id, 
                                       assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            a2 = service.assign_course(course_id=course2.id, employee_id=emp2.id,
                                       assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            a3 = service.assign_course(course_id=course3.id, employee_id=emp3.id,
                                       assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            
            # Update statuses
            service.update_assignment_status(a2.id, CourseStatusEnum.IN_PROGRESS.value)
            service.update_assignment_status(a3.id, CourseStatusEnum.IN_PROGRESS.value)
            service.update_assignment_status(a3.id, CourseStatusEnum.COMPLETED.value)
            
            # Filter by NOT_STARTED
            not_started = service.get_manager_assignments(manager.id, status_filter=CourseStatusEnum.NOT_STARTED.value)
            assert len(not_started) == 1
            assert all(a.status == CourseStatusEnum.NOT_STARTED.value for a in not_started)
            
            # Filter by IN_PROGRESS
            in_progress = service.get_manager_assignments(manager.id, status_filter=CourseStatusEnum.IN_PROGRESS.value)
            assert len(in_progress) == 1
            assert all(a.status == CourseStatusEnum.IN_PROGRESS.value for a in in_progress)
            
            # Filter by COMPLETED
            completed = service.get_manager_assignments(manager.id, status_filter=CourseStatusEnum.COMPLETED.value)
            assert len(completed) == 1
            assert all(a.status == CourseStatusEnum.COMPLETED.value for a in completed)
    
    def test_filters_by_employee(self):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.3**
        
        Should filter assignments by employee correctly.
        """
        with create_test_db() as db:
            # Create manager and employees
            manager = create_employee(db, "MGR001", "Manager")
            emp1 = create_employee(db, "EMP001", "Employee 1", line_manager_id=manager.id)
            emp2 = create_employee(db, "EMP002", "Employee 2", line_manager_id=manager.id)
            
            # Create skill and courses
            skill = create_skill(db, "Python", "Programming")
            course1 = create_course(db, "Course 1", skill_id=skill.id)
            course2 = create_course(db, "Course 2", skill_id=skill.id)
            course3 = create_course(db, "Course 3", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Assign courses
            service.assign_course(course_id=course1.id, employee_id=emp1.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            service.assign_course(course_id=course2.id, employee_id=emp1.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            service.assign_course(course_id=course3.id, employee_id=emp2.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            
            # Filter by employee 1
            emp1_assignments = service.get_manager_assignments(manager.id, employee_id=emp1.id)
            assert len(emp1_assignments) == 2
            assert all(a.employee_id == emp1.id for a in emp1_assignments)
            
            # Filter by employee 2
            emp2_assignments = service.get_manager_assignments(manager.id, employee_id=emp2.id)
            assert len(emp2_assignments) == 1
            assert all(a.employee_id == emp2.id for a in emp2_assignments)
    
    def test_filters_by_course(self):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.3**
        
        Should filter assignments by course correctly.
        """
        with create_test_db() as db:
            # Create manager and employees
            manager = create_employee(db, "MGR001", "Manager")
            emp1 = create_employee(db, "EMP001", "Employee 1", line_manager_id=manager.id)
            emp2 = create_employee(db, "EMP002", "Employee 2", line_manager_id=manager.id)
            
            # Create skill and courses
            skill = create_skill(db, "Python", "Programming")
            course1 = create_course(db, "Course 1", skill_id=skill.id)
            course2 = create_course(db, "Course 2", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Assign courses
            service.assign_course(course_id=course1.id, employee_id=emp1.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            service.assign_course(course_id=course1.id, employee_id=emp2.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            service.assign_course(course_id=course2.id, employee_id=emp1.id,
                                 assigned_by=manager.id, assigned_by_role_id=RoleID.LINE_MANAGER)
            
            # Filter by course 1
            course1_assignments = service.get_manager_assignments(manager.id, course_id=course1.id)
            assert len(course1_assignments) == 2
            assert all(a.course_id == course1.id for a in course1_assignments)
            
            # Filter by course 2
            course2_assignments = service.get_manager_assignments(manager.id, course_id=course2.id)
            assert len(course2_assignments) == 1
            assert all(a.course_id == course2.id for a in course2_assignments)
    
    @given(num_assignments=st.integers(min_value=0, max_value=5))
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_correct_count_of_assignments(self, num_assignments):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.1, 5.2**
        
        For any manager with N assignments, should return exactly N records.
        """
        with create_test_db() as db:
            # Create manager
            manager = create_employee(db, "MGR001", "Manager")
            
            # Create skill
            skill = create_skill(db, "Python", "Programming")
            
            # Create employees and courses, then assign
            for i in range(num_assignments):
                emp = create_employee(db, f"EMP{i:03d}", f"Employee {i}", line_manager_id=manager.id)
                course = create_course(db, f"Course {i}", skill_id=skill.id)
                db.flush()
            
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Assign courses
            employees = db.query(Employee).filter(Employee.line_manager_id == manager.id).all()
            courses = db.query(Course).all()
            
            for i, (emp, course) in enumerate(zip(employees, courses)):
                service.assign_course(
                    course_id=course.id,
                    employee_id=emp.id,
                    assigned_by=manager.id,
                    assigned_by_role_id=RoleID.LINE_MANAGER
                )
            
            # Get assignments
            assignments = service.get_manager_assignments(manager.id)
            
            assert len(assignments) == num_assignments
    
    def test_includes_complete_assignment_details(self):
        """
        **Feature: manager-template-assessment, Property 8: Manager Assignment Filtering**
        **Validates: Requirements 5.2**
        
        Should include employee name, course title, dates, and status.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Test Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Assign course with due date and notes
            due_date = datetime.utcnow() + timedelta(days=30)
            service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER,
                due_date=due_date,
                notes="Complete this course",
                skill_id=skill.id
            )
            
            # Get assignments
            assignments = service.get_manager_assignments(manager.id)
            
            assert len(assignments) == 1
            assignment = assignments[0]
            
            # Verify all details are present
            assert assignment.employee_name == "Test Employee"
            assert assignment.course_title == "Python Basics"
            assert assignment.assigned_at is not None
            assert assignment.due_date is not None
            assert assignment.status == CourseStatusEnum.NOT_STARTED.value
            assert assignment.notes == "Complete this course"
            assert assignment.skill_name == "Python"



class TestCourseStatusTransitions:
    """
    **Feature: manager-template-assessment, Property 9: Course Status Transitions**
    **Validates: Requirements 6.3, 6.4**
    
    For any course assignment, status transitions should follow: 
    NOT_STARTED → IN_PROGRESS → COMPLETED. When transitioning to IN_PROGRESS, 
    started_at should be set. When transitioning to COMPLETED, completed_at should be set.
    """
    
    def test_valid_transition_not_started_to_in_progress(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3**
        
        NOT_STARTED → IN_PROGRESS should succeed and set started_at.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            assert assignment.status == CourseStatusEnum.NOT_STARTED
            assert assignment.started_at is None
            
            # Transition to IN_PROGRESS
            updated = service.update_assignment_status(
                assignment.id, 
                CourseStatusEnum.IN_PROGRESS.value
            )
            
            assert updated.status == CourseStatusEnum.IN_PROGRESS
            assert updated.started_at is not None
    
    def test_valid_transition_in_progress_to_completed(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.4**
        
        IN_PROGRESS → COMPLETED should succeed and set completed_at.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment and start it
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
            
            # Transition to COMPLETED
            updated = service.update_assignment_status(
                assignment.id,
                CourseStatusEnum.COMPLETED.value,
                certificate_url="https://example.com/cert/123"
            )
            
            assert updated.status == CourseStatusEnum.COMPLETED
            assert updated.completed_at is not None
            assert updated.certificate_url == "https://example.com/cert/123"
    
    def test_invalid_transition_not_started_to_completed(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3, 6.4**
        
        NOT_STARTED → COMPLETED should fail (must go through IN_PROGRESS).
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Try to skip to COMPLETED
            with pytest.raises(ValueError) as exc_info:
                service.update_assignment_status(
                    assignment.id,
                    CourseStatusEnum.COMPLETED.value
                )
            
            assert "invalid status transition" in str(exc_info.value).lower()
    
    def test_invalid_transition_completed_to_any(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3, 6.4**
        
        COMPLETED → any status should fail (completed is terminal).
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment and complete it
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
            service.update_assignment_status(assignment.id, CourseStatusEnum.COMPLETED.value)
            
            # Try to transition from COMPLETED
            with pytest.raises(ValueError) as exc_info:
                service.update_assignment_status(
                    assignment.id,
                    CourseStatusEnum.IN_PROGRESS.value
                )
            
            assert "invalid status transition" in str(exc_info.value).lower()
    
    def test_invalid_transition_in_progress_to_not_started(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3, 6.4**
        
        IN_PROGRESS → NOT_STARTED should fail (no backward transitions).
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment and start it
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
            
            # Try to go back to NOT_STARTED
            with pytest.raises(ValueError) as exc_info:
                service.update_assignment_status(
                    assignment.id,
                    CourseStatusEnum.NOT_STARTED.value
                )
            
            assert "invalid status transition" in str(exc_info.value).lower()
    
    @given(
        start_status=st.sampled_from([CourseStatusEnum.NOT_STARTED, CourseStatusEnum.IN_PROGRESS, CourseStatusEnum.COMPLETED]),
        target_status=st.sampled_from([CourseStatusEnum.NOT_STARTED, CourseStatusEnum.IN_PROGRESS, CourseStatusEnum.COMPLETED])
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_transition_validity_property(self, start_status, target_status):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3, 6.4**
        
        For any status pair, transition should succeed iff it follows the valid path.
        """
        # Define valid transitions
        valid_transitions = {
            CourseStatusEnum.NOT_STARTED: [CourseStatusEnum.IN_PROGRESS],
            CourseStatusEnum.IN_PROGRESS: [CourseStatusEnum.COMPLETED],
            CourseStatusEnum.COMPLETED: []
        }
        
        is_valid = target_status in valid_transitions.get(start_status, [])
        
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Get to start_status
            if start_status == CourseStatusEnum.IN_PROGRESS:
                service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
            elif start_status == CourseStatusEnum.COMPLETED:
                service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
                service.update_assignment_status(assignment.id, CourseStatusEnum.COMPLETED.value)
            
            # Attempt transition
            if is_valid:
                updated = service.update_assignment_status(assignment.id, target_status.value)
                assert updated.status == target_status
            else:
                with pytest.raises(ValueError):
                    service.update_assignment_status(assignment.id, target_status.value)
    
    def test_timestamps_set_correctly_on_transitions(self):
        """
        **Feature: manager-template-assessment, Property 9: Course Status Transitions**
        **Validates: Requirements 6.3, 6.4**
        
        started_at set on IN_PROGRESS, completed_at set on COMPLETED.
        """
        with create_test_db() as db:
            # Create manager and employee
            manager = create_employee(db, "MGR001", "Manager")
            employee = create_employee(db, "EMP001", "Employee", line_manager_id=manager.id)
            
            # Create skill and course
            skill = create_skill(db, "Python", "Programming")
            course = create_course(db, "Python Basics", skill_id=skill.id)
            db.commit()
            
            service = CourseAssignmentService(db)
            
            # Create assignment
            assignment = service.assign_course(
                course_id=course.id,
                employee_id=employee.id,
                assigned_by=manager.id,
                assigned_by_role_id=RoleID.LINE_MANAGER
            )
            
            # Initial state
            assert assignment.started_at is None
            assert assignment.completed_at is None
            
            # Start course
            started = service.update_assignment_status(assignment.id, CourseStatusEnum.IN_PROGRESS.value)
            assert started.started_at is not None
            assert started.completed_at is None
            
            started_time = started.started_at
            
            # Complete course
            completed = service.update_assignment_status(assignment.id, CourseStatusEnum.COMPLETED.value)
            assert completed.started_at == started_time  # Should not change
            assert completed.completed_at is not None
            assert completed.completed_at >= started_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

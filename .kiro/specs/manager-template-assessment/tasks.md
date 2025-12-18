# Implementation Plan

- [x] 1. Database Schema Updates





  - [x] 1.1 Create template_assessment_logs table migration


    - Create table with columns: id, template_id, employee_id, assessor_id, skills_assessed, total_skills, assessed_at
    - Add indexes for template_id, employee_id, assessor_id
    - _Requirements: 1.4_

  - [x] 1.2 Add skill_id column to course_assignments table

    - Add skill_id INTEGER REFERENCES skills(id) column
    - Add index on skill_id
    - _Requirements: 4.3_

  - [x] 1.3 Create SQLAlchemy model for TemplateAssessmentLog

    - Create model with relationships to SkillTemplate, Employee
    - _Requirements: 1.4_

-

- [x] 2. Template Assessment Service



  - [x] 2.1 Create TemplateAssessmentService class


    - Implement get_template_for_assessment() method
    - Parse template content JSON to extract skills
    - Match skills with employee's current assessments
    - Return TemplateAssessmentView with skills and current levels
    - _Requirements: 1.1, 1.2_
  - [x] 2.2 Write property test for template skills retrieval


    - **Property 1: Template Skills Retrieval**
    - **Validates: Requirements 1.1, 1.2**
  - [x] 2.3 Implement submit_template_assessment() method

    - Validate assessor authority using AuthorityValidator
    - Create/update skill_assessment records for each skill
    - Create template_assessment_log record
    - Return assessment results
    - _Requirements: 1.3, 1.4_

  - [x] 2.4 Write property test for template assessment completeness

    - **Property 2: Template Assessment Completeness**
    - **Validates: Requirements 1.3, 1.4**
  - [x] 2.5 Implement get_assessment_progress() method

    - Count assessed skills from template
    - Calculate percentage
    - _Requirements: 1.5_
  - [x] 2.6 Write property test for assessment progress calculation


    - **Property 3: Assessment Progress Calculation**
    - **Validates: Requirements 1.5**

- [x] 3. Course Assignment Service





  - [x] 3.1 Create CourseAssignmentService class


    - Implement get_courses_for_skill() method
    - Query courses by skill_id
    - Return list with full course details
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Write property test for course-skill association

    - **Property 4: Course-Skill Association**
    - **Validates: Requirements 2.1, 2.2, 4.1**
  - [x] 3.3 Implement assign_course() method

    - Validate manager authority using AuthorityValidator
    - Check for existing assignment (prevent duplicates)
    - Create CourseAssignment record with all fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.4 Write property test for course assignment authority

    - **Property 5: Course Assignment Authority**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 3.5 Write property test for course assignment idempotency

    - **Property 6: Course Assignment Idempotency**
    - **Validates: Requirements 3.4**
  - [x] 3.6 Implement get_manager_assignments() method

    - Query assignments by assigned_by
    - Support filtering by status, employee, course
    - Include employee and course details in response
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 3.7 Write property test for manager assignment filtering

    - **Property 8: Manager Assignment Filtering**
    - **Validates: Requirements 5.1, 5.2, 5.3**
  - [x] 3.8 Implement get_employee_assignments() method

    - Query assignments by employee_id
    - Include course and assigner details
    - _Requirements: 6.1, 6.2_

  - [x] 3.9 Implement update_assignment_status() method
    - Validate status transition
    - Update started_at or completed_at based on new status
    - Handle certificate_url for completion
    - _Requirements: 6.3, 6.4_
  - [x] 3.10 Write property test for course status transitions

    - **Property 9: Course Status Transitions**
    - **Validates: Requirements 6.3, 6.4**
-

- [x] 4. Checkpoint - Ensure all service tests pass




  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Template Assessment API Endpoints



  - [x] 5.1 Create GET /api/assessments/templates endpoint


    - Return list of available skill templates
    - Validate LM or DM role
    - _Requirements: 1.1_

  - [x] 5.2 Create GET /api/assessments/template/{template_id}/employee/{employee_id} endpoint
    - Validate manager authority
    - Call TemplateAssessmentService.get_template_for_assessment()
    - Return template skills with current levels
    - _Requirements: 1.2_

  - [x] 5.3 Create POST /api/assessments/template/{template_id}/employee/{employee_id} endpoint
    - Validate manager authority
    - Accept list of skill assessments
    - Call TemplateAssessmentService.submit_template_assessment()
    - Return results with progress

    - _Requirements: 1.3, 1.4_
  - [x] 5.4 Create GET /api/assessments/template/{template_id}/employee/{employee_id}/progress endpoint

    - Validate manager authority
    - Call TemplateAssessmentService.get_assessment_progress()
    - Return completion percentage
    - _Requirements: 1.5_

- [x] 6. Course Assignment API Endpoints



  - [x] 6.1 Create GET /api/courses endpoint


    - Support filtering by skill_id, mandatory, search
    - Return list of courses with details
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 6.2 Create GET /api/courses/skill/{skill_id} endpoint
    - Return courses for specific skill

    - _Requirements: 2.1, 4.2_
  - [x] 6.3 Create POST /api/courses/assign endpoint
    - Validate manager authority
    - Call CourseAssignmentService.assign_course()

    - Return created assignment
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 6.4 Create GET /api/courses/assignments/manager endpoint

    - Return assignments made by current manager
    - Support filtering by status, employee, course

    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 6.5 Create GET /api/courses/assignments/me endpoint
    - Return courses assigned to current user
    - _Requirements: 6.1, 6.2_
  - [x] 6.6 Create PUT /api/courses/assignments/{assignment_id}/status endpoint

    - Validate user can update (own assignment or manager)
    - Call CourseAssignmentService.update_assignment_status()
    - _Requirements: 6.3, 6.4_

- [x] 7. Checkpoint - Ensure all API tests pass





  - Ensure all tests pass, ask the user if questions arise.
-

- [x] 8. Frontend - Template Assessment Screen




  - [x] 8.1 Create TemplateAssessmentScreen component


    - Display list of available templates
    - Allow selection of template for assessment
    - _Requirements: 1.1_
  - [x] 8.2 Create TemplateSkillsForm component

    - Display all skills from template with current levels
    - Show required level from template
    - Provide dropdown to select new level for each skill
    - Include optional comments field
    - Submit button to save all assessments
    - _Requirements: 1.2, 1.3_
  - [x] 8.3 Add assessment progress indicator

    - Show completion percentage
    - Color-code assessed vs unassessed skills
    - _Requirements: 1.5_
-

- [x] 9. Frontend - Course Assignment Screen





  - [x] 9.1 Create CourseAssignmentScreen component

    - Display available courses with filters
    - Show course details (title, description, URL, mandatory)
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 9.2 Create AssignCourseModal component
    - Select employee from assessable employees
    - Set optional due date
    - Add optional notes
    - Submit assignment
    - _Requirements: 3.1, 3.3, 3.5_
  - [x] 9.3 Add course assignment from skill gap view


    - Show "Assign Course" button on skill gaps
    - Open modal with courses for that skill
    - Pre-fill skill_id for gap linkage
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 10. Frontend - Manager Course Dashboard





  - [x] 10.1 Create ManagerCourseAssignments component


    - Display all assignments made by manager
    - Show employee, course, dates, status
    - Support filtering by status, employee, course
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 10.2 Add to LMDashboard and DMDashboard


    - Add "Course Assignments" tab or section
    - Link to full assignments view
    - _Requirements: 5.1_
-

- [x] 11. Frontend - Employee Course View




  - [x] 11.1 Create EmployeeCourseAssignments component


    - Display courses assigned to employee
    - Show course details, assigner, dates, status
    - _Requirements: 6.1, 6.2_


  - [x] 11.2 Add course status update functionality
    - "Start Course" button to set In Progress
    - "Complete Course" button with certificate upload

    - _Requirements: 6.3, 6.4_
  - [x] 11.3 Add to EmployeeDashboard

    - Add "My Courses" section
    - Show pending and in-progress courses prominently
    - _Requirements: 6.1_

- [x] 12. Final Checkpoint - Full Integration Test





  - Ensure all tests pass, ask the user if questions arise.

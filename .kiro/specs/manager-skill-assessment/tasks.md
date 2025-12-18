# Implementation Plan

- [x] 1. Database Schema and Models





  - [x] 1.1 Create skill_assessments table migration


    - Create new table with columns: id, employee_id, skill_id, level, assessment_type, assessor_id, assessor_role, comments, assessed_at, created_at, updated_at
    - Add unique constraint on (employee_id, skill_id)


    - Add indexes for employee_id and assessor_id
    - _Requirements: 4.6, 5.2_


  - [x] 1.2 Create assessment_history table migration

    - Create immutable audit table with columns: id, employee_id, skill_id, previous_level, new_level, assessment_type, assessor_id, assessor_role, comments, assessed_at
    - Add indexes for employee_id, skill_id, and assessed_at DESC

    - _Requirements: 5.1, 5.2_

  - [x] 1.3 Create pathway_skills table migration

    - Create table with columns: id, pathway, skill_id, is_core, display_order

    - Add unique constraint on (pathway, skill_id)
    - Add index on pathway
    - _Requirements: 2.1_
  - [x] 1.4 Add pathway column to employees table

    - Add pathway VARCHAR(100) column
    - Add band_locked_at and pathway_locked_at timestamp columns
    - _Requirements: 1.1_


  - [x] 1.5 Create SQLAlchemy models for new tables


    - Create SkillAssessment model
    - Create AssessmentHistory model
    - Create PathwaySkill model

    - Update Employee model with pathway field
    - _Requirements: 2.1, 4.6, 5.1_
  - [x] 1.6 Write property test for baseline proficiency mapping


    - **Property 2: Baseline Proficiency Mapping**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

- [x] 2. Authority Validation Service


  - [x] 2.1 Create AuthorityValidator service class

    - Implement can_assess() method to check manager authority over employee


    - Check direct report relationship (line_manager_id)

    - Check project assignment relationship

    - Return tuple of (is_authorized, reason)
    - _Requirements: 4.4, 4.5_
  - [x] 2.2 Implement get_assessable_employees() method

    - Return list of employees the manager can assess
    - Include direct reports for Line Managers
    - Include location-based employees for Delivery Managers

    - Include project-assigned employees
    - _Requirements: 4.1, 4.2_
  - [x] 2.3 Write property test for manager authority validation


    - **Property 4: Manager Authority Validation**
    - **Validates: Requirements 4.4, 4.5, 7.1, 7.2**

- [x] 3. Baseline Assignment Service



  - [x] 3.1 Create BaselineService class with band-to-level mapping


    - Define BAND_BASELINE_MAP constant: A=Beginner, B=Developing, C=Intermediate, L1=Advanced, L2=Expert
    - Implement get_baseline_level() method
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6_
  - [x] 3.2 Implement assign_baseline() method

    - Get all skills for the pathway from pathway_skills table
    - Create SkillAssessment records with assessment_type='baseline'
    - Set assessor_role='SYSTEM' and assessor_id=None
    - Create corresponding AssessmentHistory records
    - Skip skills that already have assessments (for pathway changes)

    - _Requirements: 2.1, 2.7, 2.8_
  - [x] 3.3 Implement get_pathway_skills() method

    - Query pathway_skills table for given pathway
    - Return list of Skill objects with is_core flag
    - _Requirements: 2.1_
  - [x] 3.4 Write property test for baseline assignment

    - **Property 2: Baseline Proficiency Mapping**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

- [x] 4. Assessment Service


  - [x] 4.1 Create AssessmentService class



    - Implement create_assessment() method

    - Validate assessor authority using AuthorityValidator
    - Create or update SkillAssessment record
    - Capture previous level before update
    - Create AssessmentHistory record

    - _Requirements: 4.6, 4.7_
  - [x] 4.2 Implement get_employee_assessments() method

    - Query all assessments for employee
    - Join with skills table for skill details
    - Include assessor name and role
    - Optionally calculate gaps vs next band
    - _Requirements: 3.1, 4.3_
  - [x] 4.3 Implement get_assessment_history() method

    - Query assessment_history table
    - Filter by employee_id and optionally skill_id
    - Order by assessed_at DESC
    - _Requirements: 5.3_
  - [x] 4.4 Write property test for assessment history immutability


    - **Property 5: Assessment History Immutability**
    - **Validates: Requirements 5.1, 5.2, 5.5**
  - [x] 4.5 Write property test for assessment history completeness

    - **Property 6: Assessment History Completeness**
    - **Validates: Requirements 5.2, 4.7**

- [x] 5. Readiness Calculator Service


  - [x] 5.1 Create ReadinessCalculator class

    - Implement calculate_readiness() method
    - Get employee's current assessments
    - Get target band requirements from role_requirements table
    - Calculate percentage of requirements met
    - Return ReadinessResult with score, gaps, and met requirements
    - _Requirements: 6.1, 6.2, 6.5_
  - [x] 5.2 Implement get_skill_gaps() method

    - Compare current assessment levels vs target band requirements
    - Return list of SkillGap objects with skill_id, current_level, required_level, gap_value


    - _Requirements: 3.4_

  - [x] 5.3 Write property test for readiness score calculation


    - **Property 7: Readiness Score Calculation**
    - **Validates: Requirements 6.1, 6.2, 6.5**

- [x] 6. Checkpoint - Ensure all service tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Band/Pathway Immutability Enforcement


  - [x] 7.1 Create middleware to intercept band/pathway modifications

    - Check all PUT/PATCH requests to employee endpoints

    - If band or pathway field is being modified, check if request is from Level Movement service
    - Reject unauthorized modifications with HTTP 403
    - _Requirements: 1.2, 1.3_
  - [x] 7.2 Update employee update endpoints to enforce immutability

    - Modify existing employee update APIs


    - Strip band and pathway from request body unless authorized
    - Return error message explaining Level Movement requirement
    - _Requirements: 1.2, 1.3_
  - [x] 7.3 Create internal method for Level Movement to update band

    - Create _update_band_via_level_movement() internal method
    - Only callable from LevelMovementService
    - Update band and trigger baseline assignment for new pathway skills
    - _Requirements: 1.4, 6.4_
  - [x] 7.4 Write property test for band/pathway immutability

    - **Property 1: Band and Pathway Immutability**
    - **Validates: Requirements 1.2, 1.3, 1.5**

- [x] 8. Assessment API Endpoints


  - [x] 8.1 Create POST /api/assessments/employee/{employee_id}/skill/{skill_id} endpoint

    - Accept level and optional comments in request body
    - Validate JWT token and extract user role
    - Verify role is LM (5) or DM (4)
    - Call AuthorityValidator.can_assess()
    - Call AssessmentService.create_assessment()
    - Return created/updated assessment
    - _Requirements: 4.4, 4.5, 4.6, 7.1, 7.2_
  - [x] 8.2 Create GET /api/assessments/employee/{employee_id} endpoint

    - Validate JWT token
    - Enforce role-based access: employee sees own, manager sees reports, HR sees all
    - Call AssessmentService.get_employee_assessments()
    - Return list of assessments with skill details
    - _Requirements: 3.1, 5.4_
  - [x] 8.3 Create GET /api/assessments/employee/{employee_id}/history endpoint

    - Validate JWT token
    - Enforce same role-based access as 8.2
    - Call AssessmentService.get_assessment_history()
    - Return ordered list of historical assessments
    - _Requirements: 5.3, 5.4_
  - [x] 8.4 Create GET /api/assessments/assessable-employees endpoint

    - Validate JWT token and verify LM or DM role
    - Call AuthorityValidator.get_assessable_employees()
    - Return list of employees with basic info
    - _Requirements: 4.1, 4.2_
  - [x] 8.5 Write property test for manager authority on assessment endpoints

    - **Property 4: Manager Authority Validation**
    - **Validates: Requirements 4.4, 4.5, 7.1, 7.2**

- [x] 9. Employee Skill Board API (Read-Only)


  - [x] 9.1 Create GET /api/skill-board/me endpoint

    - Return read-only skill board for current user
    - Include all assessments with assessor info
    - Include band and pathway (marked as locked)
    - Include skill gaps vs next band
    - Include readiness score
    - _Requirements: 3.1, 3.4, 3.5_
  - [x] 9.2 Create GET /api/skill-board/me/readiness endpoint

    - Calculate and return readiness score for next band
    - Include detailed gap analysis
    - Include list of skills meeting/not meeting requirements
    - _Requirements: 6.1, 6.5_
  - [x] 9.3 Deprecate legacy self-service endpoints

    - Update POST /api/user-skills/me to return HTTP 410 Gone
    - Update PUT /api/user-skills/me/{id} to return HTTP 410 Gone
    - Update DELETE /api/user-skills/me/{id} to return HTTP 410 Gone
    - Include message: "Self-service skill editing has been disabled"
    - _Requirements: 7.4_
  - [x] 9.4 Write property test for employee cannot modify skills

    - **Property 3: Employee Cannot Modify Skills**
    - **Validates: Requirements 3.6, 7.4**

- [x] 10. Checkpoint - Ensure all API tests pass

  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Audit Logging


  - [x] 11.1 Create audit logging for assessment operations

    - Log all assessment create/update operations
    - Capture user_id, target_employee_id, skill_id, action, timestamp
    - _Requirements: 5.6_
  - [x] 11.2 Create audit logging for unauthorized access attempts

    - Log all HTTP 403 responses on assessment endpoints
    - Capture user_id, endpoint, timestamp, IP address, reason
    - _Requirements: 7.3_
  - [x] 11.3 Create audit logging for data exports

    - Log all assessment data export operations
    - Capture user_id, export_scope, timestamp, format
    - _Requirements: 5.6_
  - [x] 11.4 Write property test for unauthorized access logging

    - **Property 9: Unauthorized Access Logging**
    - **Validates: Requirements 7.3**

- [x] 12. Level Movement Integration


  - [x] 12.1 Update Level Movement request creation to include readiness score

    - Calculate readiness_score when request is created
    - Store readiness_score in level_movement_requests table
    - Display warning if readiness_score < 70%
    - _Requirements: 6.2, 6.3_
  - [x] 12.2 Update Level Movement approval to trigger band update and baseline

    - When all approvals complete, call _update_band_via_level_movement()
    - Update employee band to requested_level
    - Call BaselineService.assign_baseline() for new pathway skills
    - _Requirements: 1.4, 6.4_
  - [x] 12.3 Write property test for Level Movement band update

    - **Property 8: Level Movement Band Update**
    - **Validates: Requirements 1.4, 6.4**

- [x] 13. Frontend - Employee Skill Board (Read-Only)


  - [x] 13.1 Create EmployeeSkillBoardReadOnly component

    - Display all assessed skills with proficiency levels
    - Show assessor name and assessment date for each skill
    - Display "Manager Assessed" or "System Baseline" labels
    - Remove all edit controls, drag-and-drop, rating buttons
    - _Requirements: 3.1, 3.2, 3.7_
  - [x] 13.2 Add locked band/pathway display

    - Show band and pathway with lock icons
    - Display tooltip explaining Level Movement requirement
    - _Requirements: 1.1, 3.3_
  - [x] 13.3 Add skill gaps and readiness display

    - Show gaps compared to next band requirements
    - Display readiness percentage with progress bar
    - Color-code skills: green (meets), yellow (close), red (gap)
    - _Requirements: 3.4, 3.5_
  - [x] 13.4 Write property test for assessment label accuracy

    - **Property 10: Assessment Label Accuracy**
    - **Validates: Requirements 3.7**

- [x] 14. Frontend - Manager Assessment Screen


  - [x] 14.1 Create ManagerAssessmentScreen component

    - Display list of assessable employees from API
    - Allow selection of employee to assess
    - _Requirements: 4.1, 4.2_
  - [x] 14.2 Create SkillAssessmentForm component

    - Display all skills in employee's pathway
    - Show current assessment level for each skill
    - Provide dropdown to select new level
    - Include optional comments field
    - Submit button to save assessment
    - _Requirements: 4.3, 4.6_
  - [x] 14.3 Add assessment history view

    - Display history of assessments for selected employee
    - Show previous level, new level, assessor, date
    - _Requirements: 5.3_
  - [x] 14.4 Add error handling for unauthorized assessments

    - Display clear error message if assessment is rejected
    - Explain why manager lacks authority
    - _Requirements: 4.5_

- [x] 15. Frontend - Update Existing Components


  - [x] 15.1 Update EmployeeDashboard to use read-only skill board

    - Replace existing skill editing components with EmployeeSkillBoardReadOnly
    - Remove "Edit Skills" button
    - Add link to view assessment history
    - _Requirements: 3.2_
  - [x] 15.2 Update LMDashboard to include assessment functionality

    - Add "Assess Skills" button for each direct report
    - Link to ManagerAssessmentScreen
    - _Requirements: 4.1_
  - [x] 15.3 Update DMDashboard to include assessment functionality

    - Add "Assess Skills" button for location employees
    - Link to ManagerAssessmentScreen
    - _Requirements: 4.2_
  - [x] 15.4 Update navigation and routing

    - Add route for /assess/:employeeId
    - Update role-based navigation to show assessment options for LM/DM
    - Hide skill editing routes for employees
    - _Requirements: 4.1, 4.2_

- [x] 16. Data Migration


  - [x] 16.1 Create migration script for existing employee_skills data

    - Copy existing employee_skills to skill_assessments
    - Set assessment_type='legacy' for migrated records
    - Set assessor_role='LEGACY_SELF_REPORTED'
    - Create corresponding assessment_history records
    - _Requirements: 5.1_
  - [x] 16.2 Create script to assign pathways to existing employees

    - Map existing category/team to pathway
    - Update employees.pathway column
    - _Requirements: 2.1_
  - [x] 16.3 Create script to generate baseline assessments for employees without assessments

    - Identify employees with pathway but no assessments
    - Call BaselineService.assign_baseline() for each
    - _Requirements: 2.1, 2.7_

- [x] 17. Final Checkpoint - Full Integration Test



  - Ensure all tests pass, ask the user if questions arise.


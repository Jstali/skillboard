# Requirements Document

## Introduction

This document specifies the requirements for enabling Line Managers and Delivery Managers to assess employee skills using skill templates and assign learning courses to employees. This extends the existing Manager-Driven Skill Assessment model by adding template-based assessment workflows and course assignment capabilities.

## Glossary

- **Skill Template**: A predefined spreadsheet-based template containing a list of skills with required proficiency levels
- **Template Assessment**: A manager's evaluation of an employee against all skills defined in a template
- **Course**: A learning resource (internal or external) that can be assigned to employees to improve specific skills
- **Course Assignment**: The assignment of a course to an employee by a manager with optional due date
- **Assessor**: A Line Manager or Delivery Manager authorized to assess employee skills and assign courses
- **Skill Gap**: The difference between an employee's current skill level and the required level

## Requirements

### Requirement 1: Template-Based Skill Assessment

**User Story:** As a Line Manager or Delivery Manager, I want to assess employee skills using a predefined template, so that I can efficiently evaluate all required skills in a structured manner.

#### Acceptance Criteria

1. WHEN a manager views an employee's assessment page THEN the system SHALL display a list of available skill templates
2. WHEN a manager selects a template for assessment THEN the system SHALL display all skills from the template with current employee levels and required levels
3. WHEN a manager submits assessments for template skills THEN the system SHALL create or update skill assessments for each skill in the template
4. WHEN a template assessment is submitted THEN the system SHALL record the template_id, assessor_id, and timestamp for audit purposes
5. WHEN a manager views template assessment progress THEN the system SHALL show completion percentage (skills assessed / total template skills)

### Requirement 2: Course Listing for Managers

**User Story:** As a Line Manager or Delivery Manager, I want to view available courses for each skill, so that I can recommend appropriate learning resources to my team members.

#### Acceptance Criteria

1. WHEN a manager views an employee's skill assessment THEN the system SHALL display available courses for each skill
2. WHEN courses are displayed THEN the system SHALL show course title, description, external URL, and mandatory flag
3. WHEN a skill has no associated courses THEN the system SHALL display "No courses available" message
4. WHEN a manager filters courses THEN the system SHALL support filtering by skill, mandatory status, and search term

### Requirement 3: Course Assignment by Managers

**User Story:** As a Line Manager or Delivery Manager, I want to assign courses to employees I supervise, so that they can improve their skills in identified gap areas.

#### Acceptance Criteria

1. WHEN a manager selects a course to assign THEN the system SHALL validate the manager has authority over the target employee
2. IF a manager attempts to assign a course to an employee they do not supervise THEN the system SHALL reject the request with HTTP 403
3. WHEN a manager assigns a course THEN the system SHALL create a CourseAssignment record with assigned_by, assigned_at, and optional due_date
4. WHEN a course is already assigned to an employee THEN the system SHALL display "Already assigned" and prevent duplicate assignment
5. WHEN a manager assigns a course THEN the system SHALL optionally allow adding notes explaining why the course was assigned

### Requirement 4: Course Assignment from Skill Gap Analysis

**User Story:** As a Line Manager or Delivery Manager, I want to assign courses directly from the skill gap analysis view, so that I can quickly address identified skill gaps.

#### Acceptance Criteria

1. WHEN a manager views an employee's skill gaps THEN the system SHALL display suggested courses for each gap
2. WHEN a manager clicks "Assign Course" on a skill gap THEN the system SHALL show available courses for that skill
3. WHEN a course is assigned from gap analysis THEN the system SHALL link the assignment to the specific skill gap
4. WHEN viewing assigned courses THEN the system SHALL indicate which courses were assigned to address specific skill gaps

### Requirement 5: Manager Course Assignment Dashboard

**User Story:** As a Line Manager or Delivery Manager, I want to view all course assignments I've made, so that I can track learning progress of my team.

#### Acceptance Criteria

1. WHEN a manager views their dashboard THEN the system SHALL display a summary of course assignments they've made
2. WHEN viewing course assignments THEN the system SHALL show employee name, course title, assigned date, due date, and status
3. WHEN filtering assignments THEN the system SHALL support filtering by status (Not Started, In Progress, Completed), employee, and course
4. WHEN an employee completes a course THEN the system SHALL update the status and notify the assigning manager

### Requirement 6: Employee Course View

**User Story:** As an employee, I want to view courses assigned to me by my manager, so that I can complete required learning.

#### Acceptance Criteria

1. WHEN an employee views their dashboard THEN the system SHALL display all courses assigned to them
2. WHEN viewing assigned courses THEN the system SHALL show course title, assigning manager, assigned date, due date, and status
3. WHEN an employee starts a course THEN the system SHALL update status to "In Progress" and record started_at timestamp
4. WHEN an employee completes a course THEN the system SHALL allow uploading a certificate and updating status to "Completed"

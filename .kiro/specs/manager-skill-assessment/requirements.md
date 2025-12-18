# Requirements Document

## Introduction

This document specifies the requirements for implementing a **Manager-Driven Skill Assessment Model** in the Skillboard application. This model fundamentally changes how skills are managed: employees can no longer self-rate their skills. Instead, only Line Managers and Delivery Managers can assess employee skills. Employee band and pathway are fixed and can only change through the formal Level Movement workflow.

The system enforces governance, auditability, and fairness by treating skills as evaluated assessments rather than self-declared claims. The Skill Board becomes an input to promotion decisions, not a promotion engine itself.

## Glossary

- **Band**: Career level designation (A, B, C, L1, L2) representing seniority and expected competency
- **Pathway**: Career track defining the skill domain (Technical, SAP, Cloud, Data, etc.)
- **Baseline Assessment**: System-generated initial skill levels assigned when an employee is given a Band + Pathway combination
- **Skill Assessment**: A manager's evaluation of an employee's proficiency in a specific skill
- **Assessor**: A Line Manager or Delivery Manager authorized to assess employee skills
- **Direct Report**: An employee whose line_manager_id points to the assessor
- **Project Assignment**: An employee assigned to a project managed by the assessor
- **Level Movement**: Formal workflow for changing an employee's band (promotion/demotion)
- **Readiness Score**: Calculated metric indicating how prepared an employee is for the next band level

## Requirements

### Requirement 1: Band and Pathway Immutability

**User Story:** As a system administrator, I want employee band and pathway to be immutable through normal operations, so that career progression follows formal governance processes.

#### Acceptance Criteria

1. WHEN an employee record is displayed THEN the system SHALL show band and pathway as read-only fields with visual lock indicators
2. WHEN any API request attempts to modify an employee's band directly THEN the system SHALL reject the request with HTTP 403 and error message "Band can only be changed via Level Movement workflow"
3. WHEN any API request attempts to modify an employee's pathway directly THEN the system SHALL reject the request with HTTP 403 and error message "Pathway can only be changed via Level Movement workflow"
4. WHEN a Level Movement request is approved by all required approvers THEN the system SHALL update the employee's band to the requested level
5. WHEN a skill assessment is submitted THEN the system SHALL NOT automatically change the employee's band or pathway regardless of the new skill level

### Requirement 2: Baseline Skill Assignment

**User Story:** As an HR administrator, I want the system to automatically assign baseline skill levels when an employee is given a Band + Pathway, so that all employees start with a consistent foundation.

#### Acceptance Criteria

1. WHEN an employee is assigned a Band and Pathway combination THEN the system SHALL automatically create skill assessments for all skills in that pathway
2. WHEN baseline skills are assigned for Band A THEN the system SHALL set all pathway skills to "Beginner" proficiency level
3. WHEN baseline skills are assigned for Band B THEN the system SHALL set all pathway skills to "Developing" proficiency level
4. WHEN baseline skills are assigned for Band C THEN the system SHALL set all pathway skills to "Intermediate" proficiency level
5. WHEN baseline skills are assigned for Band L1 THEN the system SHALL set all pathway skills to "Advanced" proficiency level
6. WHEN baseline skills are assigned for Band L2 THEN the system SHALL set all pathway skills to "Expert" proficiency level
7. WHEN a baseline assessment is created THEN the system SHALL record "SYSTEM" as the assessor_id, the current timestamp, and assessment_type as "baseline"
8. WHEN an employee already has assessed skills and their pathway changes via Level Movement THEN the system SHALL preserve existing assessments and add new baseline assessments only for skills not previously assessed

### Requirement 3: Employee Skill Board Read-Only Access

**User Story:** As an employee, I want to view my assessed skills and understand my gaps, so that I can prepare for career advancement without being able to manipulate my own ratings.

#### Acceptance Criteria

1. WHEN an employee views their skill board THEN the system SHALL display all assessed skills with proficiency levels, assessor name, and assessment date
2. WHEN an employee views their skill board THEN the system SHALL NOT display any edit controls, drag-and-drop interfaces, or rating change buttons
3. WHEN an employee views their skill board THEN the system SHALL display their band and pathway as locked fields with visual indicators
4. WHEN an employee views their skill board THEN the system SHALL display skill gaps compared to the next band's requirements
5. WHEN an employee views their skill board THEN the system SHALL display a readiness indicator showing percentage completion toward next band
6. WHEN an employee attempts to call any skill modification API endpoint THEN the system SHALL reject the request with HTTP 403 and message "Employees cannot modify skill assessments"
7. WHEN an employee views a skill THEN the system SHALL clearly label it as "Manager Assessed" or "System Baseline" based on assessment_type

### Requirement 4: Manager Skill Assessment Authority

**User Story:** As a Line Manager or Delivery Manager, I want to assess skills for employees I supervise, so that skill evaluations reflect actual observed competency.

#### Acceptance Criteria

1. WHEN a Line Manager views their dashboard THEN the system SHALL display a list of assessable employees including direct reports and project-assigned employees
2. WHEN a Delivery Manager views their dashboard THEN the system SHALL display a list of assessable employees in their location or assigned projects
3. WHEN a manager selects an employee to assess THEN the system SHALL display all skills in the employee's pathway with current assessment levels
4. WHEN a manager submits a skill assessment THEN the system SHALL validate that the manager has authority over the employee (direct report OR project assignment)
5. IF a manager attempts to assess an employee they do not supervise THEN the system SHALL reject the request with HTTP 403 and message "You do not have assessment authority over this employee"
6. WHEN a manager submits a valid skill assessment THEN the system SHALL record the new level, assessor_id, assessor_role, timestamp, and optional comments
7. WHEN a manager submits an assessment THEN the system SHALL preserve the previous assessment in the history table before updating the current level

### Requirement 5: Assessment History and Audit Trail

**User Story:** As a compliance officer, I want complete audit trails of all skill assessments, so that the organization maintains GDPR compliance and can investigate disputes.

#### Acceptance Criteria

1. WHEN any skill assessment is created or modified THEN the system SHALL create an immutable record in the assessment_history table
2. WHEN an assessment history record is created THEN the system SHALL capture: employee_id, skill_id, previous_level, new_level, assessor_id, assessor_role, timestamp, assessment_type, and comments
3. WHEN a user requests assessment history for an employee THEN the system SHALL return all historical assessments ordered by timestamp descending
4. WHEN assessment history is queried THEN the system SHALL enforce role-based access: employees see only their own history, managers see their direct reports, HR sees all
5. WHEN an attempt is made to modify or delete an assessment_history record THEN the system SHALL reject the operation with HTTP 403 and message "Assessment history is immutable"
6. WHEN assessment data is exported THEN the system SHALL log the export action with user_id, timestamp, and data scope for GDPR compliance

### Requirement 6: Level Movement Integration

**User Story:** As an employee, I want my skill assessments to inform my promotion readiness, so that I understand what I need to achieve for career advancement.

#### Acceptance Criteria

1. WHEN an employee views their skill board THEN the system SHALL calculate and display readiness_score as percentage of next-band requirements met
2. WHEN a Level Movement request is created THEN the system SHALL automatically calculate readiness_score based on current assessed skills vs target band requirements
3. WHEN a Level Movement request is submitted with readiness_score below 70% THEN the system SHALL display a warning but allow submission
4. WHEN a Level Movement request is approved THEN the system SHALL update the employee's band and trigger baseline assessment for any new pathway skills
5. WHEN calculating readiness_score THEN the system SHALL compare each assessed skill level against the required level for the target band and compute weighted average

### Requirement 7: API Authorization Enforcement

**User Story:** As a security architect, I want all skill-related APIs to enforce strict authorization, so that the assessment model cannot be bypassed.

#### Acceptance Criteria

1. WHEN any request is made to POST/PUT/DELETE on /api/user-skills/* endpoints THEN the system SHALL verify the requester has role_id 4 (DM) or 5 (LM)
2. WHEN a manager role is verified THEN the system SHALL additionally verify the target employee is within the manager's authority scope
3. WHEN an unauthorized request is detected THEN the system SHALL log the attempt with user_id, endpoint, timestamp, and IP address
4. WHEN the legacy employee skill self-service endpoints are called THEN the system SHALL return HTTP 410 Gone with message "Self-service skill editing has been disabled"
5. WHEN a new assessment API endpoint is called THEN the system SHALL require valid JWT token with appropriate role claims


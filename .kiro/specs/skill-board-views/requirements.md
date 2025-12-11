# Skill Board Views & Capability Metrics Requirements

## Introduction

This specification addresses the Skill Board user interface and capability metrics features that enable employees, capability partners, HR users, and managers to view skill information, proficiency levels, and aggregate capability metrics. The system explicitly excludes financial data while supporting reconciliation use cases for assignment tracking.

## Glossary

- **Skill Board**: The primary interface for viewing and managing employee skills and proficiency levels
- **Capability View**: Aggregate view of skill distributions across capability areas
- **Proficiency Level**: Rating of skill competency (Beginner, Developing, Intermediate, Advanced, Expert)
- **Capability Alignment**: How an employee's skills match their capability area requirements
- **Capability Partner (CP)**: Leader responsible for managing a specific capability area
- **Aggregate Metrics**: Statistical summaries of skill data without personal identifiers
- **Reconciliation**: Comparing where employees are assigned vs HR/delivery reports
- **Employee_System**: The skill board application
- **Metrics_System**: The component that calculates and displays capability metrics

## Requirements

### Requirement 1: Employee Skill Board Overview

**User Story:** As an Employee, I want to see my skills, proficiency levels, and capability alignment, so that I understand how I fit into the organisation's capability view.

#### Acceptance Criteria

1. WHEN an employee accesses their skill board, THE Employee_System SHALL display all assigned skills with current proficiency levels
2. WHEN skills are displayed, THE Employee_System SHALL show proficiency as visual indicators (Beginner through Expert)
3. WHEN capability alignment is calculated, THE Employee_System SHALL compare employee skills against capability requirements
4. WHEN skill gaps exist, THE Employee_System SHALL highlight areas where proficiency is below capability requirements
5. WHEN an employee views their profile, THE Employee_System SHALL display their home capability and team assignment

### Requirement 2: Capability View for CPs and HR

**User Story:** As a Capability Partner or HR User, I want to view aggregate skill distributions and capability metrics, so that I can plan hiring, training and allocation based on skill gaps.

#### Acceptance Criteria

1. WHEN a CP accesses capability view, THE Metrics_System SHALL display aggregate skill distribution for their capability area
2. WHEN HR users access capability view, THE Metrics_System SHALL display organisation-wide skill distributions
3. WHEN skill gaps are identified, THE Metrics_System SHALL highlight capability areas with insufficient coverage
4. WHEN training needs are assessed, THE Metrics_System SHALL provide skill gap analysis by capability area
5. WHEN allocation planning is performed, THE Metrics_System SHALL show available skills by proficiency level

### Requirement 3: Financial Data Exclusion

**User Story:** As a Product Owner, I want the Skill Board to explicitly exclude billing and financial information (unbilled, revenue, etc.), so that the system stays aligned to skills/capability use cases and avoids scope creep.

#### Acceptance Criteria

1. WHEN any data query is executed, THE Employee_System SHALL exclude billing rate information from results
2. WHEN any data query is executed, THE Employee_System SHALL exclude revenue information from results
3. WHEN any data query is executed, THE Employee_System SHALL exclude cost information from results
4. WHEN reports are generated, THE Employee_System SHALL focus exclusively on skills and capability data
5. WHEN data models are extended, THE Employee_System SHALL reject fields related to financial metrics

### Requirement 4: Reconciliation Support Without Financials

**User Story:** As a Product Owner, I want to allow the skill board to be used as a reference to reconcile where people are actually assigned (vs HR / delivery reports), so that the tool can support reconciliation without becoming a financial reporting system.

#### Acceptance Criteria

1. WHEN reconciliation is performed, THE Employee_System SHALL compare skill board assignments with HRMS data
2. WHEN assignment mismatches are detected, THE Employee_System SHALL highlight discrepancies for investigation
3. WHEN reconciliation reports are generated, THE Employee_System SHALL exclude all financial metrics
4. WHEN assignment status is displayed, THE Employee_System SHALL show project names and allocation percentages only
5. WHEN reconciliation data is exported, THE Employee_System SHALL filter out any financial fields

### Requirement 5: General Capability Metrics for Wider Audience

**User Story:** As a Manager/CP, I want to see high-level, non-sensitive capability metrics (counts, distribution, etc.), so that I can understand capability strength without seeing personal/sensitive details.

#### Acceptance Criteria

1. WHEN managers access metrics, THE Metrics_System SHALL display skill counts by proficiency level
2. WHEN capability distribution is shown, THE Metrics_System SHALL aggregate data without personal identifiers
3. WHEN skill coverage is displayed, THE Metrics_System SHALL show percentage of capability requirements met
4. WHEN trend data is requested, THE Metrics_System SHALL show skill growth over time without individual details
5. WHEN metrics are filtered, THE Metrics_System SHALL allow filtering by capability area and team

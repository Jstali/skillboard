# Design Document: Manager Template Assessment & Course Assignment

## Overview

This design extends the Manager-Driven Skill Assessment model to support template-based assessments and course assignments. Managers can assess employees using predefined skill templates and assign learning courses to address skill gaps.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  Template Assessment  │  Course Assignment  │  Employee Course View  │
│  Screen               │  Screen             │  (Read-Only)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Layer                                    │
├─────────────────────────────────────────────────────────────────────┤
│  /api/assessments/template/*  │  /api/courses/assign/*              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer                                │
├─────────────────────────────────────────────────────────────────────┤
│  TemplateAssessmentService  │  CourseAssignmentService              │
│  AuthorityValidator (reuse) │  SkillCourseMapper                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                   │
├─────────────────────────────────────────────────────────────────────┤
│  skill_templates  │  course_assignments  │  courses                  │
│  skill_assessments│  template_assessment_logs                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. TemplateAssessmentService

Handles template-based skill assessments.

```python
class TemplateAssessmentService:
    def get_template_for_assessment(
        self,
        template_id: int,
        employee_id: int
    ) -> TemplateAssessmentView:
        """Get template skills with employee's current levels."""
        
    def submit_template_assessment(
        self,
        template_id: int,
        employee_id: int,
        assessor_id: int,
        assessments: List[SkillAssessmentInput]
    ) -> TemplateAssessmentResult:
        """Submit assessments for all skills in template."""
        
    def get_assessment_progress(
        self,
        template_id: int,
        employee_id: int
    ) -> AssessmentProgress:
        """Get completion percentage for template assessment."""
```

### 2. CourseAssignmentService

Handles course assignments by managers.

```python
class CourseAssignmentService:
    def get_courses_for_skill(
        self,
        skill_id: int
    ) -> List[Course]:
        """Get available courses for a skill."""
        
    def assign_course(
        self,
        course_id: int,
        employee_id: int,
        assigned_by: int,
        due_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        skill_id: Optional[int] = None
    ) -> CourseAssignment:
        """Assign a course to an employee."""
        
    def get_manager_assignments(
        self,
        manager_id: int,
        status_filter: Optional[str] = None
    ) -> List[CourseAssignmentWithDetails]:
        """Get all course assignments made by a manager."""
        
    def get_employee_assignments(
        self,
        employee_id: int
    ) -> List[CourseAssignmentWithDetails]:
        """Get all courses assigned to an employee."""
        
    def update_assignment_status(
        self,
        assignment_id: int,
        status: CourseStatusEnum,
        certificate_url: Optional[str] = None
    ) -> CourseAssignment:
        """Update course assignment status."""
```

### 3. API Endpoints

#### Template Assessment Endpoints

```
GET    /api/assessments/templates
       Auth: LM or DM
       Returns: List of available skill templates
       
GET    /api/assessments/template/{template_id}/employee/{employee_id}
       Auth: LM or DM with authority over employee
       Returns: Template skills with current employee levels
       
POST   /api/assessments/template/{template_id}/employee/{employee_id}
       Auth: LM or DM with authority over employee
       Body: { assessments: [{ skill_id, level, comments? }] }
       Returns: Assessment results with progress
       
GET    /api/assessments/template/{template_id}/employee/{employee_id}/progress
       Auth: LM or DM with authority over employee
       Returns: Completion percentage and assessed skills count
```

#### Course Assignment Endpoints

```
GET    /api/courses
       Auth: Any authenticated user
       Query: skill_id?, mandatory?, search?
       Returns: List of courses with filters
       
GET    /api/courses/skill/{skill_id}
       Auth: Any authenticated user
       Returns: Courses for specific skill
       
POST   /api/courses/assign
       Auth: LM or DM with authority over employee
       Body: { course_id, employee_id, due_date?, notes?, skill_id? }
       Returns: Created assignment
       
GET    /api/courses/assignments/manager
       Auth: LM or DM
       Query: status?, employee_id?, course_id?
       Returns: Assignments made by current manager
       
GET    /api/courses/assignments/me
       Auth: Any authenticated user
       Returns: Courses assigned to current user
       
PUT    /api/courses/assignments/{assignment_id}/status
       Auth: Employee (own) or Manager
       Body: { status, certificate_url? }
       Returns: Updated assignment
```

## Data Models

### New Tables

#### template_assessment_logs (audit trail for template assessments)

```sql
CREATE TABLE template_assessment_logs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES skill_templates(id),
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    assessor_id INTEGER NOT NULL REFERENCES employees(id),
    skills_assessed INTEGER NOT NULL,
    total_skills INTEGER NOT NULL,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_template_assessment_logs_template ON template_assessment_logs(template_id);
CREATE INDEX idx_template_assessment_logs_employee ON template_assessment_logs(employee_id);
CREATE INDEX idx_template_assessment_logs_assessor ON template_assessment_logs(assessor_id);
```

### Modified Tables

#### course_assignments (add skill_id for gap linkage)

```sql
ALTER TABLE course_assignments 
ADD COLUMN skill_id INTEGER REFERENCES skills(id);

COMMENT ON COLUMN course_assignments.skill_id IS 'Skill this course was assigned to address (for gap analysis linkage)';
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Template Skills Retrieval
*For any* skill template T and employee E, when a manager requests template assessment view, the system should return all skills defined in T with E's current assessment levels (or null if not assessed).
**Validates: Requirements 1.1, 1.2**

### Property 2: Template Assessment Completeness
*For any* template assessment submission with N skill assessments, the system should create or update exactly N skill_assessment records and create one template_assessment_log record.
**Validates: Requirements 1.3, 1.4**

### Property 3: Assessment Progress Calculation
*For any* template T with N skills and employee E with M assessed skills from T, the progress percentage should equal (M / N) * 100.
**Validates: Requirements 1.5**

### Property 4: Course-Skill Association
*For any* skill S with associated courses, querying courses for S should return all courses where course.skill_id = S.id, with complete course details (title, description, external_url, is_mandatory).
**Validates: Requirements 2.1, 2.2, 4.1**

### Property 5: Course Assignment Authority
*For any* course assignment request by manager M for employee E, the assignment should succeed only if AuthorityValidator.can_assess(M, E) returns true. Otherwise, HTTP 403 should be returned.
**Validates: Requirements 3.1, 3.2**

### Property 6: Course Assignment Idempotency
*For any* course C and employee E, attempting to assign C to E when an assignment already exists should not create a duplicate record and should return an appropriate error message.
**Validates: Requirements 3.4**

### Property 7: Course Assignment Record Completeness
*For any* successful course assignment, the CourseAssignment record should contain: course_id (not null), employee_id (not null), assigned_by (not null), assigned_at (not null), and optionally due_date, notes, and skill_id.
**Validates: Requirements 3.3, 3.5, 4.3**

### Property 8: Manager Assignment Filtering
*For any* manager M, querying their assignments should return only CourseAssignment records where assigned_by = M.employee_id, with correct filtering by status, employee, and course when specified.
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 9: Course Status Transitions
*For any* course assignment, status transitions should follow: NOT_STARTED → IN_PROGRESS → COMPLETED. When transitioning to IN_PROGRESS, started_at should be set. When transitioning to COMPLETED, completed_at should be set.
**Validates: Requirements 6.3, 6.4**

## Error Handling

### Authorization Errors

| Error Code | Condition | Response |
|------------|-----------|----------|
| 403 | Manager lacks authority over employee | `{"error": "You do not have authority over this employee"}` |
| 403 | Non-manager attempts course assignment | `{"error": "Only managers can assign courses"}` |

### Validation Errors

| Error Code | Condition | Response |
|------------|-----------|----------|
| 400 | Course already assigned | `{"error": "Course is already assigned to this employee"}` |
| 400 | Invalid status transition | `{"error": "Invalid status transition from {current} to {new}"}` |
| 404 | Template not found | `{"error": "Template {id} not found"}` |
| 404 | Course not found | `{"error": "Course {id} not found"}` |

## Testing Strategy

### Unit Testing

- Test TemplateAssessmentService.get_template_for_assessment() returns correct skills
- Test CourseAssignmentService.assign_course() creates correct records
- Test progress calculation accuracy

### Property-Based Testing

Using Hypothesis library for Python:

1. **Template Assessment Property Test**: Generate random templates and employees, verify all skills are returned with correct levels
2. **Course Assignment Authority Test**: Generate random manager-employee relationships, verify authorization decisions
3. **Assignment Idempotency Test**: Generate random assignment attempts, verify no duplicates
4. **Status Transition Test**: Generate random status transitions, verify valid transitions succeed and invalid ones fail

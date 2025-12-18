# Design Document: Manager-Driven Skill Assessment Model

## Overview

This design document describes the architecture for transforming Skillboard from a self-service skill management system to a manager-driven assessment model. The core principle is that skills are evaluated by authorized managers, not self-declared by employees. This ensures governance, auditability, and fairness in skill tracking.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  Employee Skill Board    │  Manager Assessment    │  HR Dashboard    │
│  (Read-Only View)        │  Screen                │  (Admin View)    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                            │
├─────────────────────────────────────────────────────────────────────┤
│  Authorization Middleware  │  Role Validation  │  Audit Logging     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer                                │
├─────────────────────────────────────────────────────────────────────┤
│  AssessmentService  │  BaselineService  │  ReadinessCalculator      │
│  AuthorityValidator │  AuditService     │  LevelMovementService     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                   │
├─────────────────────────────────────────────────────────────────────┤
│  skill_assessments  │  assessment_history  │  pathway_skills        │
│  employees (locked) │  level_movement      │  audit_logs            │
└─────────────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **Employee View Flow**: Employee → API → AuthZ (verify employee role) → Read-only data fetch → Response
2. **Manager Assessment Flow**: Manager → API → AuthZ (verify LM/DM role) → Authority check → Assessment service → History capture → Response
3. **Baseline Assignment Flow**: HR/System → Band+Pathway assignment → Baseline service → Auto-create assessments → History capture

## Components and Interfaces

### 1. AssessmentService

Handles all skill assessment operations.

```python
class AssessmentService:
    def create_assessment(
        self,
        employee_id: int,
        skill_id: int,
        level: RatingEnum,
        assessor_id: int,
        assessor_role: str,
        comments: Optional[str] = None
    ) -> SkillAssessment:
        """Create or update a skill assessment. Captures history automatically."""
        
    def get_employee_assessments(
        self,
        employee_id: int,
        include_gaps: bool = True
    ) -> List[AssessmentWithGap]:
        """Get all assessments for an employee with optional gap analysis."""
        
    def get_assessment_history(
        self,
        employee_id: int,
        skill_id: Optional[int] = None
    ) -> List[AssessmentHistory]:
        """Get assessment history, optionally filtered by skill."""
```

### 2. BaselineService

Handles automatic baseline skill assignment.

```python
class BaselineService:
    BAND_BASELINE_MAP = {
        "A": RatingEnum.BEGINNER,
        "B": RatingEnum.DEVELOPING,
        "C": RatingEnum.INTERMEDIATE,
        "L1": RatingEnum.ADVANCED,
        "L2": RatingEnum.EXPERT,
    }
    
    def assign_baseline(
        self,
        employee_id: int,
        band: str,
        pathway: str
    ) -> List[SkillAssessment]:
        """Assign baseline assessments for all pathway skills."""
        
    def get_pathway_skills(self, pathway: str) -> List[Skill]:
        """Get all skills belonging to a pathway."""
```

### 3. AuthorityValidator

Validates manager authority over employees.

```python
class AuthorityValidator:
    def can_assess(
        self,
        assessor_id: int,
        assessor_role_id: int,
        target_employee_id: int
    ) -> Tuple[bool, str]:
        """
        Check if assessor has authority over target employee.
        Returns (is_authorized, reason).
        """
        
    def get_assessable_employees(
        self,
        manager_id: int,
        manager_role_id: int
    ) -> List[Employee]:
        """Get list of employees the manager can assess."""
```

### 4. ReadinessCalculator

Calculates promotion readiness scores.

```python
class ReadinessCalculator:
    def calculate_readiness(
        self,
        employee_id: int,
        target_band: str
    ) -> ReadinessResult:
        """
        Calculate readiness score for target band.
        Returns score (0-100), gaps, and met requirements.
        """
        
    def get_skill_gaps(
        self,
        employee_id: int,
        target_band: Optional[str] = None
    ) -> List[SkillGap]:
        """Get skill gaps for employee vs target or next band."""
```

### 5. API Endpoints

#### Assessment Endpoints (Manager Only)

```
POST   /api/assessments/employee/{employee_id}/skill/{skill_id}
       Body: { level: string, comments?: string }
       Auth: LM or DM with authority over employee
       
GET    /api/assessments/employee/{employee_id}
       Auth: Employee (own), Manager (reports), HR (all)
       
GET    /api/assessments/employee/{employee_id}/history
       Auth: Employee (own), Manager (reports), HR (all)
       
GET    /api/assessments/assessable-employees
       Auth: LM or DM
       Returns: List of employees the manager can assess
```

#### Employee Skill Board Endpoints (Read-Only)

```
GET    /api/skill-board/me
       Auth: Any authenticated user
       Returns: Read-only skill board with assessments, gaps, readiness
       
GET    /api/skill-board/me/readiness
       Auth: Any authenticated user
       Returns: Readiness score and gap analysis for next band
```

#### Deprecated Endpoints (Return 410 Gone)

```
POST   /api/user-skills/me          → 410 Gone
PUT    /api/user-skills/me/{id}     → 410 Gone
DELETE /api/user-skills/me/{id}     → 410 Gone
POST   /api/user-skills/            → 410 Gone (employee self-service)
```

## Data Models

### New Tables

#### skill_assessments (replaces employee_skills for assessed data)

```sql
CREATE TABLE skill_assessments (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    level VARCHAR(50) NOT NULL,  -- Beginner, Developing, Intermediate, Advanced, Expert
    assessment_type VARCHAR(20) NOT NULL,  -- 'baseline' or 'manager'
    assessor_id INTEGER REFERENCES employees(id),  -- NULL for SYSTEM baseline
    assessor_role VARCHAR(50),  -- 'SYSTEM', 'LINE_MANAGER', 'DELIVERY_MANAGER'
    comments TEXT,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(employee_id, skill_id)
);

CREATE INDEX idx_skill_assessments_employee ON skill_assessments(employee_id);
CREATE INDEX idx_skill_assessments_assessor ON skill_assessments(assessor_id);
```

#### assessment_history (immutable audit trail)

```sql
CREATE TABLE assessment_history (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    previous_level VARCHAR(50),  -- NULL for first assessment
    new_level VARCHAR(50) NOT NULL,
    assessment_type VARCHAR(20) NOT NULL,
    assessor_id INTEGER REFERENCES employees(id),
    assessor_role VARCHAR(50) NOT NULL,
    comments TEXT,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Immutability: No UPDATE or DELETE triggers allowed
    CONSTRAINT no_updates CHECK (TRUE)  -- Enforced at application level
);

CREATE INDEX idx_assessment_history_employee ON assessment_history(employee_id);
CREATE INDEX idx_assessment_history_skill ON assessment_history(skill_id);
CREATE INDEX idx_assessment_history_date ON assessment_history(assessed_at DESC);
```

#### pathway_skills (defines skills per pathway)

```sql
CREATE TABLE pathway_skills (
    id SERIAL PRIMARY KEY,
    pathway VARCHAR(100) NOT NULL,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    is_core BOOLEAN DEFAULT TRUE,  -- Core vs optional skill
    display_order INTEGER,
    
    UNIQUE(pathway, skill_id)
);

CREATE INDEX idx_pathway_skills_pathway ON pathway_skills(pathway);
```

### Modified Tables

#### employees (add pathway, enforce immutability)

```sql
ALTER TABLE employees 
ADD COLUMN pathway VARCHAR(100),
ADD COLUMN band_locked_at TIMESTAMP,
ADD COLUMN pathway_locked_at TIMESTAMP;

-- Application-level constraint: band and pathway can only be modified
-- by Level Movement service with proper approval chain
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Band and Pathway Immutability
*For any* API request that attempts to directly modify an employee's band or pathway field (excluding Level Movement approval), the system should reject the request with HTTP 403 and the employee's band and pathway should remain unchanged.
**Validates: Requirements 1.2, 1.3, 1.5**

### Property 2: Baseline Proficiency Mapping
*For any* employee assigned a Band B and Pathway P, all skills in pathway P should receive baseline assessments with proficiency level equal to BAND_BASELINE_MAP[B], assessor_role "SYSTEM", and assessment_type "baseline".
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 3: Employee Cannot Modify Skills
*For any* authenticated user with role_id = 6 (Employee), all POST/PUT/DELETE requests to skill modification endpoints should be rejected with HTTP 403 or HTTP 410, and no skill_assessments records should be created or modified.
**Validates: Requirements 3.6, 7.4**

### Property 4: Manager Authority Validation
*For any* skill assessment submission by a user with role_id 4 (DM) or 5 (LM), the assessment should only succeed if the target employee is either a direct report (line_manager_id matches) OR assigned to a project managed by the assessor. Otherwise, HTTP 403 should be returned.
**Validates: Requirements 4.4, 4.5, 7.1, 7.2**

### Property 5: Assessment History Immutability
*For any* skill assessment creation or update, an assessment_history record should be created with all required fields (employee_id, skill_id, previous_level, new_level, assessor_id, assessor_role, assessed_at). No assessment_history records should ever be modified or deleted.
**Validates: Requirements 5.1, 5.2, 5.5**

### Property 6: Assessment History Completeness
*For any* assessment_history record, the record should contain: employee_id (not null), skill_id (not null), new_level (not null), assessor_role (not null), and assessed_at (not null). The previous_level may be null only for the first assessment of a skill.
**Validates: Requirements 5.2, 4.7**

### Property 7: Readiness Score Calculation
*For any* employee with band B and pathway P, the readiness_score for target band B' should equal (sum of skills meeting B' requirements / total required skills for B') * 100, where a skill "meets requirement" if assessed_level >= required_level for B'.
**Validates: Requirements 6.1, 6.2, 6.5**

### Property 8: Level Movement Band Update
*For any* Level Movement request that receives all required approvals (manager, CP, HR), the employee's band should be updated to the requested_level, and baseline assessments should be created for any new pathway skills not previously assessed.
**Validates: Requirements 1.4, 6.4**

### Property 9: Unauthorized Access Logging
*For any* API request that is rejected due to authorization failure (HTTP 403), an audit_log record should be created with user_id, endpoint, timestamp, and IP address.
**Validates: Requirements 7.3**

### Property 10: Assessment Label Accuracy
*For any* skill assessment displayed to a user, the label should be "System Baseline" if assessment_type = "baseline", or "Manager Assessed" if assessment_type = "manager". The label should match the assessment_type field exactly.
**Validates: Requirements 3.7**

## Error Handling

### Authorization Errors

| Error Code | Condition | Response |
|------------|-----------|----------|
| 403 | Employee attempts skill modification | `{"error": "Employees cannot modify skill assessments"}` |
| 403 | Manager lacks authority over employee | `{"error": "You do not have assessment authority over this employee"}` |
| 403 | Direct band/pathway modification attempt | `{"error": "Band/Pathway can only be changed via Level Movement workflow"}` |
| 410 | Legacy self-service endpoint called | `{"error": "Self-service skill editing has been disabled"}` |

### Validation Errors

| Error Code | Condition | Response |
|------------|-----------|----------|
| 400 | Invalid proficiency level | `{"error": "Invalid level. Must be one of: Beginner, Developing, Intermediate, Advanced, Expert"}` |
| 400 | Skill not in employee's pathway | `{"error": "Skill {skill_id} is not part of employee's pathway"}` |
| 404 | Employee not found | `{"error": "Employee {employee_id} not found"}` |
| 404 | Skill not found | `{"error": "Skill {skill_id} not found"}` |

## Testing Strategy

### Unit Testing

- Test BaselineService.assign_baseline() creates correct assessments for each band
- Test AuthorityValidator.can_assess() returns correct results for various relationships
- Test ReadinessCalculator.calculate_readiness() produces accurate scores

### Property-Based Testing

Using Hypothesis library for Python:

1. **Baseline Assignment Property Test**: Generate random band/pathway combinations, verify all pathway skills get correct baseline level
2. **Authority Validation Property Test**: Generate random manager-employee relationships, verify authorization decisions are consistent
3. **Immutability Property Test**: Generate random modification attempts on band/pathway, verify all are rejected
4. **History Completeness Property Test**: Generate random assessment sequences, verify history captures all changes

### Integration Testing

- Test full assessment flow: Manager login → Select employee → Submit assessment → Verify history
- Test baseline flow: HR assigns band+pathway → Verify baseline assessments created
- Test Level Movement flow: Request → Approvals → Band update → New baselines

## Security Considerations

### RBAC Enforcement

```python
ASSESSMENT_PERMISSIONS = {
    RoleID.SYSTEM_ADMIN: ["read", "write", "admin"],
    RoleID.HR: ["read", "admin"],
    RoleID.CAPABILITY_PARTNER: ["read"],
    RoleID.DELIVERY_MANAGER: ["read", "write"],  # Only for authorized employees
    RoleID.LINE_MANAGER: ["read", "write"],      # Only for authorized employees
    RoleID.EMPLOYEE: ["read_own"],               # Read-only, own data only
}
```

### Audit Requirements

All assessment operations must log:
- User ID performing action
- Target employee ID
- Action type (create, update, view, export)
- Timestamp
- IP address
- Success/failure status

## Migration Strategy

### Phase 1: Schema Migration
1. Create new tables (skill_assessments, assessment_history, pathway_skills)
2. Add pathway column to employees table
3. Migrate existing employee_skills data to skill_assessments with assessment_type='legacy'

### Phase 2: API Migration
1. Deploy new assessment endpoints
2. Update existing endpoints to return 410 for self-service operations
3. Update frontend to use new read-only views

### Phase 3: Data Cleanup
1. Assign pathways to all employees based on category/team
2. Generate baseline assessments for employees without assessments
3. Archive legacy employee_skills table


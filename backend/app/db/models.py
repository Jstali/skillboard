"""SQLAlchemy models for Skillboard application."""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Float, UniqueConstraint, Boolean, DateTime, Date, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

Base = declarative_base()


class RatingEnum(str, enum.Enum):
    """Skill rating levels."""
    BEGINNER = "Beginner"
    DEVELOPING = "Developing"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class Skill(Base):
    """Master skills table."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    pathway = Column(String, nullable=True, index=True)  # Top-level pathway: Consulting, Technical, Legal, etc.
    category = Column(String, nullable=True, index=True)  # Category within pathway: Core Legal Skills, Advisory, etc.

    # Relationship to employee skills
    employee_skills = relationship("EmployeeSkill", back_populates="skill")


class User(Base):
    """User accounts table for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, nullable=True, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, default=6)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")




class Employee(Base):
    """Employees table."""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company_email = Column(String, nullable=True, index=True)
    department = Column(String, nullable=True)
    role = Column(String, nullable=True)
    team = Column(String, nullable=True, index=True)  # Team assignment: consulting, technical_delivery, project_programming, corporate_functions_it, corporate_functions_marketing, corporate_functions_finance, corporate_functions_legal, corporate_functions_pc
    band = Column(String, nullable=True, index=True)  # Calculated band: A, B, C, L1, L2
    category = Column(String, nullable=True, index=True)
    
    # HRMS Pre-Integration Fields
    line_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    grade = Column(String(50), nullable=True)
    capability = Column(String(100), nullable=True)
    capability_owner_id = Column(Integer, ForeignKey("capability_owners.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, default=6)
    
    # HRMS Integration fields
    hrms_employee_id = Column(String, nullable=True, index=True)  # Employee ID from HRMS system
    hrms_line_manager_id = Column(String, nullable=True, index=True)  # Line manager ID from HRMS (string format)
    home_capability = Column(String, nullable=True, index=True)  # Home capability area (AWL, Technical Delivery, etc.)
    hire_date = Column(Date, nullable=True)
    location_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    hrms_last_sync = Column(DateTime, nullable=True)  # Last sync timestamp from HRMS
    
    # Manager-Driven Skill Assessment fields
    pathway = Column(String(100), nullable=True, index=True)  # Career pathway: Technical, SAP, Cloud, Data, etc.
    band_locked_at = Column(DateTime, nullable=True)  # Timestamp when band was last set via Level Movement
    pathway_locked_at = Column(DateTime, nullable=True)  # Timestamp when pathway was last set via Level Movement
    
    # Relationship to employee skills
    employee_skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    # HRMS relationships
    hrms_project_assignments = relationship("HRMSProjectAssignment", back_populates="employee", cascade="all, delete-orphan")
    hrms_sync_logs = relationship("HRMSEmployeeSync", back_populates="employee", cascade="all, delete-orphan")
    
    # HRMS Relationships - use primaryjoin to explicitly specify the join condition
    line_manager = relationship("Employee", remote_side=[id], foreign_keys=[line_manager_id], primaryjoin="Employee.line_manager_id == Employee.id")
    capability_owner = relationship("CapabilityOwner", foreign_keys=[capability_owner_id], back_populates="employees")
    user_role = relationship("Role")  # Renamed from 'role' to avoid conflict with role column (job title)

    # Project assignments
    project_assignments = relationship("EmployeeProjectAssignment", foreign_keys="EmployeeProjectAssignment.employee_id", back_populates="employee")
    level_movement_requests = relationship("LevelMovementRequest", back_populates="employee")


class EmployeeSkill(Base):
    """Employee-Skill mappings with rating and experience."""
    __tablename__ = "employee_skills"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    rating = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=True)  # Nullable for interested skills
    initial_rating = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=True)  # First rating when skill was added (for tracking improvements)
    years_experience = Column(Float, nullable=True)
    is_interested = Column(Boolean, default=False, nullable=False)  # False = existing, True = interested
    notes = Column(String, nullable=True)  # Optional notes field
    match_score = Column(Float, nullable=True)  # For fuzzy matching during import
    needs_review = Column(Boolean, default=False, nullable=False)  # Flag for admin review
    is_custom = Column(Boolean, default=False, nullable=False)  # True if skill was added by user outside template
    learning_status = Column(String, default="Not Started", nullable=False)  # Not Started, Learning, Stuck, Completed
    status_updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="employee_skills")
    skill = relationship("Skill", back_populates="employee_skills")

    # Unique constraint: one rating per employee-skill pair
    __table_args__ = (
        UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),
    )


class TeamSkillTemplate(Base):
    """Team-specific skill templates defining which skills are relevant for each team."""
    __tablename__ = "team_skill_templates"

    id = Column(Integer, primary_key=True, index=True)
    team = Column(String, nullable=False, index=True)  # Team name: consulting, technical_delivery, etc.
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)  # Whether this skill is required for the team
    display_order = Column(Integer, nullable=True)  # Order in which skills should be displayed

    # Relationships
    skill = relationship("Skill")

    # Unique constraint: one template entry per team-skill pair
    __table_args__ = (
        UniqueConstraint("team", "skill_id", name="uq_team_skill_template"),
    )


class RoleRequirement(Base):
    """Role requirements defining required skill levels for each band."""
    __tablename__ = "role_requirements"

    id = Column(Integer, primary_key=True, index=True)
    band = Column(String, nullable=False, index=True)  # Band: A, B, C, L1, L2
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    required_rating = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=False)  # Required rating level for this band
    is_required = Column(Boolean, default=True, nullable=False)  # Whether this skill is required for the band

    # Relationships
    skill = relationship("Skill")

    # Unique constraint: one requirement per band-skill pair
    __table_args__ = (
        UniqueConstraint("band", "skill_id", name="uq_band_skill_requirement"),
    )


class CategorySkillTemplate(Base):
    """Category-specific skill templates defining which skills are available for each category."""
    __tablename__ = "category_skill_templates"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)  # Category name
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)  # Whether this skill is required for the category
    display_order = Column(Integer, nullable=True)  # Order in which skills should be displayed

    # Relationships
    skill = relationship("Skill")

    # Unique constraint: one template entry per category-skill pair
    __table_args__ = (
        UniqueConstraint("category", "skill_id", name="uq_category_skill_template"),
    )


class CourseStatusEnum(str, enum.Enum):
    """Course completion status."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class Course(Base):
    """Learning courses/certifications."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)  # Associated skill
    external_url = Column(String, nullable=True)  # Link to external learning platform
    is_mandatory = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who created it

    # Relationships
    skill = relationship("Skill")
    assignments = relationship("CourseAssignment", back_populates="course")


class CourseAssignment(Base):
    """Course assignments to employees."""
    __tablename__ = "course_assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who assigned
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(CourseStatusEnum, native_enum=False, length=50), default=CourseStatusEnum.NOT_STARTED, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    certificate_url = Column(String, nullable=True)  # Uploaded certificate file path/URL
    notes = Column(String, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)  # Skill this course was assigned to address (for gap analysis linkage)

    # Relationships
    course = relationship("Course", back_populates="assignments")
    employee = relationship("Employee")
    skill = relationship("Skill")  # Link to skill for gap analysis

    # Unique constraint: one assignment per employee-course pair
    __table_args__ = (
        UniqueConstraint("employee_id", "course_id", name="uq_employee_course_assignment"),
    )


class SkillTemplate(Base):
    """Uploaded skill templates from spreadsheet files."""
    __tablename__ = "skill_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String, nullable=False, index=True)  # Sheet name
    file_name = Column(String, nullable=False)  # Original file name
    content = Column(String, nullable=False)  # JSON string of array of rows/columns
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationship
    uploader = relationship("User")


class TemplateAssignment(Base):
    """Assignment of a skill template to an employee."""
    __tablename__ = "template_assignments"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("skill_templates.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="Pending", nullable=False)  # Pending, In Progress, Completed
    category_hr = Column(String, nullable=True)  # Category selected by HR (hidden from employee)

    # Relationships
    template = relationship("SkillTemplate")
    employee = relationship("Employee")
    assigner = relationship("User")
    responses = relationship("EmployeeTemplateResponse", back_populates="assignment", cascade="all, delete-orphan")
    gap_results = relationship("SkillGapResult", back_populates="assignment", cascade="all, delete-orphan")

    # Unique constraint: one assignment per employee-template pair
    __table_args__ = (
        UniqueConstraint("template_id", "employee_id", name="uq_template_employee_assignment"),
    )


class EmployeeTemplateResponse(Base):
    """Employee responses to assigned skill templates."""
    __tablename__ = "employee_template_responses"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("template_assignments.id"), nullable=False)
    employee_category = Column(String, nullable=False)  # Category selected by employee
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    employee_level = Column(String, nullable=True)  # Rating: Beginner, Developing, Intermediate, Advanced, Expert
    years_experience = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assignment = relationship("TemplateAssignment", back_populates="responses")
    skill = relationship("Skill")

    # Unique constraint: one response per assignment-skill pair
    __table_args__ = (
        UniqueConstraint("assignment_id", "skill_id", name="uq_assignment_skill_response"),
    )


class SkillGapResult(Base):
    """Calculated skill gap results for template assignments."""
    __tablename__ = "skill_gap_results"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("template_assignments.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    required_level = Column(String, nullable=False)  # From template requirement
    employee_level = Column(String, nullable=True)  # From employee response
    gap_status = Column(String, nullable=False)  # "Gap", "Met", "Exceeded"
    gap_value = Column(Integer, nullable=False)  # Numeric difference (-2, 0, +1, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assignment = relationship("TemplateAssignment", back_populates="gap_results")
    skill = relationship("Skill")

    # Unique constraint: one gap result per assignment-skill pair
    __table_args__ = (
        UniqueConstraint("assignment_id", "skill_id", name="uq_assignment_skill_gap"),
    )


class TemplateAssessmentLog(Base):
    """Audit trail for template-based skill assessments by managers.
    
    Records when a manager assesses an employee using a skill template,
    tracking the template used, assessor, and assessment statistics.
    """
    __tablename__ = "template_assessment_logs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("skill_templates.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    assessor_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skills_assessed = Column(Integer, nullable=False)
    total_skills = Column(Integer, nullable=False)
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("SkillTemplate")
    employee = relationship("Employee", foreign_keys=[employee_id])
    assessor = relationship("Employee", foreign_keys=[assessor_id])


# ============================================================================
# HRMS PRE-INTEGRATION MODELS
# Added for multi-project support, RBAC, level movement workflow
# ============================================================================

class Role(Base):
    """User roles for RBAC."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="role")





class Project(Base):
    """Projects table for multi-project assignment."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    capability_required = Column(String(100), nullable=True)
    hrms_project_id = Column(String(100), nullable=True, unique=True, index=True)  # Link to HRMS
    client_name = Column(String(255), nullable=True)
    manager_name = Column(String(255), nullable=True)
    status = Column(String(50), default="Active", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignments = relationship("EmployeeProjectAssignment", back_populates="project", cascade="all, delete-orphan")


class EmployeeProjectAssignment(Base):
    """Employee-Project assignments with allocation and management."""
    __tablename__ = "employee_project_assignments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    percentage_allocation = Column(Integer, nullable=True)  # 0-100
    line_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    capability_owner_id = Column(Integer, ForeignKey("capability_owners.id"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    project = relationship("Project", back_populates="assignments")
    line_manager = relationship("Employee", foreign_keys=[line_manager_id])

    # Unique constraint: one assignment per employee-project pair
    __table_args__ = (
        UniqueConstraint("employee_id", "project_id", name="uq_employee_project"),
    )


class CapabilityOwner(Base):
    """Capability owners for grouping employees by capability."""
    __tablename__ = "capability_owners"

    id = Column(Integer, primary_key=True, index=True)
    capability_name = Column(String(100), unique=True, nullable=False)
    owner_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    employees = relationship("Employee", back_populates="capability_owner", foreign_keys="Employee.capability_owner_id")
    owner = relationship("Employee", foreign_keys=[owner_employee_id])


class LevelMovementRequest(Base):
    """Level/Grade movement requests for promotions."""
    __tablename__ = "level_movement_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    current_level = Column(String(50), nullable=True)
    requested_level = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, manager_approved, cp_approved, hr_approved, rejected
    readiness_score = Column(Float, nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    manager_approval_date = Column(DateTime, nullable=True)
    cp_approval_date = Column(DateTime, nullable=True)
    hr_approval_date = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)

    # Relationships
    employee = relationship("Employee")
    approvals = relationship("LevelMovementApprovalAudit", back_populates="request", cascade="all, delete-orphan")


class LevelMovementApprovalAudit(Base):
    """Audit trail for level movement approvals."""
    __tablename__ = "level_movement_approval_audit"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("level_movement_requests.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approver_role = Column(String(50), nullable=False)
    approval_status = Column(String(50), nullable=False)  # approved, rejected
    comments = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    request = relationship("LevelMovementRequest", back_populates="approvals")
    approver = relationship("Employee")


class AuditLog(Base):
    """Audit logs for GDPR-sensitive data access."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=True)
    target_type = Column(String(50), nullable=True)
    accessed_fields = Column(String, nullable=True)  # JSON string
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class OrgStructure(Base):
    """Organizational hierarchy structure."""
    __tablename__ = "org_structure"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    level = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    manager = relationship("Employee", foreign_keys=[manager_id])



# ============================================================================
# HRMS Integration Models
# ============================================================================

class HRMSProject(Base):
    """Projects from HRMS system."""
    __tablename__ = "hrms_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    hrms_project_id = Column(String, unique=True, index=True, nullable=False)  # Project ID from HRMS
    project_name = Column(String, nullable=False, index=True)
    client_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Active")  # Active, Completed, On Hold
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    project_manager_id = Column(String, nullable=True)  # HRMS manager ID
    project_manager_name = Column(String, nullable=True)
    
    # Sync tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    hrms_last_sync = Column(DateTime, nullable=True)
    
    # Relationships
    assignments = relationship("HRMSProjectAssignment", back_populates="project", cascade="all, delete-orphan")


class HRMSProjectAssignment(Base):
    """Employee project assignments from HRMS."""
    __tablename__ = "hrms_project_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("hrms_projects.id"), nullable=False)
    
    # Assignment details from HRMS
    allocated_days = Column(Float, nullable=False, default=0.0)
    consumed_days = Column(Float, nullable=False, default=0.0)
    remaining_days = Column(Float, nullable=False, default=0.0)
    allocation_percentage = Column(Float, nullable=True)  # Percentage of time allocated
    month = Column(String, nullable=False, index=True)  # Format: "2025-01"
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Sync tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    hrms_last_sync = Column(DateTime, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="hrms_project_assignments")
    project = relationship("HRMSProject", back_populates="assignments")
    
    # Unique constraint: one assignment per employee-project-month
    __table_args__ = (
        UniqueConstraint("employee_id", "project_id", "month", name="uq_employee_project_month"),
    )


class HRMSAttendanceRecord(Base):
    """Attendance records from HRMS for skill correlation."""
    __tablename__ = "hrms_attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("hrms_projects.id"), nullable=True)
    
    # Attendance details
    date = Column(Date, nullable=False, index=True)
    action = Column(String, nullable=False)  # Present, WFH, Leave, At office
    total_hours = Column(Float, nullable=False, default=0.0)
    project_hours = Column(Float, nullable=False, default=0.0)
    
    # Task details for skill correlation
    sub_tasks = Column(JSON, nullable=True)  # JSON array of sub-tasks and hours
    
    # Sync tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    hrms_last_sync = Column(DateTime, nullable=True)
    
    # Relationships
    employee = relationship("Employee")
    project = relationship("HRMSProject")
    
    # Unique constraint: one record per employee-project-date
    __table_args__ = (
        UniqueConstraint("employee_id", "project_id", "date", name="uq_employee_project_date"),
    )


class HRMSEmployeeSync(Base):
    """Track employee data synchronization from HRMS."""
    __tablename__ = "hrms_employee_sync"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String, nullable=False)  # full_sync, incremental, manual
    sync_status = Column(String, nullable=False)  # success, failed, partial
    sync_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Data synced
    data_synced = Column(JSON, nullable=True)  # JSON of what data was synced
    errors = Column(Text, nullable=True)  # Any errors during sync
    
    # Relationships
    employee = relationship("Employee", back_populates="hrms_sync_logs")


class HRMSImportLog(Base):
    """Log of HRMS data import operations."""
    __tablename__ = "hrms_import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    import_type = Column(String, nullable=False, index=True)  # employees, projects, assignments, attendance
    import_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Import statistics
    records_processed = Column(Integer, nullable=False, default=0)
    records_created = Column(Integer, nullable=False, default=0)
    records_updated = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    
    # Import details
    status = Column(String, nullable=False)  # success, failed, partial
    error_details = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Data quality metrics
    data_quality_score = Column(Float, nullable=True)  # 0.0 to 100.0
    validation_errors = Column(Text, nullable=True)  # JSON array of validation errors


class HRMSConfiguration(Base):
    """HRMS integration configuration."""
    __tablename__ = "hrms_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)  # Encrypted for sensitive values
    is_encrypted = Column(Boolean, default=False, nullable=False)
    description = Column(String, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    updater = relationship("User")


class AccessLog(Base):
    """Audit log for sensitive data access (GDPR compliance)."""
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Access details
    resource_type = Column(String, nullable=False, index=True)  # Employee, Project, Assignment, Report
    resource_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # View, Edit, Delete, Export, Sync
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Request details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    
    # Data sensitivity classification
    data_sensitivity = Column(String, nullable=False, index=True)  # Public, Internal, Sensitive, Restricted
    
    # Relationships
    user = relationship("User")


# ============================================================================
# Manager-Driven Skill Assessment Models
# ============================================================================

class AssessmentTypeEnum(str, enum.Enum):
    """Types of skill assessments."""
    BASELINE = "baseline"  # System-generated based on band
    MANAGER = "manager"    # Assessed by Line Manager or Delivery Manager
    LEGACY = "legacy"      # Migrated from old self-service system


class AssessorRoleEnum(str, enum.Enum):
    """Roles that can assess skills."""
    SYSTEM = "SYSTEM"
    LINE_MANAGER = "LINE_MANAGER"
    DELIVERY_MANAGER = "DELIVERY_MANAGER"
    LEGACY_SELF_REPORTED = "LEGACY_SELF_REPORTED"


class SkillAssessment(Base):
    """Manager-assessed skill levels for employees.
    
    Replaces self-service skill ratings. Only managers can create/update assessments.
    """
    __tablename__ = "skill_assessments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    level = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=False)
    assessment_type = Column(SQLEnum(AssessmentTypeEnum, native_enum=False, length=20), nullable=False)
    assessor_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # NULL for SYSTEM
    assessor_role = Column(SQLEnum(AssessorRoleEnum, native_enum=False, length=50), nullable=False)
    comments = Column(Text, nullable=True)
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    skill = relationship("Skill")
    assessor = relationship("Employee", foreign_keys=[assessor_id])

    # Unique constraint: one assessment per employee-skill pair
    __table_args__ = (
        UniqueConstraint("employee_id", "skill_id", name="uq_skill_assessment_employee_skill"),
    )


class AssessmentHistory(Base):
    """Immutable audit trail of all skill assessment changes.
    
    Records cannot be modified or deleted (enforced by database triggers).
    """
    __tablename__ = "assessment_history"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    previous_level = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=True)  # NULL for first assessment
    new_level = Column(SQLEnum(RatingEnum, native_enum=False, length=50), nullable=False)
    assessment_type = Column(SQLEnum(AssessmentTypeEnum, native_enum=False, length=20), nullable=False)
    assessor_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # NULL for SYSTEM
    assessor_role = Column(SQLEnum(AssessorRoleEnum, native_enum=False, length=50), nullable=False)
    comments = Column(Text, nullable=True)
    assessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    skill = relationship("Skill")
    assessor = relationship("Employee", foreign_keys=[assessor_id])


class PathwaySkill(Base):
    """Defines which skills belong to each career pathway."""
    __tablename__ = "pathway_skills"

    id = Column(Integer, primary_key=True, index=True)
    pathway = Column(String(100), nullable=False, index=True)  # Technical, SAP, Cloud, Data, etc.
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    is_core = Column(Boolean, default=True, nullable=False)  # Core vs optional skill
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    skill = relationship("Skill")

    # Unique constraint: one entry per pathway-skill pair
    __table_args__ = (
        UniqueConstraint("pathway", "skill_id", name="uq_pathway_skill"),
    )

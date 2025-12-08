"""SQLAlchemy models for Skillboard application."""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Float, UniqueConstraint, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
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
    category = Column(String, nullable=True, index=True)  # Category like "Programming", "SAP", "Cloud", "DevOps"

    # Relationship to employee skills
    employee_skills = relationship("EmployeeSkill", back_populates="skill")


class User(Base):
    """User accounts table for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, nullable=True, unique=True, index=True)  # References Employee.employee_id (string), not FK to avoid circular deps
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


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
    category = Column(String, nullable=True, index=True)  # Employee category for skill template filtering

    # Relationship to employee skills
    employee_skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")


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

    # Relationships
    course = relationship("Course", back_populates="assignments")
    employee = relationship("Employee")

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

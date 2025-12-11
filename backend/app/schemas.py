"""Pydantic schemas for request/response validation."""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from app.db.models import RatingEnum


# Skill schemas
class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class Skill(SkillBase):
    id: int

    class Config:
        from_attributes = True


# Employee schemas
class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    band: Optional[str] = None
    category: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: int

    class Config:
        from_attributes = True


# EmployeeSkill schemas
class EmployeeSkillBase(BaseModel):
    rating: Optional[RatingEnum] = None  # Optional - not required for interested skills
    years_experience: Optional[float] = None


class EmployeeSkillCreate(EmployeeSkillBase):
    employee_id: str
    employee_name: Optional[str] = None  # Optional, will use employee_id if not provided
    skill_name: str
    is_interested: Optional[bool] = False
    notes: Optional[str] = None
    is_custom: Optional[bool] = False


class EmployeeSkillCreateMe(BaseModel):
    """Schema for creating employee skill via /me endpoint (no employee_id needed)."""
    skill_name: str
    skill_category: Optional[str] = None  # Category for the skill
    rating: Optional[RatingEnum] = None  # Optional - not required for interested skills
    years_experience: Optional[float] = None
    is_interested: Optional[bool] = False
    notes: Optional[str] = None
    is_custom: Optional[bool] = False


class EmployeeSkillUpdate(BaseModel):
    rating: Optional[RatingEnum] = None
    years_experience: Optional[float] = None
    is_interested: Optional[bool] = None
    notes: Optional[str] = None
    learning_status: Optional[str] = None


class EmployeeSkill(EmployeeSkillBase):
    id: int
    employee_id: int
    skill_id: int
    is_interested: bool
    notes: Optional[str] = None
    is_custom: bool
    learning_status: str
    status_updated_at: datetime
    employee: Employee
    skill: Skill

    class Config:
        from_attributes = True


# Search result schemas
class MatchedSkillInfo(BaseModel):
    skill_name: str
    match_score: float


class FuzzySearchResult(BaseModel):
    employee_id: str
    employee_name: str
    overall_match_score: float
    matched_skills: List[MatchedSkillInfo]
    ratings: List[dict]  # List of {skill_name, rating, years_experience}


# Upload response schemas
class UploadResponse(BaseModel):
    message: str
    rows_processed: int
    rows_created: int
    rows_updated: int
    errors: Optional[List[str]] = None


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    employee_id: Optional[str] = None


class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    must_change_password: bool
    created_at: datetime
    role_id: Optional[int] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# Update forward references after all models are defined
Token.model_rebuild()


# ============================================================================
# HRMS PRE-INTEGRATION SCHEMAS
# ============================================================================

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    capability_required: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capability_required: Optional[str] = None


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Employee Project Assignment schemas
class EmployeeProjectAssignmentBase(BaseModel):
    employee_id: int
    project_id: int
    is_primary: bool = False
    percentage_allocation: Optional[int] = Field(None, ge=0, le=100)
    line_manager_id: Optional[int] = None
    capability_owner_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EmployeeProjectAssignmentCreate(EmployeeProjectAssignmentBase):
    pass


class EmployeeProjectAssignmentUpdate(BaseModel):
    is_primary: Optional[bool] = None
    percentage_allocation: Optional[int] = Field(None, ge=0, le=100)
    line_manager_id: Optional[int] = None
    capability_owner_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class EmployeeProjectAssignment(EmployeeProjectAssignmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Capability Owner schemas
class CapabilityOwnerBase(BaseModel):
    capability_name: str
    owner_employee_id: Optional[int] = None


class CapabilityOwnerCreate(CapabilityOwnerBase):
    pass


class CapabilityOwner(CapabilityOwnerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Level Movement Request schemas
class LevelMovementRequestBase(BaseModel):
    requested_level: str


class LevelMovementRequestCreate(LevelMovementRequestBase):
    pass


class LevelMovementRequest(LevelMovementRequestBase):
    id: int
    employee_id: int
    current_level: Optional[str] = None
    status: str
    readiness_score: Optional[float] = None
    submission_date: datetime
    manager_approval_date: Optional[datetime] = None
    cp_approval_date: Optional[datetime] = None
    hr_approval_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


# Level Movement Approval schemas
class ApprovalRequest(BaseModel):
    comments: Optional[str] = None


class LevelMovementApprovalAudit(BaseModel):
    id: int
    request_id: int
    approver_id: Optional[int] = None
    approver_role: str
    approval_status: str
    comments: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Audit Log schemas
class AuditLogCreate(BaseModel):
    action: str
    target_id: Optional[int] = None
    target_type: Optional[str] = None
    accessed_fields: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLog(AuditLogCreate):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Org Structure schemas
class OrgStructureBase(BaseModel):
    employee_id: int
    manager_id: Optional[int] = None
    level: Optional[int] = None


class OrgStructureCreate(OrgStructureBase):
    pass


class OrgStructure(OrgStructureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

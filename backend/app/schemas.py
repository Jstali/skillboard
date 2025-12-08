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

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# Update forward references after all models are defined
Token.model_rebuild()




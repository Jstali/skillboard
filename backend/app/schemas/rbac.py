"""Pydantic Schemas for RBAC"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.rbac import Role, Capability


class UserCreate(BaseModel):
    employee_id: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: Role = Role.EMPLOYEE
    capability: Optional[Capability] = None
    department: Optional[str] = None
    line_manager_id: Optional[int] = None
    delivery_manager_id: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class UserPublic(BaseModel):
    id: int
    employee_id: str
    email: str
    first_name: str
    last_name: str
    role: Role
    capability: Optional[Capability]
    department: Optional[str]

    class Config:
        from_attributes = True


class UserFull(UserPublic):
    """Full user data - HR/Admin only"""
    personal_email: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    salary: Optional[int]
    date_of_birth: Optional[datetime]
    performance_rating: Optional[str]
    joining_date: Optional[datetime]
    line_manager_id: Optional[int]
    delivery_manager_id: Optional[int]


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: int
    user_role: Role
    action: str
    resource_type: str
    resource_id: Optional[str]
    fields_accessed: Optional[List[str]]
    gdpr_basis: Optional[str]

    class Config:
        from_attributes = True

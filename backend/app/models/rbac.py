"""RBAC Models and Enums for Skillboard"""
from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.models import Base


class Role(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    HR = "hr"
    CAPABILITY_PARTNER = "capability_partner"
    DELIVERY_MANAGER = "delivery_manager"
    LINE_MANAGER = "line_manager"
    EMPLOYEE = "employee"


class Capability(str, Enum):
    ENGINEERING = "Engineering"
    DATA_SCIENCE = "Data Science"
    PRODUCT = "Product"
    DESIGN = "Design"
    QA = "QA"
    DEVOPS = "DevOps"


class DataSensitivity(str, Enum):
    SENSITIVE = "sensitive"
    SEMI_SENSITIVE = "semi_sensitive"
    NON_SENSITIVE = "non_sensitive"


# Field classification mapping
FIELD_CLASSIFICATION = {
    # Sensitive - HR/Self only
    "personal_email": DataSensitivity.SENSITIVE,
    "phone_number": DataSensitivity.SENSITIVE,
    "address": DataSensitivity.SENSITIVE,
    "salary": DataSensitivity.SENSITIVE,
    "date_of_birth": DataSensitivity.SENSITIVE,
    "national_id": DataSensitivity.SENSITIVE,
    "performance_rating": DataSensitivity.SENSITIVE,
    "medical_info": DataSensitivity.SENSITIVE,
    # Semi-sensitive
    "skill_rating": DataSensitivity.SEMI_SENSITIVE,
    "joining_date": DataSensitivity.SEMI_SENSITIVE,
    "first_name": DataSensitivity.SEMI_SENSITIVE,
    "last_name": DataSensitivity.SEMI_SENSITIVE,
    "company_email": DataSensitivity.SEMI_SENSITIVE,
    # Non-sensitive
    "employee_id": DataSensitivity.NON_SENSITIVE,
    "department": DataSensitivity.NON_SENSITIVE,
    "capability": DataSensitivity.NON_SENSITIVE,
    "skills": DataSensitivity.NON_SENSITIVE,
}


class UserWithRBAC(Base):
    """Extended User model with RBAC fields"""
    __tablename__ = "users_rbac"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(Role), default=Role.EMPLOYEE, nullable=False)
    capability = Column(SQLEnum(Capability), nullable=True)
    
    # Hierarchy
    line_manager_id = Column(Integer, ForeignKey("users_rbac.id"), nullable=True)
    delivery_manager_id = Column(Integer, ForeignKey("users_rbac.id"), nullable=True)
    
    # Sensitive fields
    personal_email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    salary = Column(Integer, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    national_id = Column(String(50), nullable=True)
    performance_rating = Column(String(20), nullable=True)
    
    # Non-sensitive
    department = Column(String(100), nullable=True)
    joining_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    line_manager = relationship("UserWithRBAC", remote_side=[id], foreign_keys=[line_manager_id])
    delivery_manager = relationship("UserWithRBAC", remote_side=[id], foreign_keys=[delivery_manager_id])
    direct_reports = relationship("UserWithRBAC", foreign_keys=[line_manager_id], back_populates="line_manager")


# Use the AuditLog from app.db.models to avoid duplicate table definition
# Import it here for convenience
from app.db.models import AuditLog

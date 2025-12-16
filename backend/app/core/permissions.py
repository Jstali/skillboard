"""RBAC Permissions Configuration"""
from enum import IntEnum
from typing import Set

class RoleID(IntEnum):
    SYSTEM_ADMIN = 1
    HR = 2
    LINE_MANAGER = 3        # Client-side Line Manager
    CAPABILITY_PARTNER = 4  # Capability Partner/Owner
    DELIVERY_MANAGER = 5    # Location-based Delivery Manager
    EMPLOYEE = 6

# Fields by sensitivity level
SENSITIVE_FIELDS = {
    "salary", "salary_band", "date_of_birth", "pan_number", "national_id",
    "personal_email", "phone_number", "address", "emergency_contact",
    "medical_info", "performance_notes", "bank_details"
}

SEMI_SENSITIVE_FIELDS = {
    "skill_rating", "years_experience", "certifications", "performance_rating",
    "joining_date", "resume", "project_history", "appraisal_inputs"
}

NON_SENSITIVE_FIELDS = {
    "employee_id", "first_name", "last_name", "name", "company_email",
    "department", "capability", "role", "team", "band", "category",
    "skills", "line_manager_id", "grade"
}

# What each role can see
ROLE_FIELD_ACCESS = {
    RoleID.SYSTEM_ADMIN: SENSITIVE_FIELDS | SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS,
    RoleID.HR: SENSITIVE_FIELDS | SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS,
    RoleID.CAPABILITY_PARTNER: SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS,
    RoleID.DELIVERY_MANAGER: SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS,
    RoleID.LINE_MANAGER: SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS,
    RoleID.EMPLOYEE: NON_SENSITIVE_FIELDS,  # Self gets more via special handling
}

# Employee self-access (what employees can see about themselves)
EMPLOYEE_SELF_ACCESS = SEMI_SENSITIVE_FIELDS | NON_SENSITIVE_FIELDS | {"salary_band"}  # Policy: allow own salary band

def get_accessible_fields(role_id: int, is_self: bool = False) -> Set[str]:
    """Get fields accessible by role"""
    if is_self and role_id == RoleID.EMPLOYEE:
        return EMPLOYEE_SELF_ACCESS
    return ROLE_FIELD_ACCESS.get(role_id, NON_SENSITIVE_FIELDS)

def can_view_employee(viewer_role: int, viewer_id: int, viewer_capability: str,
                      target_employee_id: int, target_capability: str,
                      target_line_manager_id: int, target_dm_id: int) -> bool:
    """Check if viewer can access target employee"""
    # Admin & HR see everyone
    if viewer_role in [RoleID.SYSTEM_ADMIN, RoleID.HR]:
        return True
    # Self
    if viewer_id == target_employee_id:
        return True
    # CP sees own capability only
    if viewer_role == RoleID.CAPABILITY_PARTNER:
        return viewer_capability and viewer_capability == target_capability
    # LM sees direct reports only
    if viewer_role == RoleID.LINE_MANAGER:
        return target_line_manager_id == viewer_id
    # DM sees their delivery unit
    if viewer_role == RoleID.DELIVERY_MANAGER:
        return target_dm_id == viewer_id
    # Employee sees only self
    return False

def mask_fields(data: dict, allowed_fields: Set[str]) -> dict:
    """Mask fields not in allowed set"""
    result = {}
    for key, value in data.items():
        if key in allowed_fields or key in {"id"}:
            result[key] = value
        elif key in SENSITIVE_FIELDS:
            result[key] = "***RESTRICTED***"
        else:
            result[key] = value
    return result

"""Property-based tests for Access Control Service.

**Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
**Validates: Requirements 5.1, 5.2, 5.3, 5.4**
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.access_control import (
    RoleManager, DataClassifier, AccessLogger, PermissionEngine,
    UserRole, DataSensitivity, Permission, ROLE_PERMISSIONS
)


# Hypothesis strategies
user_id_strategy = st.integers(min_value=1, max_value=1000)
role_strategy = st.sampled_from(list(UserRole))
permission_strategy = st.sampled_from(list(Permission))
sensitivity_strategy = st.sampled_from(list(DataSensitivity))
resource_type_strategy = st.sampled_from(["Employee", "Project", "Assignment", "Report", "AuditLog", "User"])
action_strategy = st.sampled_from(["view", "edit", "delete", "export", "approve"])


@given(role=role_strategy, permission=permission_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_role_permission_consistency(role, permission):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.1, 5.2**
    
    For any role, permission checks should be consistent with the permission matrix.
    """
    role_manager = RoleManager()
    
    has_permission = role_manager.has_permission(role, permission)
    expected = permission in ROLE_PERMISSIONS.get(role, set())
    
    assert has_permission == expected


@given(role=role_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_admin_has_all_permissions(role):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.1**
    
    Admin role should have all permissions.
    """
    role_manager = RoleManager()
    
    if role == UserRole.ADMIN:
        for permission in Permission:
            assert role_manager.has_permission(role, permission)


@given(role=role_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_employee_has_minimal_permissions(role):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.3**
    
    Employee role should have minimal permissions (only own data).
    """
    role_manager = RoleManager()
    
    if role == UserRole.EMPLOYEE:
        permissions = role_manager.get_permissions(role)
        
        # Should only have view_own_data and edit_own_data
        assert Permission.VIEW_OWN_DATA in permissions
        assert Permission.EDIT_OWN_DATA in permissions
        
        # Should not have admin permissions
        assert Permission.MANAGE_USERS not in permissions
        assert Permission.MANAGE_ROLES not in permissions
        assert Permission.VIEW_ALL_DATA not in permissions


@given(
    user_id=user_id_strategy,
    resource_type=resource_type_strategy,
    resource_id=st.text(min_size=1, max_size=10),
    action=action_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_access_logging_completeness(user_id, resource_type, resource_id, action):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.2**
    
    All access attempts should be logged with complete information.
    """
    access_logger = AccessLogger()
    data_classifier = DataClassifier()
    
    sensitivity = data_classifier.classify_resource(resource_type)
    
    result = access_logger.log_access(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        data_sensitivity=sensitivity,
        ip_address="127.0.0.1"
    )
    
    assert result == True
    
    # Verify log was recorded
    logs = access_logger.get_logs(user_id=user_id)
    assert len(logs) >= 1
    
    latest_log = logs[-1]
    assert latest_log.user_id == user_id
    assert latest_log.resource_type == resource_type
    assert latest_log.action == action


@given(resource_type=resource_type_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_data_classification_consistency(resource_type):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.4**
    
    Data classification should be consistent for the same resource type.
    """
    classifier = DataClassifier()
    
    sensitivity1 = classifier.classify_resource(resource_type)
    sensitivity2 = classifier.classify_resource(resource_type)
    
    assert sensitivity1 == sensitivity2
    assert sensitivity1 in list(DataSensitivity)


@given(
    role=role_strategy,
    resource_type=resource_type_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_role_data_access_boundaries(role, resource_type):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.3, 5.4**
    
    Each role should only access data within their sensitivity boundary.
    """
    classifier = DataClassifier()
    
    accessible_fields = classifier.get_accessible_fields(role, resource_type)
    
    # All roles should have access to public fields
    assert "name" in accessible_fields
    assert "department" in accessible_fields
    
    # Only admin and HR should have access to restricted fields
    if role in [UserRole.ADMIN, UserRole.HR]:
        # These roles can access restricted data
        pass
    else:
        # Other roles should not access restricted fields
        for field in accessible_fields:
            sensitivity = classifier.classify_field(field)
            if role == UserRole.EMPLOYEE:
                assert sensitivity in [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL]


@given(
    user_id=user_id_strategy,
    resource_type=resource_type_strategy,
    action=action_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_permission_engine_logs_all_access(user_id, resource_type, action):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.2**
    
    Permission engine should log all access attempts regardless of outcome.
    """
    access_logger = AccessLogger()
    engine = PermissionEngine(
        access_logger=access_logger
    )
    
    # Check access (will use default employee role)
    engine.check_access(
        user_id=user_id,
        resource_type=resource_type,
        resource_id="test-123",
        action=action
    )
    
    # Verify access was logged
    logs = access_logger.get_logs(user_id=user_id)
    assert len(logs) >= 1


@given(role=role_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_role_hierarchy_permissions(role):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.1**
    
    Higher roles should have at least the permissions of lower roles.
    """
    role_manager = RoleManager()
    
    employee_perms = role_manager.get_permissions(UserRole.EMPLOYEE)
    
    # All roles should have at least employee permissions
    role_perms = role_manager.get_permissions(role)
    
    for perm in employee_perms:
        assert perm in role_perms, f"Role {role} missing employee permission {perm}"


@given(
    field_name=st.sampled_from([
        "name", "email", "salary", "employee_id", "band", "grade"
    ])
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_field_sensitivity_classification(field_name):
    """
    **Feature: hrms-integration, Property 3: Access Control Boundary Enforcement**
    **Validates: Requirements 5.4**
    
    Field sensitivity should be properly classified.
    """
    classifier = DataClassifier()
    
    sensitivity = classifier.classify_field(field_name)
    
    # Verify known field sensitivities
    if field_name == "name":
        assert sensitivity == DataSensitivity.PUBLIC
    elif field_name == "email":
        assert sensitivity == DataSensitivity.SENSITIVE
    elif field_name == "salary":
        assert sensitivity == DataSensitivity.RESTRICTED
    elif field_name == "employee_id":
        assert sensitivity == DataSensitivity.INTERNAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Test cases for RBAC permissions - US 6.1 to 6.9"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.rbac import Role

client = TestClient(app)

# Test credentials from seed data
USERS = {
    "admin": {"email": "admin@skillboard.com", "password": "Admin@123!"},
    "hr": {"email": "priya.sharma@skillboard.com", "password": "Priya@123!"},
    "cp_eng": {"email": "anita.desai@skillboard.com", "password": "Anita@123!"},
    "cp_ds": {"email": "vikram.patel@skillboard.com", "password": "Vikram@123!"},
    "dm": {"email": "suresh.kumar@skillboard.com", "password": "Suresh@123!"},
    "lm": {"email": "arun.reddy@skillboard.com", "password": "Arun@123!"},
    "emp": {"email": "sanjay.gupta@skillboard.com", "password": "Sanjay@123!"},
    "emp_ds": {"email": "ravi.krishnan@skillboard.com", "password": "Ravi@123!"},
}


def get_token(user_key: str) -> str:
    """Get JWT token for user"""
    response = client.post("/api/auth/login", json=USERS[user_key])
    return response.json()["access_token"]


def auth_header(user_key: str) -> dict:
    return {"Authorization": f"Bearer {get_token(user_key)}"}


class TestUS61_SystemRoles:
    """US 6.1 - Define System Roles"""
    
    def test_all_roles_can_login(self):
        for user_key in USERS:
            response = client.post("/api/auth/login", json=USERS[user_key])
            assert response.status_code == 200, f"{user_key} should be able to login"
    
    def test_role_returned_in_token(self):
        response = client.post("/api/auth/login", json=USERS["hr"])
        assert "role" in response.json()


class TestUS62_DataClassification:
    """US 6.2 - Identify Sensitive vs Non-Sensitive Data"""
    
    def test_sensitive_fields_masked_for_employee(self):
        # Employee viewing another employee
        response = client.get("/api/v2/employees/11", headers=auth_header("emp"))  # Sanjay viewing Neha
        if response.status_code == 200:
            data = response.json()
            assert data.get("salary") in [None, "***REDACTED***"]
            assert data.get("phone_number") in [None, "***REDACTED***"]
    
    def test_sensitive_fields_visible_for_hr(self):
        response = client.get("/api/v2/employees/11", headers=auth_header("hr"))
        assert response.status_code == 200
        data = response.json()
        assert data.get("salary") != "***REDACTED***"


class TestUS63_HRFullAccess:
    """US 6.3 - HR Full Access to Sensitive Employee Data"""
    
    def test_hr_can_view_all_employees(self):
        response = client.get("/api/v2/employees/capability/Engineering", headers=auth_header("hr"))
        assert response.status_code == 200
    
    def test_hr_can_view_sensitive_data(self):
        response = client.get("/api/v2/employees/11", headers=auth_header("hr"))
        assert response.status_code == 200
        data = response.json()
        # HR should see unmasked sensitive fields
        assert "salary" in data


class TestUS64_CPRestrictedAccess:
    """US 6.4 - Restricted Access for CPs based on capability"""
    
    def test_cp_can_view_own_capability(self):
        response = client.get("/api/v2/employees/capability/Engineering", headers=auth_header("cp_eng"))
        assert response.status_code == 200
    
    def test_cp_cannot_view_other_capability(self):
        response = client.get("/api/v2/employees/capability/Data%20Science", headers=auth_header("cp_eng"))
        assert response.status_code == 403
    
    def test_cp_cannot_see_sensitive_data(self):
        response = client.get("/api/v2/employees/capability/Engineering", headers=auth_header("cp_eng"))
        if response.status_code == 200:
            for emp in response.json():
                assert emp.get("salary") in [None, "***REDACTED***"]


class TestUS65_ManagerDirectReports:
    """US 6.5 - Managers see only their direct reports"""
    
    def test_line_manager_sees_direct_reports(self):
        response = client.get("/api/v2/employees/reports/direct", headers=auth_header("lm"))
        assert response.status_code == 200
        # Arun Reddy should see his reports (Sanjay, Neha, Karthik, Mohan, Sneha)
    
    def test_line_manager_cannot_see_other_reports(self):
        # Arun (LM for Engineering team 1) trying to view Ravi (Data Science)
        response = client.get("/api/v2/employees/15", headers=auth_header("lm"))  # Ravi's ID
        assert response.status_code == 403


class TestUS66_EmployeeSelfView:
    """US 6.6 - Employee self-view only"""
    
    def test_employee_can_view_own_profile(self):
        response = client.get("/api/v2/employees/me", headers=auth_header("emp"))
        assert response.status_code == 200
    
    def test_employee_cannot_view_other_employee(self):
        response = client.get("/api/v2/employees/12", headers=auth_header("emp"))  # Neha's ID
        assert response.status_code == 403
    
    def test_employee_sees_own_sensitive_data(self):
        response = client.get("/api/v2/employees/me", headers=auth_header("emp"))
        data = response.json()
        # Employee should see their own salary
        assert data.get("salary") != "***REDACTED***"


class TestUS67_AggregateMetrics:
    """US 6.7 - Aggregate metrics for CP/Senior Management"""
    
    def test_cp_can_view_capability_metrics(self):
        response = client.get("/api/v2/employees/metrics/capability/Engineering", headers=auth_header("cp_eng"))
        assert response.status_code == 200
        data = response.json()
        assert "total_employees" in data
        assert "skill_distribution" in data
    
    def test_employee_cannot_view_metrics(self):
        response = client.get("/api/v2/employees/metrics/capability/Engineering", headers=auth_header("emp"))
        assert response.status_code == 403


class TestUS68_AuditLogging:
    """US 6.8 - Audit log all sensitive data access"""
    
    def test_audit_logs_created_on_sensitive_access(self):
        # HR views employee (triggers audit)
        client.get("/api/v2/employees/11", headers=auth_header("hr"))
        
        # Check audit logs
        response = client.get("/api/v2/employees/audit/logs?limit=5", headers=auth_header("admin"))
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) > 0
    
    def test_employee_cannot_view_audit_logs(self):
        response = client.get("/api/v2/employees/audit/logs", headers=auth_header("emp"))
        assert response.status_code == 403


class TestUS69_GDPRCompliance:
    """US 6.9 - Enforce GDPR-aligned permissions"""
    
    def test_data_minimization_for_cp(self):
        """CP should only see necessary fields"""
        response = client.get("/api/v2/employees/capability/Engineering", headers=auth_header("cp_eng"))
        if response.status_code == 200:
            for emp in response.json():
                # Should not have access to personal contact info
                assert emp.get("personal_email") in [None, "***REDACTED***"]
                assert emp.get("address") in [None, "***REDACTED***"]
    
    def test_audit_log_contains_gdpr_basis(self):
        response = client.get("/api/v2/employees/audit/logs?limit=1", headers=auth_header("admin"))
        if response.status_code == 200 and response.json():
            log = response.json()[0]
            assert "gdpr_basis" in log


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

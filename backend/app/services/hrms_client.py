"""HRMS API client for data synchronization."""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class HRMSClientError(Exception):
    """Base exception for HRMS client errors."""
    pass


class HRMSAuthenticationError(HRMSClientError):
    """Authentication failed with HRMS."""
    pass


class HRMSAPIError(HRMSClientError):
    """API error from HRMS."""
    pass


class HRMSClient:
    """Client for communicating with HRMS API."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'HRMS_BASE_URL', 'http://127.0.0.1:8000')
        self.timeout = getattr(settings, 'HRMS_TIMEOUT', 30)
        self.auth_token = None
        self.token_expires_at = None
        
    async def _authenticate(self) -> str:
        """Authenticate with HRMS and get access token."""
        if self.auth_token and self.token_expires_at and datetime.utcnow().timestamp() < self.token_expires_at:
            return self.auth_token
            
        # HRMS uses OAuth2 form-based authentication
        auth_data = {
            "username": getattr(settings, 'HRMS_INTEGRATION_EMAIL', ''),
            "password": getattr(settings, 'HRMS_INTEGRATION_PASSWORD', '')
        }
        
        if not auth_data["username"] or not auth_data["password"]:
            raise HRMSAuthenticationError("HRMS integration credentials not configured")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use form data (application/x-www-form-urlencoded) for OAuth2 login
                response = await client.post(
                    f"{self.base_url}/users/login",
                    data=auth_data  # Use 'data' for form encoding, not 'json'
                )
                response.raise_for_status()
                
                auth_response = response.json()
                self.auth_token = auth_response.get("access_token")
                
                if not self.auth_token:
                    raise HRMSAuthenticationError("No access token in HRMS response")
                
                # Set token expiration (default 1 hour if not provided)
                expires_in = auth_response.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow().timestamp() + expires_in
                
                logger.info("Successfully authenticated with HRMS")
                return self.auth_token
                
        except httpx.HTTPError as e:
            logger.error(f"HRMS authentication failed: {e}")
            raise HRMSAuthenticationError(f"Failed to authenticate with HRMS: {e}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to HRMS API."""
        token = await self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HRMS API error {e.response.status_code}: {e.response.text}")
            raise HRMSAPIError(f"HRMS API error {e.response.status_code}: {e.response.text}")
        except httpx.HTTPError as e:
            logger.error(f"HRMS request failed: {e}")
            raise HRMSAPIError(f"HRMS request failed: {e}")
    
    # Employee Data Methods
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """Fetch all employees from HRMS."""
        logger.info("Fetching all employees from HRMS")
        response = await self._make_request("GET", "/users/employees")
        # HRMS returns {"count": N, "employees": [...]} - extract the list
        if isinstance(response, dict) and "employees" in response:
            return response["employees"]
        return response if isinstance(response, list) else []
    
    async def get_employee_details(self, employee_id: str) -> Dict[str, Any]:
        """Get specific employee details from HRMS."""
        logger.info(f"Fetching employee details for {employee_id} from HRMS")
        return await self._make_request("GET", f"/users/employee/{employee_id}")
    
    async def get_employee_profile(self, employee_id: str) -> Dict[str, Any]:
        """Get employee profile with managers and HRs from HRMS."""
        logger.info(f"Fetching employee profile for {employee_id} from HRMS")
        return await self._make_request("GET", f"/users/{employee_id}")
    
    async def get_managers_list(self) -> List[Dict[str, Any]]:
        """Get all managers from HRMS."""
        logger.info("Fetching managers list from HRMS")
        return await self._make_request("GET", "/users/managers")
    
    async def get_hrs_list(self) -> List[Dict[str, Any]]:
        """Get all HR personnel from HRMS."""
        logger.info("Fetching HR list from HRMS")
        return await self._make_request("GET", "/users/hrs")
    
    # Project Data Methods
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from HRMS."""
        logger.info("Fetching all projects from HRMS")
        return await self._make_request("GET", "/projects/get_projects")
    
    async def get_manager_employees(self, manager_id: str) -> List[Dict[str, Any]]:
        """Get employees assigned to a specific manager."""
        logger.info(f"Fetching employees for manager {manager_id} from HRMS")
        return await self._make_request("GET", f"/projects/manager-employees?manager_id={manager_id}")
    
    # Allocation Data Methods
    async def get_employee_allocations(self, employee_id: str, month: str) -> Dict[str, Any]:
        """Get employee project allocations for a specific month."""
        logger.info(f"Fetching allocations for employee {employee_id}, month {month} from HRMS")
        return await self._make_request("GET", f"/allocations/summary/{employee_id}/{month}")
    
    async def get_active_projects(self, employee_id: str, month: str) -> List[Dict[str, Any]]:
        """Get active projects for an employee in a specific month."""
        logger.info(f"Fetching active projects for employee {employee_id}, month {month} from HRMS")
        return await self._make_request("GET", f"/attendance/active-projects?employee_id={employee_id}&month={month}")
    
    # Attendance Data Methods
    async def get_employee_attendance(self, employee_id: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Get employee attendance data for a specific month."""
        logger.info(f"Fetching attendance for employee {employee_id}, {year}-{month:02d} from HRMS")
        return await self._make_request("GET", f"/attendance/daily?employee_id={employee_id}&year={year}&month={month}")
    
    async def get_weekly_attendance(self, employee_id: str, week_start: str, week_end: str) -> Dict[str, Any]:
        """Get employee weekly attendance data."""
        logger.info(f"Fetching weekly attendance for employee {employee_id}, {week_start} to {week_end} from HRMS")
        return await self._make_request("GET", f"/attendance/weekly?employee_id={employee_id}&week_start={week_start}&week_end={week_end}")
    
    # Batch Operations
    async def sync_all_data(self) -> Dict[str, Any]:
        """Sync all data from HRMS (employees, projects, allocations)."""
        logger.info("Starting full data sync from HRMS")
        
        results = {
            "employees": [],
            "projects": [],
            "managers": [],
            "hrs": [],
            "errors": []
        }
        
        try:
            # Fetch all core data
            results["employees"] = await self.get_all_employees()
            results["projects"] = await self.get_all_projects()
            results["managers"] = await self.get_managers_list()
            results["hrs"] = await self.get_hrs_list()
            
            logger.info(f"Successfully synced {len(results['employees'])} employees, "
                       f"{len(results['projects'])} projects from HRMS")
            
        except Exception as e:
            logger.error(f"Error during full sync: {e}")
            results["errors"].append(str(e))
        
        return results
    
    # Health Check
    async def health_check(self) -> bool:
        """Check if HRMS API is accessible."""
        try:
            await self._authenticate()
            logger.info("HRMS health check passed")
            return True
        except Exception as e:
            logger.error(f"HRMS health check failed: {e}")
            return False


# Singleton instance
hrms_client = HRMSClient()
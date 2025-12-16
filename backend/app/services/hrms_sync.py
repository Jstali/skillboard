"""HRMS data synchronization service."""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.db import database
from app.db.models import (
    Employee, HRMSProject, HRMSProjectAssignment, HRMSAttendanceRecord,
    HRMSEmployeeSync, HRMSImportLog, AccessLog
)
from app.services.hrms_client import hrms_client, HRMSClientError
from app.db import crud

logger = logging.getLogger(__name__)


class HRMSSyncError(Exception):
    """Base exception for HRMS sync errors."""
    pass


class HRMSDataSync:
    """Service for synchronizing data from HRMS to Skillboard."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = hrms_client
    
    async def sync_all_employees(self) -> Dict[str, Any]:
        """Sync all employees from HRMS to Skillboard."""
        logger.info("Starting employee sync from HRMS")
        
        # Create import log
        import_log = HRMSImportLog(
            import_type="employees",
            import_timestamp=datetime.utcnow(),
            status="in_progress"
        )
        self.db.add(import_log)
        self.db.commit()
        
        try:
            # Fetch employees from HRMS
            hrms_employees = await self.client.get_all_employees()
            
            stats = {
                "processed": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
                "errors": []
            }
            
            for hrms_emp in hrms_employees:
                try:
                    result = await self._sync_single_employee(hrms_emp)
                    stats["processed"] += 1
                    if result["created"]:
                        stats["created
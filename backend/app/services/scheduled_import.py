"""Scheduled Import Service for HRMS data.

This service handles background processing and scheduling of HRMS imports
with retry logic and monitoring capabilities.
"""
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class ImportStatus(str, Enum):
    """Import job status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class ScheduleInterval(str, Enum):
    """Schedule interval options."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ImportJob(BaseModel):
    """Import job details."""
    id: str
    import_type: str
    status: ImportStatus
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0


class ScheduleConfig(BaseModel):
    """Schedule configuration."""
    import_type: str
    interval: ScheduleInterval
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    retry_on_failure: bool = True
    max_retries: int = 3


class RetryPolicy:
    """Retry policy with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt < 0:
            return 0.0
        
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int) -> bool:
        """
        Check if another retry should be attempted.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.max_retries


class ImportScheduler:
    """Manages scheduled import execution."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self._schedules: Dict[str, ScheduleConfig] = {}
        self._jobs: Dict[str, ImportJob] = {}
        self._job_counter = 0
        self._running = False
    
    def add_schedule(self, config: ScheduleConfig) -> bool:
        """
        Add or update a schedule configuration.
        
        Args:
            config: Schedule configuration
            
        Returns:
            True if added successfully
        """
        config.next_run = self._calculate_next_run(config.interval)
        self._schedules[config.import_type] = config
        return True
    
    def remove_schedule(self, import_type: str) -> bool:
        """
        Remove a schedule.
        
        Args:
            import_type: Type of import to remove
            
        Returns:
            True if removed, False if not found
        """
        if import_type in self._schedules:
            del self._schedules[import_type]
            return True
        return False
    
    def get_schedule(self, import_type: str) -> Optional[ScheduleConfig]:
        """Get schedule configuration by import type."""
        return self._schedules.get(import_type)
    
    def get_all_schedules(self) -> List[ScheduleConfig]:
        """Get all schedule configurations."""
        return list(self._schedules.values())
    
    def create_job(self, import_type: str) -> ImportJob:
        """
        Create a new import job.
        
        Args:
            import_type: Type of import
            
        Returns:
            Created ImportJob
        """
        self._job_counter += 1
        job_id = f"job_{self._job_counter}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        job = ImportJob(
            id=job_id,
            import_type=import_type,
            status=ImportStatus.PENDING,
            scheduled_at=datetime.utcnow()
        )
        
        self._jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[ImportJob]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_pending_jobs(self) -> List[ImportJob]:
        """Get all pending jobs."""
        return [j for j in self._jobs.values() if j.status == ImportStatus.PENDING]
    
    def get_due_schedules(self) -> List[ScheduleConfig]:
        """Get schedules that are due for execution."""
        now = datetime.utcnow()
        due = []
        
        for schedule in self._schedules.values():
            if schedule.enabled and schedule.next_run and schedule.next_run <= now:
                due.append(schedule)
        
        return due
    
    def update_job_status(
        self,
        job_id: str,
        status: ImportStatus,
        error_message: Optional[str] = None,
        records_processed: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        records_failed: int = 0
    ) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if failed
            records_processed: Number of records processed
            records_created: Number of records created
            records_updated: Number of records updated
            records_failed: Number of records failed
            
        Returns:
            True if updated successfully
        """
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        job.status = status
        job.error_message = error_message
        job.records_processed = records_processed
        job.records_created = records_created
        job.records_updated = records_updated
        job.records_failed = records_failed
        
        if status == ImportStatus.RUNNING:
            job.started_at = datetime.utcnow()
        elif status in [ImportStatus.SUCCESS, ImportStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        return True
    
    def _calculate_next_run(
        self,
        interval: ScheduleInterval,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """Calculate next run time based on interval."""
        base = from_time or datetime.utcnow()
        
        if interval == ScheduleInterval.HOURLY:
            return base + timedelta(hours=1)
        elif interval == ScheduleInterval.DAILY:
            return base + timedelta(days=1)
        elif interval == ScheduleInterval.WEEKLY:
            return base + timedelta(weeks=1)
        elif interval == ScheduleInterval.MONTHLY:
            return base + timedelta(days=30)
        
        return base + timedelta(days=1)
    
    def mark_schedule_executed(self, import_type: str) -> bool:
        """
        Mark a schedule as executed and calculate next run.
        
        Args:
            import_type: Type of import
            
        Returns:
            True if updated successfully
        """
        schedule = self._schedules.get(import_type)
        if not schedule:
            return False
        
        schedule.last_run = datetime.utcnow()
        schedule.next_run = self._calculate_next_run(schedule.interval)
        return True


class ImportExecutor:
    """Executes import jobs with retry logic."""
    
    def __init__(
        self,
        scheduler: ImportScheduler,
        retry_policy: Optional[RetryPolicy] = None
    ):
        """
        Initialize the executor.
        
        Args:
            scheduler: Import scheduler instance
            retry_policy: Retry policy (default: 3 retries with exponential backoff)
        """
        self.scheduler = scheduler
        self.retry_policy = retry_policy or RetryPolicy()
        self._import_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, import_type: str, handler: Callable) -> None:
        """
        Register an import handler.
        
        Args:
            import_type: Type of import
            handler: Handler function
        """
        self._import_handlers[import_type] = handler
    
    async def execute_job(self, job: ImportJob) -> ImportJob:
        """
        Execute an import job with retry logic.
        
        Args:
            job: Job to execute
            
        Returns:
            Updated job with results
        """
        handler = self._import_handlers.get(job.import_type)
        
        if not handler:
            self.scheduler.update_job_status(
                job.id,
                ImportStatus.FAILED,
                error_message=f"No handler registered for {job.import_type}"
            )
            return self.scheduler.get_job(job.id)
        
        self.scheduler.update_job_status(job.id, ImportStatus.RUNNING)
        
        attempt = 0
        last_error = None
        
        while self.retry_policy.should_retry(attempt):
            try:
                result = await self._run_handler(handler)
                
                self.scheduler.update_job_status(
                    job.id,
                    ImportStatus.SUCCESS,
                    records_processed=result.get('processed', 0),
                    records_created=result.get('created', 0),
                    records_updated=result.get('updated', 0),
                    records_failed=result.get('failed', 0)
                )
                
                # Update schedule
                self.scheduler.mark_schedule_executed(job.import_type)
                
                return self.scheduler.get_job(job.id)
                
            except Exception as e:
                last_error = str(e)
                attempt += 1
                job.retry_count = attempt
                
                if self.retry_policy.should_retry(attempt):
                    self.scheduler.update_job_status(
                        job.id,
                        ImportStatus.RETRYING,
                        error_message=f"Attempt {attempt} failed: {last_error}"
                    )
                    delay = self.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        self.scheduler.update_job_status(
            job.id,
            ImportStatus.FAILED,
            error_message=f"Failed after {attempt} attempts: {last_error}"
        )
        
        return self.scheduler.get_job(job.id)
    
    async def _run_handler(self, handler: Callable) -> Dict[str, Any]:
        """Run the import handler."""
        if asyncio.iscoroutinefunction(handler):
            return await handler()
        else:
            return handler()


class ImportMonitor:
    """Monitors import health and provides metrics."""
    
    def __init__(self, scheduler: ImportScheduler):
        """Initialize the monitor."""
        self.scheduler = scheduler
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        jobs = list(self.scheduler._jobs.values())
        
        total = len(jobs)
        success = len([j for j in jobs if j.status == ImportStatus.SUCCESS])
        failed = len([j for j in jobs if j.status == ImportStatus.FAILED])
        pending = len([j for j in jobs if j.status == ImportStatus.PENDING])
        running = len([j for j in jobs if j.status == ImportStatus.RUNNING])
        
        success_rate = (success / total * 100) if total > 0 else 100.0
        
        return {
            "status": "healthy" if success_rate >= 80 else "degraded",
            "total_jobs": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "running": running,
            "success_rate": success_rate,
            "schedules_active": len([s for s in self.scheduler._schedules.values() if s.enabled])
        }
    
    def get_recent_failures(self, limit: int = 10) -> List[ImportJob]:
        """Get recent failed jobs."""
        failed = [j for j in self.scheduler._jobs.values() if j.status == ImportStatus.FAILED]
        failed.sort(key=lambda j: j.completed_at or datetime.min, reverse=True)
        return failed[:limit]
    
    def get_job_metrics(self) -> Dict[str, Any]:
        """Get job execution metrics."""
        jobs = list(self.scheduler._jobs.values())
        
        if not jobs:
            return {
                "total_records_processed": 0,
                "total_records_created": 0,
                "total_records_updated": 0,
                "total_records_failed": 0,
                "average_processing_time": 0
            }
        
        total_processed = sum(j.records_processed for j in jobs)
        total_created = sum(j.records_created for j in jobs)
        total_updated = sum(j.records_updated for j in jobs)
        total_failed = sum(j.records_failed for j in jobs)
        
        # Calculate average processing time
        completed_jobs = [j for j in jobs if j.started_at and j.completed_at]
        if completed_jobs:
            total_time = sum(
                (j.completed_at - j.started_at).total_seconds()
                for j in completed_jobs
            )
            avg_time = total_time / len(completed_jobs)
        else:
            avg_time = 0
        
        return {
            "total_records_processed": total_processed,
            "total_records_created": total_created,
            "total_records_updated": total_updated,
            "total_records_failed": total_failed,
            "average_processing_time": avg_time
        }


# Factory functions
def get_import_scheduler() -> ImportScheduler:
    """Create an ImportScheduler instance."""
    return ImportScheduler()


def get_import_executor(scheduler: ImportScheduler) -> ImportExecutor:
    """Create an ImportExecutor instance."""
    return ImportExecutor(scheduler)

"""Bulk Operations Service for Performance Optimization.

This service provides bulk database operations for large HRMS imports
with caching and optimized queries.
"""
from typing import List, Dict, Any, Optional, TypeVar, Generic
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    total: int
    created: int
    updated: int
    failed: int
    errors: List[str]
    processing_time_ms: float


class CacheEntry(BaseModel):
    """Cache entry with expiration."""
    key: str
    value: Any
    expires_at: datetime


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if datetime.utcnow() > entry.expires_at:
            del self._cache[key]
            return None
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at
        )
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._cache.items()
            if now > v.expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    @staticmethod
    def make_key(*args) -> str:
        """Create a cache key from arguments."""
        key_str = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


class BulkOperationService:
    """Service for bulk database operations."""
    
    def __init__(self, db: Optional[Session] = None, batch_size: int = 100):
        """
        Initialize bulk operation service.
        
        Args:
            db: Database session
            batch_size: Number of records per batch
        """
        self.db = db
        self.batch_size = batch_size
    
    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        on_conflict: str = "ignore"
    ) -> BulkOperationResult:
        """
        Bulk insert records into a table.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries
            on_conflict: Conflict handling: "ignore", "update", "error"
            
        Returns:
            BulkOperationResult with statistics
        """
        start_time = datetime.utcnow()
        result = BulkOperationResult(
            total=len(records),
            created=0,
            updated=0,
            failed=0,
            errors=[],
            processing_time_ms=0
        )
        
        if not records or not self.db:
            return result
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            try:
                # Use bulk insert
                if batch:
                    columns = list(batch[0].keys())
                    
                    for record in batch:
                        try:
                            # Build insert statement
                            cols = ", ".join(columns)
                            vals = ", ".join([f":{c}" for c in columns])
                            
                            if on_conflict == "ignore":
                                sql = f"INSERT OR IGNORE INTO {table_name} ({cols}) VALUES ({vals})"
                            else:
                                sql = f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"
                            
                            self.db.execute(text(sql), record)
                            result.created += 1
                        except Exception as e:
                            result.failed += 1
                            result.errors.append(str(e))
                    
                    self.db.commit()
                    
            except Exception as e:
                result.failed += len(batch)
                result.errors.append(f"Batch error: {str(e)}")
                self.db.rollback()
        
        end_time = datetime.utcnow()
        result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return result
    
    def bulk_update(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        key_column: str
    ) -> BulkOperationResult:
        """
        Bulk update records in a table.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries (must include key column)
            key_column: Column to use as key for updates
            
        Returns:
            BulkOperationResult with statistics
        """
        start_time = datetime.utcnow()
        result = BulkOperationResult(
            total=len(records),
            created=0,
            updated=0,
            failed=0,
            errors=[],
            processing_time_ms=0
        )
        
        if not records or not self.db:
            return result
        
        for record in records:
            try:
                key_value = record.get(key_column)
                if not key_value:
                    result.failed += 1
                    result.errors.append(f"Missing key column: {key_column}")
                    continue
                
                # Build update statement
                update_cols = [c for c in record.keys() if c != key_column]
                set_clause = ", ".join([f"{c} = :{c}" for c in update_cols])
                
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = :{key_column}"
                
                self.db.execute(text(sql), record)
                result.updated += 1
                
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e))
        
        try:
            self.db.commit()
        except Exception as e:
            result.errors.append(f"Commit error: {str(e)}")
            self.db.rollback()
        
        end_time = datetime.utcnow()
        result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return result
    
    def bulk_upsert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        key_column: str
    ) -> BulkOperationResult:
        """
        Bulk upsert (insert or update) records.
        
        Args:
            table_name: Target table name
            records: List of record dictionaries
            key_column: Column to use as key
            
        Returns:
            BulkOperationResult with statistics
        """
        start_time = datetime.utcnow()
        result = BulkOperationResult(
            total=len(records),
            created=0,
            updated=0,
            failed=0,
            errors=[],
            processing_time_ms=0
        )
        
        if not records or not self.db:
            return result
        
        for record in records:
            try:
                key_value = record.get(key_column)
                if not key_value:
                    result.failed += 1
                    continue
                
                # Check if exists
                check_sql = f"SELECT 1 FROM {table_name} WHERE {key_column} = :{key_column}"
                exists = self.db.execute(text(check_sql), {key_column: key_value}).fetchone()
                
                if exists:
                    # Update
                    update_cols = [c for c in record.keys() if c != key_column]
                    set_clause = ", ".join([f"{c} = :{c}" for c in update_cols])
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = :{key_column}"
                    self.db.execute(text(sql), record)
                    result.updated += 1
                else:
                    # Insert
                    columns = list(record.keys())
                    cols = ", ".join(columns)
                    vals = ", ".join([f":{c}" for c in columns])
                    sql = f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"
                    self.db.execute(text(sql), record)
                    result.created += 1
                    
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e))
        
        try:
            self.db.commit()
        except Exception as e:
            result.errors.append(f"Commit error: {str(e)}")
            self.db.rollback()
        
        end_time = datetime.utcnow()
        result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return result


class CachedQueryService:
    """Service for cached database queries."""
    
    def __init__(self, db: Optional[Session] = None, cache: Optional[SimpleCache] = None):
        """Initialize with database and cache."""
        self.db = db
        self.cache = cache or SimpleCache()
    
    def get_employees_by_capability(
        self,
        capability: str,
        use_cache: bool = True
    ) -> List[Dict]:
        """Get employees by capability with caching."""
        cache_key = self.cache.make_key("employees_capability", capability)
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        if not self.db:
            return []
        
        from app.db.models import Employee
        
        employees = self.db.query(Employee).filter(
            Employee.capability == capability
        ).all()
        
        result = [
            {
                "id": e.id,
                "employee_id": e.employee_id,
                "name": e.name,
                "capability": e.capability,
                "band": e.band
            }
            for e in employees
        ]
        
        if use_cache:
            self.cache.set(cache_key, result, ttl=300)
        
        return result
    
    def get_project_assignments_summary(
        self,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get project assignments summary with caching."""
        cache_key = self.cache.make_key("assignments_summary")
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        if not self.db:
            return {"total": 0, "by_project": {}}
        
        from app.db.models import EmployeeProjectAssignment, Project
        
        assignments = self.db.query(EmployeeProjectAssignment).all()
        
        by_project = {}
        for a in assignments:
            pid = a.project_id
            if pid not in by_project:
                by_project[pid] = {"count": 0, "total_allocation": 0}
            by_project[pid]["count"] += 1
            by_project[pid]["total_allocation"] += a.percentage_allocation or 0
        
        result = {
            "total": len(assignments),
            "by_project": by_project
        }
        
        if use_cache:
            self.cache.set(cache_key, result, ttl=60)
        
        return result
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            count = len(self.cache._cache)
            self.cache.clear()
            return count
        
        # Simple pattern matching
        keys_to_delete = [
            k for k in self.cache._cache.keys()
            if pattern in k
        ]
        
        for key in keys_to_delete:
            self.cache.delete(key)
        
        return len(keys_to_delete)


# Global cache instance
_global_cache = SimpleCache(default_ttl=300)


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _global_cache


def get_bulk_operation_service(db: Session) -> BulkOperationService:
    """Create a BulkOperationService instance."""
    return BulkOperationService(db)


def get_cached_query_service(db: Session) -> CachedQueryService:
    """Create a CachedQueryService instance."""
    return CachedQueryService(db, _global_cache)

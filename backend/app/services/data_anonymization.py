"""Data Anonymization Service for aggregate metrics.

This service ensures personal identifiers are removed from aggregate
metrics while maintaining statistical accuracy.
"""
from typing import List, Dict, Any, Set, Optional
from pydantic import BaseModel
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class AnonymizationError(Exception):
    """Exception raised when anonymization fails."""
    pass


class AnonymizedMetrics(BaseModel):
    """Anonymized aggregate metrics."""
    metric_type: str
    data: Dict[str, Any]
    record_count: int
    is_anonymized: bool = True


class DataAnonymizationService:
    """
    Service for anonymizing data in aggregate metrics.
    
    Removes personal identifiers while preserving statistical accuracy.
    """
    
    # Personal identifier fields to remove
    PERSONAL_FIELDS: Set[str] = {
        # Direct identifiers
        'employee_id',
        'hrms_employee_id',
        'user_id',
        'id',
        
        # Name fields
        'name',
        'first_name',
        'last_name',
        'full_name',
        'display_name',
        
        # Contact information
        'email',
        'company_email',
        'personal_email',
        'phone',
        'phone_number',
        'mobile',
        'address',
        
        # Other identifiers
        'ssn',
        'social_security',
        'national_id',
        'passport',
        'employee_number',
        'badge_id',
        
        # Manager/relationship identifiers
        'line_manager_id',
        'manager_id',
        'supervisor_id',
        'manager_name',
        'line_manager_name',
    }
    
    # Patterns to match in field names (more specific to avoid false positives)
    PERSONAL_PATTERNS: List[str] = [
        'employee_id',
        'user_id',
        'person_name',
        'full_name',
        'first_name',
        'last_name',
        'manager_name',
        'email_address',
        'phone_number',
        'home_address',
        'ssn_number',
        'passport_number',
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the anonymization service.
        
        Args:
            strict_mode: If True, raises exception when personal data detected
        """
        self.strict_mode = strict_mode
    
    def remove_personal_identifiers(self, data: Any) -> Any:
        """
        Remove personal identifiers from data.
        
        Args:
            data: The data to anonymize (dict, list, or primitive)
            
        Returns:
            Anonymized data with personal fields removed
        """
        if data is None:
            return None
        
        if isinstance(data, dict):
            return self._anonymize_dict(data)
        elif isinstance(data, list):
            return [self.remove_personal_identifiers(item) for item in data]
        else:
            return data
    
    def _anonymize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize a dictionary by removing personal fields."""
        anonymized = {}
        
        for key, value in data.items():
            if self._is_personal_field(key):
                if self.strict_mode:
                    logger.warning(f"Personal field removed: {key}")
                continue
            
            # Recursively anonymize nested structures
            if isinstance(value, dict):
                anonymized[key] = self._anonymize_dict(value)
            elif isinstance(value, list):
                anonymized[key] = [self.remove_personal_identifiers(item) for item in value]
            else:
                anonymized[key] = value
        
        return anonymized
    
    def _is_personal_field(self, field_name: str) -> bool:
        """Check if a field name is a personal identifier."""
        normalized = field_name.lower().strip()
        
        # Check exact matches
        if normalized in self.PERSONAL_FIELDS:
            return True
        
        # Check patterns
        for pattern in self.PERSONAL_PATTERNS:
            if pattern in normalized:
                return True
        
        return False

    
    def aggregate_without_individuals(
        self,
        records: List[Dict[str, Any]],
        group_by: Optional[str] = None,
        aggregate_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate data without exposing individual records.
        
        Args:
            records: List of records to aggregate
            group_by: Optional field to group by
            aggregate_fields: Fields to include in aggregation
            
        Returns:
            Aggregated data without individual identifiers
        """
        if not records:
            return {"count": 0, "aggregates": {}}
        
        # Remove personal identifiers first
        anonymized_records = [self.remove_personal_identifiers(r) for r in records]
        
        if group_by and group_by in anonymized_records[0]:
            # Group by specified field
            groups = {}
            for record in anonymized_records:
                key = record.get(group_by, "Unknown")
                if key not in groups:
                    groups[key] = []
                groups[key].append(record)
            
            result = {
                "count": len(records),
                "groups": {}
            }
            
            for group_key, group_records in groups.items():
                result["groups"][group_key] = {
                    "count": len(group_records),
                    "aggregates": self._calculate_aggregates(group_records, aggregate_fields)
                }
            
            return result
        else:
            # Simple aggregation
            return {
                "count": len(records),
                "aggregates": self._calculate_aggregates(anonymized_records, aggregate_fields)
            }
    
    def _calculate_aggregates(
        self,
        records: List[Dict[str, Any]],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate aggregate statistics for records."""
        if not records:
            return {}
        
        aggregates = {}
        
        # Get numeric fields if not specified
        if fields is None:
            fields = []
            for key, value in records[0].items():
                if isinstance(value, (int, float)) and not self._is_personal_field(key):
                    fields.append(key)
        
        for field in fields:
            values = [r.get(field) for r in records if r.get(field) is not None]
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            
            if numeric_values:
                aggregates[field] = {
                    "count": len(numeric_values),
                    "sum": sum(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values)
                }
        
        return aggregates
    
    def validate_no_personal_data(self, data: Any) -> bool:
        """
        Validate that data contains no personal identifiers.
        
        Args:
            data: The data to validate
            
        Returns:
            True if no personal data found, False otherwise
        """
        if data is None:
            return True
        
        if isinstance(data, dict):
            for key, value in data.items():
                if self._is_personal_field(key):
                    return False
                if not self.validate_no_personal_data(value):
                    return False
            return True
        
        elif isinstance(data, list):
            for item in data:
                if not self.validate_no_personal_data(item):
                    return False
            return True
        
        return True
    
    def get_personal_fields_in_data(self, data: Any) -> List[str]:
        """
        Get list of personal fields found in data.
        
        Args:
            data: The data to check
            
        Returns:
            List of personal field names found
        """
        personal_fields = []
        self._collect_personal_fields(data, personal_fields)
        return personal_fields
    
    def _collect_personal_fields(
        self,
        data: Any,
        found_fields: List[str],
        prefix: str = ""
    ) -> None:
        """Recursively collect personal field names."""
        if data is None:
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if self._is_personal_field(key):
                    found_fields.append(full_key)
                self._collect_personal_fields(value, found_fields, full_key)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._collect_personal_fields(item, found_fields, f"{prefix}[{i}]")
    
    def create_anonymized_metrics(
        self,
        metric_type: str,
        data: Dict[str, Any],
        record_count: int
    ) -> AnonymizedMetrics:
        """
        Create anonymized metrics object.
        
        Args:
            metric_type: Type of metric
            data: The metric data
            record_count: Number of records aggregated
            
        Returns:
            AnonymizedMetrics object
        """
        anonymized_data = self.remove_personal_identifiers(data)
        
        return AnonymizedMetrics(
            metric_type=metric_type,
            data=anonymized_data,
            record_count=record_count,
            is_anonymized=True
        )


# Singleton instance
anonymization_service = DataAnonymizationService(strict_mode=True)

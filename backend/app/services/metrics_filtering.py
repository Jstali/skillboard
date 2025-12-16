"""Metrics Filtering Service for filtering aggregate metrics.

This service provides filtering capabilities for metrics by capability,
team, and other criteria.
"""
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel
from copy import deepcopy


class FilterCriteria(BaseModel):
    """Filter criteria for metrics."""
    capability: Optional[str] = None
    team: Optional[str] = None
    band: Optional[str] = None
    department: Optional[str] = None


class FilteredResult(BaseModel):
    """Result of filtered metrics."""
    original_count: int
    filtered_count: int
    filter_applied: Dict[str, Any]
    data: List[Dict[str, Any]]


class MetricsFilteringService:
    """
    Service for filtering metrics data.
    
    Provides filtering by capability, team, and combined criteria.
    """
    
    def filter_by_capability(
        self,
        data: List[Dict[str, Any]],
        capability: str
    ) -> List[Dict[str, Any]]:
        """
        Filter data by capability area.
        
        Args:
            data: List of records to filter
            capability: Capability to filter by
            
        Returns:
            Filtered list of records
        """
        if not capability:
            return data
        
        return [
            record for record in data
            if self._matches_capability(record, capability)
        ]
    
    def _matches_capability(self, record: Dict[str, Any], capability: str) -> bool:
        """Check if record matches capability."""
        cap_lower = capability.lower()
        
        # Check various capability fields
        for field in ['capability', 'home_capability', 'capability_area']:
            if field in record:
                value = record[field]
                if value and str(value).lower() == cap_lower:
                    return True
        
        return False
    
    def filter_by_team(
        self,
        data: List[Dict[str, Any]],
        team: str
    ) -> List[Dict[str, Any]]:
        """
        Filter data by team.
        
        Args:
            data: List of records to filter
            team: Team to filter by
            
        Returns:
            Filtered list of records
        """
        if not team:
            return data
        
        return [
            record for record in data
            if self._matches_team(record, team)
        ]
    
    def _matches_team(self, record: Dict[str, Any], team: str) -> bool:
        """Check if record matches team."""
        team_lower = team.lower()
        
        # Check team field
        if 'team' in record:
            value = record['team']
            if value and str(value).lower() == team_lower:
                return True
        
        return False
    
    def filter_by_criteria(
        self,
        data: List[Dict[str, Any]],
        criteria: FilterCriteria
    ) -> FilteredResult:
        """
        Filter data by multiple criteria.
        
        Args:
            data: List of records to filter
            criteria: Filter criteria to apply
            
        Returns:
            FilteredResult with filtered data and metadata
        """
        original_count = len(data)
        filtered = data
        
        # Apply capability filter
        if criteria.capability:
            filtered = self.filter_by_capability(filtered, criteria.capability)
        
        # Apply team filter
        if criteria.team:
            filtered = self.filter_by_team(filtered, criteria.team)
        
        # Apply band filter
        if criteria.band:
            filtered = self._filter_by_field(filtered, 'band', criteria.band)
        
        # Apply department filter
        if criteria.department:
            filtered = self._filter_by_field(filtered, 'department', criteria.department)
        
        return FilteredResult(
            original_count=original_count,
            filtered_count=len(filtered),
            filter_applied=criteria.model_dump(exclude_none=True),
            data=filtered
        )
    
    def _filter_by_field(
        self,
        data: List[Dict[str, Any]],
        field: str,
        value: str
    ) -> List[Dict[str, Any]]:
        """Filter data by a specific field value."""
        if not value:
            return data
        
        value_lower = value.lower()
        return [
            record for record in data
            if field in record and record[field] and str(record[field]).lower() == value_lower
        ]

    
    def combine_filters(
        self,
        *filter_funcs: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
    ) -> Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Combine multiple filter functions into one.
        
        Args:
            filter_funcs: Filter functions to combine
            
        Returns:
            Combined filter function
        """
        def combined(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            result = data
            for func in filter_funcs:
                result = func(result)
            return result
        
        return combined
    
    def validate_filter_result(
        self,
        original: List[Dict[str, Any]],
        filtered: List[Dict[str, Any]],
        criteria: FilterCriteria
    ) -> bool:
        """
        Validate that filtered results match the criteria.
        
        Args:
            original: Original data
            filtered: Filtered data
            criteria: Applied filter criteria
            
        Returns:
            True if all filtered records match criteria
        """
        for record in filtered:
            if criteria.capability:
                if not self._matches_capability(record, criteria.capability):
                    return False
            
            if criteria.team:
                if not self._matches_team(record, criteria.team):
                    return False
            
            if criteria.band:
                if 'band' not in record or str(record['band']).lower() != criteria.band.lower():
                    return False
            
            if criteria.department:
                if 'department' not in record or str(record['department']).lower() != criteria.department.lower():
                    return False
        
        return True
    
    def get_unique_values(
        self,
        data: List[Dict[str, Any]],
        field: str
    ) -> List[str]:
        """
        Get unique values for a field in the data.
        
        Args:
            data: List of records
            field: Field to get unique values for
            
        Returns:
            List of unique values
        """
        values = set()
        for record in data:
            if field in record and record[field]:
                values.add(str(record[field]))
        
        return sorted(list(values))


# Singleton instance
metrics_filter = MetricsFilteringService()

"""Financial Data Filter Service for excluding financial information from responses.

This service ensures that billing rates, revenue, cost, and other financial
information is never exposed through the Skill Board system.
"""
import logging
from typing import Dict, List, Any, Optional, Set
from copy import deepcopy

logger = logging.getLogger(__name__)


class FinancialDataFilterError(Exception):
    """Exception raised when financial data is detected."""
    pass


class FinancialDataFilter:
    """
    Filters out financial data from all system responses.
    
    This service is critical for maintaining the Skill Board's focus on
    skills and capabilities, explicitly excluding billing and financial information.
    """
    
    # Fields that are explicitly excluded from all responses
    EXCLUDED_FIELDS: Set[str] = {
        # Billing related
        'billing_rate',
        'bill_rate',
        'billable_rate',
        'hourly_rate',
        'daily_rate',
        'rate',
        'billing',
        'billable',
        'unbilled',
        'billed',
        'billing_status',
        
        # Revenue related
        'revenue',
        'total_revenue',
        'monthly_revenue',
        'annual_revenue',
        'revenue_target',
        'revenue_actual',
        'revenue_forecast',
        
        # Cost related
        'cost',
        'total_cost',
        'cost_rate',
        'cost_center_amount',
        'labor_cost',
        'overhead_cost',
        'project_cost',
        'employee_cost',
        
        # Profit related
        'profit',
        'profit_margin',
        'gross_profit',
        'net_profit',
        'margin',
        'markup',
        
        # Budget related
        'budget',
        'budget_amount',
        'budget_remaining',
        'budget_spent',
        'budget_variance',
        
        # Invoice related
        'invoice',
        'invoice_amount',
        'invoice_status',
        'invoiced',
        'invoice_date',
        
        # Financial metrics
        'financial_status',
        'financial_data',
        'financial_metrics',
        'financial_summary',
        'financial_report',
        
        # Salary related (sensitive)
        'salary',
        'base_salary',
        'compensation',
        'bonus',
        'commission',
        'pay_rate',
        'wage',
    }
    
    # Patterns to match in field names (case-insensitive)
    EXCLUDED_PATTERNS: List[str] = [
        'billing',
        'revenue',
        'cost',
        'profit',
        'budget',
        'invoice',
        'financial',
        'salary',
        'compensation',
        'wage',
        'pay_',
        '_pay',
        'rate_',
        '_rate',
        'price',
        'amount',
        'money',
        'dollar',
        'currency',
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the financial data filter.
        
        Args:
            strict_mode: If True, raises exception when financial data is detected.
                        If False, silently removes financial data.
        """
        self.strict_mode = strict_mode
    
    def filter_response(self, data: Any) -> Any:
        """
        Filter financial data from a response.
        
        Args:
            data: The data to filter (dict, list, or primitive)
            
        Returns:
            Filtered data with financial fields removed
        """
        if data is None:
            return None
        
        if isinstance(data, dict):
            return self._filter_dict(data)
        elif isinstance(data, list):
            return [self.filter_response(item) for item in data]
        else:
            return data
    
    def _filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter financial fields from a dictionary."""
        filtered = {}
        
        for key, value in data.items():
            if self._is_financial_field(key):
                if self.strict_mode:
                    logger.warning(f"Financial field detected and removed: {key}")
                continue
            
            # Recursively filter nested structures
            if isinstance(value, dict):
                filtered[key] = self._filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [self.filter_response(item) for item in value]
            else:
                filtered[key] = value
        
        return filtered
    
    def _is_financial_field(self, field_name: str) -> bool:
        """
        Check if a field name is a financial field.
        
        Args:
            field_name: The field name to check
            
        Returns:
            True if the field is financial, False otherwise
        """
        # Normalize field name for comparison
        normalized = field_name.lower().strip()
        
        # Check exact matches
        if normalized in self.EXCLUDED_FIELDS:
            return True
        
        # Check patterns
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern in normalized:
                return True
        
        return False
    
    def validate_no_financial_data(self, data: Any) -> bool:
        """
        Validate that data contains no financial information.
        
        Args:
            data: The data to validate
            
        Returns:
            True if no financial data is present, False otherwise
        """
        if data is None:
            return True
        
        if isinstance(data, dict):
            for key, value in data.items():
                if self._is_financial_field(key):
                    return False
                if not self.validate_no_financial_data(value):
                    return False
            return True
        
        elif isinstance(data, list):
            for item in data:
                if not self.validate_no_financial_data(item):
                    return False
            return True
        
        return True
    
    def get_excluded_fields(self) -> List[str]:
        """
        Get the list of excluded financial fields.
        
        Returns:
            List of field names that are excluded
        """
        return sorted(list(self.EXCLUDED_FIELDS))
    
    def get_excluded_patterns(self) -> List[str]:
        """
        Get the list of excluded patterns.
        
        Returns:
            List of patterns that are excluded
        """
        return sorted(self.EXCLUDED_PATTERNS)
    
    def sanitize_for_export(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize data for export, ensuring no financial information is included.
        
        Args:
            data: List of records to sanitize
            
        Returns:
            Sanitized list of records
        """
        if not data:
            return []
        
        sanitized = []
        for record in data:
            filtered_record = self.filter_response(record)
            sanitized.append(filtered_record)
        
        return sanitized
    
    def validate_schema_field(self, field_name: str) -> bool:
        """
        Validate that a field name is allowed in the schema.
        
        This is used to prevent financial fields from being added to data models.
        
        Args:
            field_name: The field name to validate
            
        Returns:
            True if the field is allowed, False if it's a financial field
        """
        return not self._is_financial_field(field_name)
    
    def get_financial_fields_in_data(self, data: Any) -> List[str]:
        """
        Get a list of financial fields found in the data.
        
        Args:
            data: The data to check
            
        Returns:
            List of financial field names found
        """
        financial_fields = []
        self._collect_financial_fields(data, financial_fields)
        return financial_fields
    
    def _collect_financial_fields(self, data: Any, found_fields: List[str], prefix: str = "") -> None:
        """Recursively collect financial field names."""
        if data is None:
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if self._is_financial_field(key):
                    found_fields.append(full_key)
                self._collect_financial_fields(value, found_fields, full_key)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._collect_financial_fields(item, found_fields, f"{prefix}[{i}]")


# Singleton instance for easy access
financial_filter = FinancialDataFilter(strict_mode=True)
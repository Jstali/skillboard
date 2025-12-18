"""Enhanced HRMS data import service with file parsing and validation."""
import asyncio
import csv
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from io import StringIO

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import (
    Employee, HRMSProject, HRMSProjectAssignment, HRMSImportLog, 
    HRMSConfiguration, HRMSEmployeeSync
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class HRMSImportError(Exception):
    """Base exception for HRMS import errors."""
    pass


class ValidationError(Exception):
    """Data validation error."""
    pass


class FieldMapper:
    """Maps HRMS fields to internal schema."""
    
    # Default field mappings from HRMS to internal schema
    EMPLOYEE_FIELD_MAPPING = {
        'emp_id': 'employee_id',
        'employee_id': 'employee_id',
        'emp_name': 'name',
        'employee_name': 'name',
        'full_name': 'name',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'company_email',
        'company_email': 'company_email',
        'dept': 'department',
        'department': 'department',
        'job_title': 'role',
        'role': 'role',
        'position': 'role',
        'team': 'team',
        'band': 'band',
        'grade': 'band',
        'level': 'band',
        'manager_id': 'line_manager_id',
        'line_manager': 'line_manager_id',
        'supervisor_id': 'line_manager_id',
        'capability': 'home_capability',
        'home_capability': 'home_capability',
        'hire_date': 'hire_date',
        'start_date': 'hire_date',
        'location': 'location_id',
        'location_id': 'location_id',
        'office': 'location_id',
        'active': 'is_active',
        'is_active': 'is_active',
        'status': 'is_active'
    }
    
    PROJECT_FIELD_MAPPING = {
        'project_id': 'hrms_project_id',
        'proj_id': 'hrms_project_id',
        'project_name': 'project_name',
        'proj_name': 'project_name',
        'name': 'project_name',
        'client': 'client_name',
        'client_name': 'client_name',
        'customer': 'client_name',
        'status': 'status',
        'project_status': 'status',
        'start_date': 'start_date',
        'end_date': 'end_date',
        'manager_id': 'project_manager_id',
        'project_manager': 'project_manager_id',
        'pm_id': 'project_manager_id',
        'manager_name': 'project_manager_name',
        'project_manager_name': 'project_manager_name',
        'pm_name': 'project_manager_name'
    }
    
    ASSIGNMENT_FIELD_MAPPING = {
        'employee_id': 'employee_id',
        'emp_id': 'employee_id',
        'project_id': 'project_id',
        'proj_id': 'project_id',
        'allocated_days': 'allocated_days',
        'allocation': 'allocated_days',
        'consumed_days': 'consumed_days',
        'consumed': 'consumed_days',
        'remaining_days': 'remaining_days',
        'remaining': 'remaining_days',
        'allocation_percentage': 'allocation_percentage',
        'percentage': 'allocation_percentage',
        'percent': 'allocation_percentage',
        'month': 'month',
        'period': 'month',
        'is_primary': 'is_primary',
        'primary': 'is_primary',
        'line_manager_id': 'line_manager_id',
        'manager_id': 'line_manager_id',
        'supervisor_id': 'line_manager_id',
        'reporting_manager': 'line_manager_id'
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, Dict[str, str]]] = None):
        """Initialize field mapper with optional custom mappings."""
        self.employee_mapping = self.EMPLOYEE_FIELD_MAPPING.copy()
        self.project_mapping = self.PROJECT_FIELD_MAPPING.copy()
        self.assignment_mapping = self.ASSIGNMENT_FIELD_MAPPING.copy()
        
        if custom_mappings:
            if 'employee' in custom_mappings:
                self.employee_mapping.update(custom_mappings['employee'])
            if 'project' in custom_mappings:
                self.project_mapping.update(custom_mappings['project'])
            if 'assignment' in custom_mappings:
                self.assignment_mapping.update(custom_mappings['assignment'])
    
    def map_employee_fields(self, hrms_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map HRMS employee fields to internal schema."""
        mapped_data = {}
        
        for hrms_field, value in hrms_data.items():
            # Normalize field name (lowercase, remove spaces/underscores)
            normalized_field = hrms_field.lower().replace(' ', '_').replace('-', '_')
            
            if normalized_field in self.employee_mapping:
                internal_field = self.employee_mapping[normalized_field]
                mapped_data[internal_field] = self._convert_value(internal_field, value)
            else:
                # Keep unmapped fields as-is for potential custom processing
                mapped_data[hrms_field] = value
        
        return mapped_data
    
    def map_project_fields(self, hrms_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map HRMS project fields to internal schema."""
        mapped_data = {}
        
        for hrms_field, value in hrms_data.items():
            normalized_field = hrms_field.lower().replace(' ', '_').replace('-', '_')
            
            if normalized_field in self.project_mapping:
                internal_field = self.project_mapping[normalized_field]
                mapped_data[internal_field] = self._convert_value(internal_field, value)
            else:
                mapped_data[hrms_field] = value
        
        return mapped_data
    
    def map_assignment_fields(self, hrms_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map HRMS assignment fields to internal schema."""
        mapped_data = {}
        
        for hrms_field, value in hrms_data.items():
            normalized_field = hrms_field.lower().replace(' ', '_').replace('-', '_')
            
            if normalized_field in self.assignment_mapping:
                internal_field = self.assignment_mapping[normalized_field]
                mapped_data[internal_field] = self._convert_value(internal_field, value)
            else:
                mapped_data[hrms_field] = value
        
        return mapped_data
    
    def _convert_value(self, field_name: str, value: Any) -> Any:
        """Convert value to appropriate type based on field name."""
        if value is None or value == '':
            return None
        
        # Date fields
        if 'date' in field_name.lower():
            return self._parse_date(value)
        
        # Boolean fields
        if field_name in ['is_active', 'is_primary']:
            return self._parse_boolean(value)
        
        # Numeric fields
        if field_name in ['allocated_days', 'consumed_days', 'remaining_days', 'allocation_percentage']:
            return self._parse_float(value)
        
        # String fields - strip whitespace
        if isinstance(value, str):
            return value.strip()
        
        return value
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        
        return None
    
    def _parse_boolean(self, value: Any) -> bool:
        """Parse boolean from various formats."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'active', 'y']
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return False
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float from various formats."""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            try:
                return float(value.replace(',', ''))
            except ValueError:
                return None
        
        return None


class ValidationEngine:
    """Validates HRMS data quality and completeness."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_employee_data(self, employee_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate employee data completeness and quality."""
        errors = []
        
        # Required fields
        required_fields = ['employee_id', 'name']
        for field in required_fields:
            if not employee_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Employee ID format validation
        emp_id = employee_data.get('employee_id')
        if emp_id and not isinstance(emp_id, str):
            errors.append(f"Employee ID must be string, got {type(emp_id)}")
        
        # Email validation
        email = employee_data.get('company_email')
        if email and '@' not in email:
            errors.append(f"Invalid email format: {email}")
        
        # Band validation
        band = employee_data.get('band')
        if band and band not in ['A', 'B', 'C', 'L1', 'L2']:
            errors.append(f"Invalid band: {band}")
        
        # Team validation
        team = employee_data.get('team')
        valid_teams = ['consulting', 'technical_delivery', 'project_programming', 
                      'corporate_functions_it', 'corporate_functions_marketing',
                      'corporate_functions_finance', 'corporate_functions_legal', 
                      'corporate_functions_pc']
        if team and team not in valid_teams:
            errors.append(f"Invalid team: {team}")
        
        return len(errors) == 0, errors
    
    def validate_project_data(self, project_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate project data completeness and quality."""
        errors = []
        
        # Required fields
        required_fields = ['hrms_project_id', 'project_name']
        for field in required_fields:
            if not project_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Status validation
        status = project_data.get('status')
        if status and status not in ['Active', 'Completed', 'On Hold']:
            errors.append(f"Invalid project status: {status}")
        
        # Date validation
        start_date = project_data.get('start_date')
        end_date = project_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            errors.append("Start date cannot be after end date")
        
        return len(errors) == 0, errors
    
    def validate_assignment_data(self, assignment_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate assignment data completeness and quality."""
        errors = []
        
        # Required fields
        required_fields = ['employee_id', 'project_id', 'month']
        for field in required_fields:
            if not assignment_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Allocation percentage validation
        allocation = assignment_data.get('allocation_percentage')
        if allocation is not None and (allocation < 0 or allocation > 100):
            errors.append(f"Allocation percentage must be between 0-100, got {allocation}")
        
        # Days validation
        allocated = assignment_data.get('allocated_days', 0)
        consumed = assignment_data.get('consumed_days', 0)
        if allocated < 0 or consumed < 0:
            errors.append("Days cannot be negative")
        
        if consumed > allocated:
            errors.append("Consumed days cannot exceed allocated days")
        
        # Month format validation
        month = assignment_data.get('month')
        if month and not isinstance(month, str):
            errors.append("Month must be string in YYYY-MM format")
        
        return len(errors) == 0, errors
    
    def calculate_data_quality_score(self, total_records: int, valid_records: int, 
                                   completeness_score: float) -> float:
        """Calculate overall data quality score (0-100)."""
        if total_records == 0:
            return 0.0
        
        validity_score = (valid_records / total_records) * 100
        return (validity_score + completeness_score) / 2


class DataParser:
    """Parses various HRMS file formats."""
    
    def parse_csv_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Parse CSV file and return list of records."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                return [row for row in reader]
        
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path}: {e}")
            raise HRMSImportError(f"Failed to parse CSV file: {e}")
    
    def parse_excel_file(self, file_path: Union[str, Path], sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse Excel file and return list of records."""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            # Clean up NaN values
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)
            
            return cleaned_records
        
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path}: {e}")
            raise HRMSImportError(f"Failed to parse Excel file: {e}")
    
    def parse_json_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Parse JSON file and return list of records."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Handle both single object and array formats
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    raise HRMSImportError("JSON file must contain object or array")
        
        except Exception as e:
            logger.error(f"Error parsing JSON file {file_path}: {e}")
            raise HRMSImportError(f"Failed to parse JSON file: {e}")


class HRMSImportService:
    """Enhanced HRMS import service with file parsing and validation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.field_mapper = FieldMapper()
        self.validation_engine = ValidationEngine()
        self.data_parser = DataParser()
    
    async def import_from_file(self, file_path: Union[str, Path], 
                             import_type: str, 
                             file_format: str = 'auto') -> Dict[str, Any]:
        """Import data from file (CSV, Excel, or JSON)."""
        logger.info(f"Starting file import: {file_path} (type: {import_type})")
        
        # Create import log
        import_log = HRMSImportLog(
            import_type=import_type,
            import_timestamp=datetime.utcnow(),
            status="in_progress"
        )
        self.db.add(import_log)
        self.db.commit()
        
        start_time = datetime.utcnow()
        
        try:
            # Parse file based on format
            if file_format == 'auto':
                file_format = self._detect_file_format(file_path)
            
            if file_format == 'csv':
                records = self.data_parser.parse_csv_file(file_path)
            elif file_format == 'excel':
                records = self.data_parser.parse_excel_file(file_path)
            elif file_format == 'json':
                records = self.data_parser.parse_json_file(file_path)
            else:
                raise HRMSImportError(f"Unsupported file format: {file_format}")
            
            # Process records based on import type
            if import_type == 'employees':
                result = await self._import_employees(records)
            elif import_type == 'projects':
                result = await self._import_projects(records)
            elif import_type == 'assignments':
                result = await self._import_assignments(records)
            else:
                raise HRMSImportError(f"Unsupported import type: {import_type}")
            
            # Update import log
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            import_log.records_processed = result['processed']
            import_log.records_created = result['created']
            import_log.records_updated = result['updated']
            import_log.records_failed = result['failed']
            import_log.status = "success" if result['failed'] == 0 else "partial"
            import_log.processing_time_seconds = processing_time
            import_log.data_quality_score = result.get('quality_score', 0.0)
            
            if result.get('errors'):
                import_log.error_details = json.dumps(result['errors'])
            
            self.db.commit()
            
            logger.info(f"File import completed: {result}")
            return result
        
        except Exception as e:
            # Update import log with error
            import_log.status = "failed"
            import_log.error_details = str(e)
            self.db.commit()
            
            logger.error(f"File import failed: {e}")
            raise
    
    async def _import_employees(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import employee records with band defaulting and line manager handling."""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0, 'errors': [], 'band_defaults_applied': 0}
        valid_records = 0
        
        for record in records:
            try:
                # Map fields
                mapped_data = self.field_mapper.map_employee_fields(record)
                
                # Default band to 'A' if not provided or empty
                if not mapped_data.get('band'):
                    mapped_data['band'] = 'A'
                    stats['band_defaults_applied'] += 1
                    logger.info(f"Applied default band 'A' for employee {mapped_data.get('employee_id')}")
                
                # Validate data
                is_valid, errors = self.validation_engine.validate_employee_data(mapped_data)
                if not is_valid:
                    stats['failed'] += 1
                    stats['errors'].extend(errors)
                    continue
                
                valid_records += 1
                
                # Check if employee exists
                existing_employee = self.db.query(Employee).filter(
                    Employee.employee_id == mapped_data['employee_id']
                ).first()
                
                if existing_employee:
                    # Update existing employee
                    for key, value in mapped_data.items():
                        if hasattr(existing_employee, key):
                            setattr(existing_employee, key, value)
                    # Ensure band is set even for existing employees
                    if not existing_employee.band:
                        existing_employee.band = 'A'
                        stats['band_defaults_applied'] += 1
                    existing_employee.hrms_last_sync = datetime.utcnow()
                    stats['updated'] += 1
                else:
                    # Create new employee with band defaulting
                    if 'band' not in mapped_data or not mapped_data['band']:
                        mapped_data['band'] = 'A'
                    new_employee = Employee(**mapped_data)
                    new_employee.hrms_last_sync = datetime.utcnow()
                    self.db.add(new_employee)
                    stats['created'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"Record {stats['processed'] + stats['failed']}: {str(e)}")
        
        # Calculate quality score
        completeness_score = self._calculate_completeness_score(records, 'employee')
        stats['quality_score'] = self.validation_engine.calculate_data_quality_score(
            len(records), valid_records, completeness_score
        )
        
        self.db.commit()
        return stats
    
    async def _import_projects(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import project records."""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0, 'errors': []}
        valid_records = 0
        
        for record in records:
            try:
                # Map fields
                mapped_data = self.field_mapper.map_project_fields(record)
                
                # Validate data
                is_valid, errors = self.validation_engine.validate_project_data(mapped_data)
                if not is_valid:
                    stats['failed'] += 1
                    stats['errors'].extend(errors)
                    continue
                
                valid_records += 1
                
                # Check if project exists
                existing_project = self.db.query(HRMSProject).filter(
                    HRMSProject.hrms_project_id == mapped_data['hrms_project_id']
                ).first()
                
                if existing_project:
                    # Update existing project
                    for key, value in mapped_data.items():
                        if hasattr(existing_project, key):
                            setattr(existing_project, key, value)
                    existing_project.hrms_last_sync = datetime.utcnow()
                    stats['updated'] += 1
                else:
                    # Create new project
                    new_project = HRMSProject(**mapped_data)
                    new_project.hrms_last_sync = datetime.utcnow()
                    self.db.add(new_project)
                    stats['created'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"Record {stats['processed'] + stats['failed']}: {str(e)}")
        
        # Calculate quality score
        completeness_score = self._calculate_completeness_score(records, 'project')
        stats['quality_score'] = self.validation_engine.calculate_data_quality_score(
            len(records), valid_records, completeness_score
        )
        
        self.db.commit()
        return stats
    
    async def _import_assignments(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Import assignment records with line manager handling from project allocations."""
        stats = {'processed': 0, 'created': 0, 'updated': 0, 'failed': 0, 'errors': [], 'line_managers_updated': 0}
        valid_records = 0
        
        for record in records:
            try:
                # Map fields
                mapped_data = self.field_mapper.map_assignment_fields(record)
                
                # Validate data
                is_valid, errors = self.validation_engine.validate_assignment_data(mapped_data)
                if not is_valid:
                    stats['failed'] += 1
                    stats['errors'].extend(errors)
                    continue
                
                valid_records += 1
                
                # Find employee and project
                employee = self.db.query(Employee).filter(
                    Employee.employee_id == mapped_data['employee_id']
                ).first()
                
                project = self.db.query(HRMSProject).filter(
                    HRMSProject.hrms_project_id == mapped_data['project_id']
                ).first()
                
                if not employee:
                    stats['failed'] += 1
                    stats['errors'].append(f"Employee not found: {mapped_data['employee_id']}")
                    continue
                
                if not project:
                    stats['failed'] += 1
                    stats['errors'].append(f"Project not found: {mapped_data['project_id']}")
                    continue
                
                # Pull line manager from project allocation if provided
                line_manager_id_from_allocation = mapped_data.get('line_manager_id')
                if line_manager_id_from_allocation:
                    # Find the line manager employee
                    line_manager = self.db.query(Employee).filter(
                        Employee.employee_id == line_manager_id_from_allocation
                    ).first()
                    
                    if line_manager and not employee.line_manager_id:
                        # Update employee's line manager from project allocation
                        employee.line_manager_id = line_manager.id
                        stats['line_managers_updated'] += 1
                        logger.info(f"Updated line manager for employee {employee.employee_id} from project allocation to {line_manager.employee_id}")
                
                # Check if assignment exists
                existing_assignment = self.db.query(HRMSProjectAssignment).filter(
                    and_(
                        HRMSProjectAssignment.employee_id == employee.id,
                        HRMSProjectAssignment.project_id == project.id,
                        HRMSProjectAssignment.month == mapped_data['month']
                    )
                ).first()
                
                # Remove line_manager_id from assignment data (it's for employee, not assignment)
                assignment_fields = {k: v for k, v in mapped_data.items() if k != 'line_manager_id'}
                
                if existing_assignment:
                    # Update existing assignment
                    for key, value in assignment_fields.items():
                        if key not in ['employee_id', 'project_id'] and hasattr(existing_assignment, key):
                            setattr(existing_assignment, key, value)
                    existing_assignment.hrms_last_sync = datetime.utcnow()
                    stats['updated'] += 1
                else:
                    # Create new assignment
                    assignment_data = assignment_fields.copy()
                    assignment_data['employee_id'] = employee.id
                    assignment_data['project_id'] = project.id
                    
                    new_assignment = HRMSProjectAssignment(**assignment_data)
                    new_assignment.hrms_last_sync = datetime.utcnow()
                    self.db.add(new_assignment)
                    stats['created'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"Record {stats['processed'] + stats['failed']}: {str(e)}")
        
        # Calculate quality score
        completeness_score = self._calculate_completeness_score(records, 'assignment')
        stats['quality_score'] = self.validation_engine.calculate_data_quality_score(
            len(records), valid_records, completeness_score
        )
        
        self.db.commit()
        return stats
    
    def _detect_file_format(self, file_path: Union[str, Path]) -> str:
        """Detect file format based on extension."""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return 'csv'
        elif extension in ['.xlsx', '.xls']:
            return 'excel'
        elif extension == '.json':
            return 'json'
        else:
            raise HRMSImportError(f"Unsupported file extension: {extension}")
    
    def _calculate_completeness_score(self, records: List[Dict[str, Any]], record_type: str) -> float:
        """Calculate data completeness score."""
        if not records:
            return 0.0
        
        # Define required fields for each record type
        required_fields = {
            'employee': ['employee_id', 'name'],
            'project': ['hrms_project_id', 'project_name'],
            'assignment': ['employee_id', 'project_id', 'month']
        }
        
        fields = required_fields.get(record_type, [])
        if not fields:
            return 100.0
        
        total_fields = len(records) * len(fields)
        complete_fields = 0
        
        for record in records:
            for field in fields:
                if record.get(field):
                    complete_fields += 1
        
        return (complete_fields / total_fields) * 100 if total_fields > 0 else 0.0


class ConfigurationManager:
    """Manages HRMS configuration with encryption for sensitive data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_config(self, key: str, value: str, is_sensitive: bool = False, 
                    description: Optional[str] = None, user_id: Optional[int] = None) -> None:
        """Store configuration value with optional encryption."""
        # Check if config exists
        existing_config = self.db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == key
        ).first()
        
        # Encrypt sensitive values
        stored_value = value
        if is_sensitive:
            stored_value = settings.encrypt_value(value)
        
        if existing_config:
            existing_config.config_value = stored_value
            existing_config.is_encrypted = is_sensitive
            existing_config.description = description
            existing_config.updated_by = user_id
            existing_config.updated_at = datetime.utcnow()
        else:
            new_config = HRMSConfiguration(
                config_key=key,
                config_value=stored_value,
                is_encrypted=is_sensitive,
                description=description,
                updated_by=user_id
            )
            self.db.add(new_config)
        
        self.db.commit()
    
    def get_config(self, key: str) -> Optional[str]:
        """Retrieve configuration value with automatic decryption."""
        config = self.db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == key
        ).first()
        
        if not config:
            return None
        
        if config.is_encrypted:
            try:
                return settings.decrypt_value(config.config_value)
            except Exception as e:
                logger.error(f"Failed to decrypt config {key}: {e}")
                return None
        
        return config.config_value
    
    def get_all_configs(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Get all configuration values."""
        configs = self.db.query(HRMSConfiguration).all()
        result = {}
        
        for config in configs:
            if config.is_encrypted and not include_sensitive:
                result[config.config_key] = "***ENCRYPTED***"
            elif config.is_encrypted:
                try:
                    result[config.config_key] = settings.decrypt_value(config.config_value)
                except Exception:
                    result[config.config_key] = "***DECRYPTION_FAILED***"
            else:
                result[config.config_key] = config.config_value
        
        return result
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration value."""
        config = self.db.query(HRMSConfiguration).filter(
            HRMSConfiguration.config_key == key
        ).first()
        
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        
        return False
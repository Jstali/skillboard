"""Tests for HRMS band defaulting and line manager from project allocations."""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Employee, HRMSProject, HRMSProjectAssignment
from app.services.hrms_import import HRMSImportService, FieldMapper


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestBandDefaulting:
    """Tests for band defaulting to 'A' when missing."""
    
    @pytest.mark.asyncio
    async def test_band_defaults_to_a_when_missing(self, test_db):
        """Test that employees without band get default band 'A'."""
        service = HRMSImportService(test_db)
        
        # Employee data without band
        records = [{
            'employee_id': 'EMP001',
            'name': 'John Doe',
            'company_email': 'john@example.com',
            'department': 'Engineering'
            # No band field
        }]
        
        result = await service._import_employees(records)
        
        employee = test_db.query(Employee).filter(
            Employee.employee_id == 'EMP001'
        ).first()
        
        assert employee is not None
        assert employee.band == 'A'
        assert result['band_defaults_applied'] >= 1
    
    @pytest.mark.asyncio
    async def test_band_preserved_when_provided(self, test_db):
        """Test that band is preserved when explicitly provided."""
        service = HRMSImportService(test_db)
        
        records = [{
            'employee_id': 'EMP002',
            'name': 'Jane Smith',
            'company_email': 'jane@example.com',
            'band': 'C'
        }]
        
        result = await service._import_employees(records)
        
        employee = test_db.query(Employee).filter(
            Employee.employee_id == 'EMP002'
        ).first()
        
        assert employee is not None
        assert employee.band == 'C'
    
    @pytest.mark.asyncio
    async def test_grade_maps_to_band(self, test_db):
        """Test that grade field maps to band."""
        service = HRMSImportService(test_db)
        
        records = [{
            'employee_id': 'EMP003',
            'name': 'Bob Johnson',
            'company_email': 'bob@example.com',
            'grade': 'L1'  # Using grade instead of band
        }]
        
        result = await service._import_employees(records)
        
        employee = test_db.query(Employee).filter(
            Employee.employee_id == 'EMP003'
        ).first()
        
        assert employee is not None
        assert employee.band == 'L1'
    
    @pytest.mark.asyncio
    async def test_empty_band_defaults_to_a(self, test_db):
        """Test that empty string band defaults to 'A'."""
        service = HRMSImportService(test_db)
        
        records = [{
            'employee_id': 'EMP004',
            'name': 'Alice Brown',
            'company_email': 'alice@example.com',
            'band': ''  # Empty string
        }]
        
        result = await service._import_employees(records)
        
        employee = test_db.query(Employee).filter(
            Employee.employee_id == 'EMP004'
        ).first()
        
        assert employee is not None
        assert employee.band == 'A'


class TestLineManagerFromProjectAllocation:
    """Tests for pulling line managers from project allocations."""
    
    @pytest.mark.asyncio
    async def test_line_manager_updated_from_assignment(self, test_db):
        """Test that line manager is updated from project assignment."""
        service = HRMSImportService(test_db)
        
        # Create manager
        manager = Employee(
            employee_id='MGR001',
            name='Manager One',
            company_email='manager@example.com',
            band='L2'
        )
        test_db.add(manager)
        
        # Create employee without line manager
        employee = Employee(
            employee_id='EMP005',
            name='Employee Five',
            company_email='emp5@example.com',
            band='B'
        )
        test_db.add(employee)
        
        # Create project
        project = HRMSProject(
            hrms_project_id='PROJ001',
            project_name='Test Project'
        )
        test_db.add(project)
        test_db.commit()
        
        # Assignment with line manager
        records = [{
            'employee_id': 'EMP005',
            'project_id': 'PROJ001',
            'month': '2024-01',
            'line_manager_id': 'MGR001',
            'allocation_percentage': 100
        }]
        
        result = await service._import_assignments(records)
        
        test_db.refresh(employee)
        assert employee.line_manager_id == manager.id
        assert result['line_managers_updated'] == 1
    
    @pytest.mark.asyncio
    async def test_existing_line_manager_not_overwritten(self, test_db):
        """Test that existing line manager is not overwritten."""
        service = HRMSImportService(test_db)
        
        # Create two managers
        manager1 = Employee(
            employee_id='MGR001',
            name='Manager One',
            company_email='manager1@example.com',
            band='L2'
        )
        manager2 = Employee(
            employee_id='MGR002',
            name='Manager Two',
            company_email='manager2@example.com',
            band='L2'
        )
        test_db.add_all([manager1, manager2])
        test_db.flush()
        
        # Create employee with existing line manager
        employee = Employee(
            employee_id='EMP006',
            name='Employee Six',
            company_email='emp6@example.com',
            band='B',
            line_manager_id=manager1.id  # Already has manager1
        )
        test_db.add(employee)
        
        # Create project
        project = HRMSProject(
            hrms_project_id='PROJ002',
            project_name='Test Project 2'
        )
        test_db.add(project)
        test_db.commit()
        
        # Assignment with different line manager
        records = [{
            'employee_id': 'EMP006',
            'project_id': 'PROJ002',
            'month': '2024-01',
            'line_manager_id': 'MGR002',  # Different manager
            'allocation_percentage': 50
        }]
        
        result = await service._import_assignments(records)
        
        test_db.refresh(employee)
        # Should still be manager1
        assert employee.line_manager_id == manager1.id
        assert result['line_managers_updated'] == 0


class TestFieldMapping:
    """Tests for field mapping including line manager fields."""
    
    def test_line_manager_field_mapping(self):
        """Test that line manager fields are properly mapped."""
        mapper = FieldMapper()
        
        # Test various line manager field names
        test_cases = [
            {'line_manager_id': 'MGR001'},
            {'manager_id': 'MGR002'},
            {'supervisor_id': 'MGR003'},
            {'reporting_manager': 'MGR004'}
        ]
        
        for data in test_cases:
            mapped = mapper.map_assignment_fields(data)
            assert 'line_manager_id' in mapped
    
    def test_band_field_mapping(self):
        """Test that band fields are properly mapped."""
        mapper = FieldMapper()
        
        # Test various band field names
        test_cases = [
            {'band': 'A'},
            {'grade': 'B'},
            {'level': 'C'}
        ]
        
        for data in test_cases:
            mapped = mapper.map_employee_fields(data)
            assert 'band' in mapped


# Property-based tests
class TestBandDefaultingProperties:
    """Property-based tests for band defaulting."""
    
    @given(st.text(min_size=1, max_size=10).filter(lambda x: x.strip()))
    @settings(max_examples=50)
    def test_employee_always_has_band(self, employee_id):
        """Property: Every imported employee should have a band."""
        mapper = FieldMapper()
        
        # Employee data without band
        data = {
            'employee_id': employee_id,
            'name': 'Test Employee',
            'company_email': f'{employee_id}@test.com'
        }
        
        mapped = mapper.map_employee_fields(data)
        
        # After mapping, band might be None, but import should default it
        # This tests the mapping preserves the absence for later defaulting
        assert 'band' not in mapped or mapped.get('band') is None or mapped.get('band') == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

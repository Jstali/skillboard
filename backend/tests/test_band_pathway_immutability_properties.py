"""Property-based tests for Band and Pathway Immutability.

**Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
**Validates: Requirements 1.2, 1.3, 1.5**

For any API request that attempts to directly modify an employee's band or pathway 
field (excluding Level Movement approval), the system should reject the request 
and the employee's band and pathway should remain unchanged.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import Base, Employee, Skill, PathwaySkill
from app.services.band_pathway_service import BandPathwayService, BandPathwayImmutabilityError


@contextmanager
def create_test_db():
    """Create a temporary test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_employee(db, band: str = "B", pathway: str = "Technical"):
    """Create a test employee."""
    employee = Employee(
        employee_id=f"EMP{datetime.now().timestamp()}",
        name="Test Employee",
        company_email="test@example.com",
        band=band,
        pathway=pathway,
        is_active=True
    )
    db.add(employee)
    db.commit()
    return employee


# Test strategies
band_strategy = st.sampled_from(["A", "B", "C", "L1", "L2"])
pathway_strategy = st.sampled_from(["Technical", "SAP", "Cloud", "Data", "Consulting"])


@given(new_band=band_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_band_modification_rejected_outside_level_movement(new_band):
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.2**
    
    Band modification should be rejected when not in Level Movement context.
    """
    with create_test_db() as db:
        employee = create_employee(db, band="A")
        original_band = employee.band
        
        service = BandPathwayService(db)
        
        # Ensure Level Movement context is disabled
        BandPathwayService.disable_level_movement_context()
        
        is_valid, error, _ = service.validate_employee_update(
            employee.id,
            {"band": new_band}
        )
        
        assert is_valid is False
        assert "Level Movement" in error
        
        # Verify band unchanged
        db.refresh(employee)
        assert employee.band == original_band


@given(new_pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pathway_modification_rejected_outside_level_movement(new_pathway):
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.3**
    
    Pathway modification should be rejected when not in Level Movement context.
    """
    with create_test_db() as db:
        employee = create_employee(db, pathway="Technical")
        original_pathway = employee.pathway
        
        service = BandPathwayService(db)
        
        # Ensure Level Movement context is disabled
        BandPathwayService.disable_level_movement_context()
        
        is_valid, error, _ = service.validate_employee_update(
            employee.id,
            {"pathway": new_pathway}
        )
        
        assert is_valid is False
        assert "Level Movement" in error
        
        # Verify pathway unchanged
        db.refresh(employee)
        assert employee.pathway == original_pathway


@given(new_band=band_strategy, new_pathway=pathway_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_band_pathway_allowed_in_level_movement_context(new_band, new_pathway):
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.4**
    
    Band and pathway modification should be allowed in Level Movement context.
    """
    with create_test_db() as db:
        employee = create_employee(db, band="A", pathway="Technical")
        
        service = BandPathwayService(db)
        
        # Enable Level Movement context
        BandPathwayService.enable_level_movement_context()
        
        try:
            is_valid, error, _ = service.validate_employee_update(
                employee.id,
                {"band": new_band, "pathway": new_pathway}
            )
            
            assert is_valid is True
            assert error is None
        finally:
            # Always disable context after test
            BandPathwayService.disable_level_movement_context()


def test_strip_immutable_fields_removes_band_pathway():
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.2, 1.3**
    
    strip_immutable_fields should remove band and pathway when not in Level Movement context.
    """
    with create_test_db() as db:
        service = BandPathwayService(db)
        
        BandPathwayService.disable_level_movement_context()
        
        update_data = {
            "name": "New Name",
            "band": "C",
            "pathway": "Cloud",
            "department": "Engineering"
        }
        
        sanitized = service.strip_immutable_fields(update_data)
        
        assert "name" in sanitized
        assert "department" in sanitized
        assert "band" not in sanitized
        assert "pathway" not in sanitized


def test_strip_immutable_fields_keeps_band_pathway_in_level_movement():
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.4**
    
    strip_immutable_fields should keep band and pathway in Level Movement context.
    """
    with create_test_db() as db:
        service = BandPathwayService(db)
        
        BandPathwayService.enable_level_movement_context()
        
        try:
            update_data = {
                "name": "New Name",
                "band": "C",
                "pathway": "Cloud"
            }
            
            sanitized = service.strip_immutable_fields(update_data)
            
            assert "band" in sanitized
            assert "pathway" in sanitized
        finally:
            BandPathwayService.disable_level_movement_context()


@given(new_band=band_strategy)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_update_band_via_level_movement_succeeds(new_band):
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.4**
    
    update_band_via_level_movement should successfully update band.
    """
    with create_test_db() as db:
        employee = create_employee(db, band="A", pathway="Technical")
        
        service = BandPathwayService(db)
        
        updated = service.update_band_via_level_movement(
            employee.id,
            new_band
        )
        
        assert updated.band == new_band
        assert updated.band_locked_at is not None


def test_band_pathway_status_shows_locked():
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.1**
    
    Band and pathway status should always show as locked.
    """
    with create_test_db() as db:
        employee = create_employee(db)
        
        service = BandPathwayService(db)
        status = service.get_employee_band_pathway_status(employee.id)
        
        assert status["band_locked"] is True
        assert status["pathway_locked"] is True
        assert "Level Movement" in status["message"]


@given(
    other_field=st.sampled_from(["name", "department", "company_email"]),
    other_value=st.text(min_size=1, max_size=50)
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_non_immutable_fields_allowed(other_field, other_value):
    """
    **Feature: manager-skill-assessment, Property 1: Band and Pathway Immutability**
    **Validates: Requirements 1.5**
    
    Non-immutable fields should be allowed to be updated.
    """
    with create_test_db() as db:
        service = BandPathwayService(db)
        
        BandPathwayService.disable_level_movement_context()
        
        # Create employee first
        employee = create_employee(db)
        
        is_valid, error, sanitized = service.validate_employee_update(
            employee.id,
            {other_field: other_value}
        )
        
        assert is_valid is True
        assert error is None
        assert other_field in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

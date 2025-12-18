"""Band and Pathway Immutability Service.

Enforces that employee band and pathway can only be changed through
the Level Movement workflow, not through direct API modifications.

**Validates: Requirements 1.2, 1.3, 1.4, 1.5**
"""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Employee
from app.services.baseline_service import BaselineService


class BandPathwayImmutabilityError(Exception):
    """Raised when attempting to modify band/pathway outside Level Movement."""
    pass


class BandPathwayService:
    """Service for enforcing band/pathway immutability."""
    
    # Internal flag to allow Level Movement service to bypass immutability
    _level_movement_context = False
    
    def __init__(self, db: Session):
        self.db = db
        self.baseline_service = BaselineService(db)
    
    @classmethod
    def enable_level_movement_context(cls):
        """Enable Level Movement context to allow band/pathway updates."""
        cls._level_movement_context = True
    
    @classmethod
    def disable_level_movement_context(cls):
        """Disable Level Movement context."""
        cls._level_movement_context = False
    
    @classmethod
    def is_level_movement_context(cls) -> bool:
        """Check if Level Movement context is active."""
        return cls._level_movement_context
    
    def validate_employee_update(
        self,
        employee_id: int,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate an employee update request for band/pathway immutability.
        
        Args:
            employee_id: The employee's ID
            update_data: Dictionary of fields being updated
            
        Returns:
            Tuple of (is_valid, error_message, sanitized_data)
            - is_valid: True if update is allowed
            - error_message: Error message if not valid
            - sanitized_data: Update data with band/pathway removed if not authorized
        """
        sanitized = update_data.copy()
        
        # Check if band is being modified
        if 'band' in update_data:
            if not self.is_level_movement_context():
                return (
                    False,
                    "Band can only be changed via Level Movement workflow",
                    sanitized
                )
        
        # Check if pathway is being modified
        if 'pathway' in update_data:
            if not self.is_level_movement_context():
                return (
                    False,
                    "Pathway can only be changed via Level Movement workflow",
                    sanitized
                )
        
        return True, None, sanitized
    
    def strip_immutable_fields(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove band and pathway from update data if not in Level Movement context.
        
        Args:
            update_data: Dictionary of fields being updated
            
        Returns:
            Sanitized update data with immutable fields removed
        """
        if self.is_level_movement_context():
            return update_data
        
        sanitized = update_data.copy()
        sanitized.pop('band', None)
        sanitized.pop('pathway', None)
        return sanitized
    
    def update_band_via_level_movement(
        self,
        employee_id: int,
        new_band: str,
        new_pathway: Optional[str] = None
    ) -> Employee:
        """
        Update employee band (and optionally pathway) via Level Movement.
        
        This is the ONLY authorized way to change band/pathway.
        
        Args:
            employee_id: The employee's ID
            new_band: The new band level
            new_pathway: Optional new pathway
            
        Returns:
            Updated Employee object
        """
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        old_band = employee.band
        old_pathway = employee.pathway
        
        # Update band
        employee.band = new_band
        employee.band_locked_at = datetime.utcnow()
        
        # Update pathway if provided
        if new_pathway and new_pathway != old_pathway:
            employee.pathway = new_pathway
            employee.pathway_locked_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(employee)
        
        # Assign baseline assessments for new pathway skills
        if employee.pathway:
            self.baseline_service.assign_baseline(
                employee_id=employee.id,
                band=new_band,
                pathway=employee.pathway,
                skip_existing=True  # Don't overwrite existing assessments
            )
        
        return employee
    
    def get_employee_band_pathway_status(self, employee_id: int) -> Dict[str, Any]:
        """
        Get the band/pathway status for an employee.
        
        Args:
            employee_id: The employee's ID
            
        Returns:
            Dictionary with band, pathway, and lock status
        """
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        return {
            "employee_id": employee.id,
            "band": employee.band,
            "pathway": employee.pathway,
            "band_locked": True,  # Always locked
            "pathway_locked": True,  # Always locked
            "band_locked_at": employee.band_locked_at,
            "pathway_locked_at": employee.pathway_locked_at,
            "message": "Band and pathway can only be changed via Level Movement workflow"
        }


def get_band_pathway_service(db: Session) -> BandPathwayService:
    """Factory function to create BandPathwayService instance."""
    return BandPathwayService(db)

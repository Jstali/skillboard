"""
Capability Owners API endpoints for HRMS pre-integration.
Manages capability groups and their owners.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import database
from app.db.models import CapabilityOwner, Employee, User
from app.schemas import (
    CapabilityOwner as CapabilityOwnerSchema,
    CapabilityOwnerCreate,
    Employee as EmployeeSchema
)
from app.api.rbac import require_role, require_hr
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/capability-owners", tags=["capability-owners"])


@router.post("", response_model=CapabilityOwnerSchema)
async def create_capability_owner(
    capability_owner: CapabilityOwnerCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Create a new capability owner.
    Requires: HR or System Admin role
    """
    # Check if capability already exists
    existing = db.query(CapabilityOwner).filter(
        CapabilityOwner.capability_name == capability_owner.capability_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Capability '{capability_owner.capability_name}' already exists"
        )
    
    # Verify owner employee exists if provided
    if capability_owner.owner_employee_id:
        employee = db.query(Employee).filter(
            Employee.id == capability_owner.owner_employee_id
        ).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Owner employee not found")
    
    db_capability_owner = CapabilityOwner(**capability_owner.dict())
    db.add(db_capability_owner)
    db.commit()
    db.refresh(db_capability_owner)
    return db_capability_owner


@router.get("", response_model=List[CapabilityOwnerSchema])
async def list_capability_owners(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all capability owners.
    Available to all authenticated users.
    """
    capability_owners = db.query(CapabilityOwner).all()
    return capability_owners


@router.get("/{capability_owner_id}", response_model=CapabilityOwnerSchema)
async def get_capability_owner(
    capability_owner_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """Get capability owner details"""
    capability_owner = db.query(CapabilityOwner).filter(
        CapabilityOwner.id == capability_owner_id
    ).first()
    
    if not capability_owner:
        raise HTTPException(status_code=404, detail="Capability owner not found")
    
    return capability_owner


@router.get("/{capability_owner_id}/employees", response_model=List[EmployeeSchema])
async def get_capability_employees(
    capability_owner_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all employees under a capability owner.
    Available to all authenticated users.
    """
    capability_owner = db.query(CapabilityOwner).filter(
        CapabilityOwner.id == capability_owner_id
    ).first()
    
    if not capability_owner:
        raise HTTPException(status_code=404, detail="Capability owner not found")
    
    # Get employees with this capability_owner_id
    employees = db.query(Employee).filter(
        Employee.capability_owner_id == capability_owner_id
    ).all()
    
    return employees


@router.put("/{capability_owner_id}", response_model=CapabilityOwnerSchema)
async def update_capability_owner(
    capability_owner_id: int,
    capability_owner_update: CapabilityOwnerCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_hr)
):
    """
    Update capability owner.
    Requires: HR or System Admin role
    """
    capability_owner = db.query(CapabilityOwner).filter(
        CapabilityOwner.id == capability_owner_id
    ).first()
    
    if not capability_owner:
        raise HTTPException(status_code=404, detail="Capability owner not found")
    
    # Verify new owner employee exists if provided
    if capability_owner_update.owner_employee_id:
        employee = db.query(Employee).filter(
            Employee.id == capability_owner_update.owner_employee_id
        ).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Owner employee not found")
    
    # Update fields
    for field, value in capability_owner_update.dict().items():
        setattr(capability_owner, field, value)
    
    db.commit()
    db.refresh(capability_owner)
    return capability_owner


@router.delete("/{capability_owner_id}")
async def delete_capability_owner(
    capability_owner_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(require_role("System Admin"))
):
    """
    Delete a capability owner.
    Requires: System Admin role
    """
    capability_owner = db.query(CapabilityOwner).filter(
        CapabilityOwner.id == capability_owner_id
    ).first()
    
    if not capability_owner:
        raise HTTPException(status_code=404, detail="Capability owner not found")
    
    db.delete(capability_owner)
    db.commit()
    return {"message": "Capability owner deleted successfully"}

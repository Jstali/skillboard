"""API endpoints for Capability Metrics.

Provides endpoints for aggregate skill metrics, distributions,
coverage analysis, and training needs with role-based access.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.db.database import get_db
from app.db.models import User, Employee
from app.services.metrics_service import (
    MetricsService, SkillDistribution, CoverageMetrics,
    TrainingNeed, MetricsFilter, get_metrics_service
)
from app.services.data_anonymization import anonymization_service
from app.services.financial_filter import financial_filter
from app.api.dependencies import get_current_user, get_hr_or_admin_user, get_cp_user
from app.core.permissions import RoleID

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("/counts", response_model=Dict[str, int])
async def get_skill_counts_by_proficiency(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    team: Optional[str] = Query(None, description="Filter by team"),
    band: Optional[str] = Query(None, description="Filter by band"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill counts grouped by proficiency level.
    
    Returns aggregate counts without personal identifiers.
    
    Access: All authenticated users (aggregate data only)
    """
    service = get_metrics_service(db)
    
    # CPs can only see their capability area
    if current_user.role_id == RoleID.CAPABILITY_PARTNER and not current_user.is_admin:
        user_emp = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
        if user_emp and user_emp.home_capability:
            capability = user_emp.home_capability
    
    filters = MetricsFilter(
        capability=capability,
        team=team,
        band=band
    )
    
    counts = service.get_skill_counts_by_proficiency(filters)
    return counts


@router.get("/distribution", response_model=SkillDistribution)
async def get_capability_distribution(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    db: Session = Depends(get_db)
):
    """
    Get skill distribution for a capability or organisation-wide.
    
    Returns aggregate distribution without personal identifiers.
    """
    service = get_metrics_service(db)
    distribution = service.get_capability_distribution(capability)
    
    return distribution


@router.get("/coverage/{capability}", response_model=CoverageMetrics)
async def get_capability_coverage(
    capability: str,
    db: Session = Depends(get_db)
):
    """
    Get coverage metrics for a specific capability.
    
    Returns coverage percentage and critical gaps.
    """
    service = get_metrics_service(db)
    coverage = service.get_capability_coverage(capability)
    
    return coverage


@router.get("/training-needs/{capability}", response_model=List[TrainingNeed])
async def get_training_needs(
    capability: str,
    db: Session = Depends(get_db)
):
    """
    Get training needs for a capability.
    
    Returns prioritized list of skills needing training.
    """
    service = get_metrics_service(db)
    needs = service.get_training_needs(capability)
    
    return needs

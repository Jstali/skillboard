"""Level Movement Workflow Engine.

This service manages employee level progression and approval workflows
with multi-step approval processes (Manager → CP → HR).
"""
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import (
    Employee, LevelMovementRequest, LevelMovementApprovalAudit,
    EmployeeSkill, RoleRequirement, RatingEnum
)


class WorkflowStatus(str, Enum):
    """Workflow status values."""
    PENDING = "pending"
    MANAGER_APPROVED = "manager_approved"
    CP_APPROVED = "cp_approved"
    HR_APPROVED = "hr_approved"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ApproverRole(str, Enum):
    """Approver roles in workflow."""
    MANAGER = "manager"
    CAPABILITY_PARTNER = "capability_partner"
    HR = "hr"


class ReadinessScore(BaseModel):
    """Readiness assessment result."""
    employee_id: int
    current_level: str
    target_level: str
    score: float  # 0-100
    criteria_met: int
    criteria_total: int
    skill_gaps: List[Dict]
    is_ready: bool


class WorkflowInstance(BaseModel):
    """Workflow instance details."""
    id: int
    employee_id: int
    current_level: str
    target_level: str
    status: WorkflowStatus
    readiness_score: Optional[float]
    current_approver_role: Optional[str]
    initiated_at: datetime
    approvals: List[Dict]


class LevelCriteriaEngine:
    """Evaluates employee readiness against level criteria."""
    
    # Level progression paths
    LEVEL_ORDER = ["A", "B", "C", "L1", "L2"]
    
    # Rating numeric values for comparison
    RATING_VALUES = {
        RatingEnum.BEGINNER: 1,
        RatingEnum.DEVELOPING: 2,
        RatingEnum.INTERMEDIATE: 3,
        RatingEnum.ADVANCED: 4,
        RatingEnum.EXPERT: 5,
    }
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def evaluate_readiness(
        self,
        employee_id: int,
        target_level: str,
        current_level: Optional[str] = None
    ) -> ReadinessScore:
        """
        Evaluate employee readiness for target level.
        
        Args:
            employee_id: Employee ID
            target_level: Target level to evaluate against
            current_level: Current level (optional, will be fetched if not provided)
            
        Returns:
            ReadinessScore with assessment details
        """
        if not self.db:
            # Return mock score for testing
            return ReadinessScore(
                employee_id=employee_id,
                current_level=current_level or "A",
                target_level=target_level,
                score=75.0,
                criteria_met=3,
                criteria_total=4,
                skill_gaps=[],
                is_ready=True
            )
        
        # Get employee
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return ReadinessScore(
                employee_id=employee_id,
                current_level=current_level or "Unknown",
                target_level=target_level,
                score=0.0,
                criteria_met=0,
                criteria_total=0,
                skill_gaps=[],
                is_ready=False
            )
        
        actual_current = current_level or employee.band or "A"
        
        # Get requirements for target level
        requirements = self.db.query(RoleRequirement).filter(
            RoleRequirement.band == target_level
        ).all()
        
        if not requirements:
            return ReadinessScore(
                employee_id=employee_id,
                current_level=actual_current,
                target_level=target_level,
                score=100.0,
                criteria_met=0,
                criteria_total=0,
                skill_gaps=[],
                is_ready=True
            )
        
        # Get employee skills
        employee_skills = self.db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee_id
        ).all()
        
        skill_map = {es.skill_id: es for es in employee_skills}
        
        # Evaluate each requirement
        criteria_met = 0
        criteria_total = len(requirements)
        skill_gaps = []
        
        for req in requirements:
            emp_skill = skill_map.get(req.skill_id)
            
            if emp_skill and emp_skill.rating:
                emp_value = self.RATING_VALUES.get(emp_skill.rating, 0)
                req_value = self.RATING_VALUES.get(req.required_rating, 0)
                
                if emp_value >= req_value:
                    criteria_met += 1
                else:
                    skill_gaps.append({
                        "skill_id": req.skill_id,
                        "required": req.required_rating.value if req.required_rating else None,
                        "current": emp_skill.rating.value if emp_skill.rating else None,
                        "gap": req_value - emp_value
                    })
            else:
                skill_gaps.append({
                    "skill_id": req.skill_id,
                    "required": req.required_rating.value if req.required_rating else None,
                    "current": None,
                    "gap": self.RATING_VALUES.get(req.required_rating, 0)
                })
        
        score = (criteria_met / criteria_total * 100) if criteria_total > 0 else 100.0
        is_ready = score >= 80.0  # 80% threshold for readiness
        
        return ReadinessScore(
            employee_id=employee_id,
            current_level=actual_current,
            target_level=target_level,
            score=score,
            criteria_met=criteria_met,
            criteria_total=criteria_total,
            skill_gaps=skill_gaps,
            is_ready=is_ready
        )
    
    def get_next_level(self, current_level: str) -> Optional[str]:
        """Get the next level in progression."""
        try:
            idx = self.LEVEL_ORDER.index(current_level)
            if idx < len(self.LEVEL_ORDER) - 1:
                return self.LEVEL_ORDER[idx + 1]
        except ValueError:
            pass
        return None
    
    def is_valid_progression(self, current_level: str, target_level: str) -> bool:
        """Check if progression from current to target is valid."""
        try:
            current_idx = self.LEVEL_ORDER.index(current_level)
            target_idx = self.LEVEL_ORDER.index(target_level)
            return target_idx == current_idx + 1
        except ValueError:
            return False


class WorkflowManager:
    """Manages multi-step approval workflows."""
    
    # Approval sequence
    APPROVAL_SEQUENCE = [
        ApproverRole.MANAGER,
        ApproverRole.CAPABILITY_PARTNER,
        ApproverRole.HR
    ]
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
        self.criteria_engine = LevelCriteriaEngine(db)
    
    def initiate_request(
        self,
        employee_id: int,
        target_level: str,
        initiator_id: int
    ) -> WorkflowInstance:
        """
        Initiate a level movement request.
        
        Args:
            employee_id: Employee requesting level change
            target_level: Target level
            initiator_id: User initiating the request
            
        Returns:
            WorkflowInstance with request details
        """
        # Evaluate readiness
        readiness = self.criteria_engine.evaluate_readiness(employee_id, target_level)
        
        if not self.db:
            # Return mock instance for testing
            return WorkflowInstance(
                id=1,
                employee_id=employee_id,
                current_level=readiness.current_level,
                target_level=target_level,
                status=WorkflowStatus.PENDING,
                readiness_score=readiness.score,
                current_approver_role=ApproverRole.MANAGER.value,
                initiated_at=datetime.utcnow(),
                approvals=[]
            )
        
        # Create request in database
        request = LevelMovementRequest(
            employee_id=employee_id,
            current_level=readiness.current_level,
            requested_level=target_level,
            status=WorkflowStatus.PENDING.value,
            readiness_score=readiness.score,
            submission_date=datetime.utcnow()
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        return WorkflowInstance(
            id=request.id,
            employee_id=employee_id,
            current_level=readiness.current_level,
            target_level=target_level,
            status=WorkflowStatus.PENDING,
            readiness_score=readiness.score,
            current_approver_role=ApproverRole.MANAGER.value,
            initiated_at=request.submission_date,
            approvals=[]
        )
    
    def approve(
        self,
        request_id: int,
        approver_id: int,
        approver_role: ApproverRole,
        approved: bool,
        comments: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Process an approval decision.
        
        Args:
            request_id: Request ID
            approver_id: Approver's employee ID
            approver_role: Role of approver
            approved: Whether approved or rejected
            comments: Optional comments
            
        Returns:
            Tuple of (success, message)
        """
        if not self.db:
            return True, "Approval recorded (mock)"
        
        request = self.db.query(LevelMovementRequest).filter(
            LevelMovementRequest.id == request_id
        ).first()
        
        if not request:
            return False, "Request not found"
        
        # Validate approver role matches current stage
        expected_role = self._get_current_approver_role(request.status)
        if expected_role != approver_role:
            return False, f"Expected {expected_role.value} approval, got {approver_role.value}"
        
        # Record approval
        audit = LevelMovementApprovalAudit(
            request_id=request_id,
            approver_id=approver_id,
            approver_role=approver_role.value,
            approval_status="approved" if approved else "rejected",
            comments=comments,
            timestamp=datetime.utcnow()
        )
        self.db.add(audit)
        
        if not approved:
            request.status = WorkflowStatus.REJECTED.value
            request.rejection_reason = comments
            self.db.commit()
            return True, "Request rejected"
        
        # Update status based on approver role
        if approver_role == ApproverRole.MANAGER:
            request.status = WorkflowStatus.MANAGER_APPROVED.value
            request.manager_approval_date = datetime.utcnow()
        elif approver_role == ApproverRole.CAPABILITY_PARTNER:
            request.status = WorkflowStatus.CP_APPROVED.value
            request.cp_approval_date = datetime.utcnow()
        elif approver_role == ApproverRole.HR:
            request.status = WorkflowStatus.HR_APPROVED.value
            request.hr_approval_date = datetime.utcnow()
            # Final approval - update employee level
            self._update_employee_level(request.employee_id, request.requested_level)
        
        self.db.commit()
        return True, f"Approved by {approver_role.value}"
    
    def _get_current_approver_role(self, status: str) -> ApproverRole:
        """Get the expected approver role for current status."""
        status_to_role = {
            WorkflowStatus.PENDING.value: ApproverRole.MANAGER,
            WorkflowStatus.MANAGER_APPROVED.value: ApproverRole.CAPABILITY_PARTNER,
            WorkflowStatus.CP_APPROVED.value: ApproverRole.HR,
        }
        return status_to_role.get(status, ApproverRole.MANAGER)
    
    def _update_employee_level(self, employee_id: int, new_level: str) -> bool:
        """Update employee's level after final approval."""
        if not self.db:
            return True
        
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if employee:
            employee.band = new_level
            self.db.commit()
            return True
        return False
    
    def get_request(self, request_id: int) -> Optional[WorkflowInstance]:
        """Get workflow instance by ID."""
        if not self.db:
            return None
        
        request = self.db.query(LevelMovementRequest).filter(
            LevelMovementRequest.id == request_id
        ).first()
        
        if not request:
            return None
        
        approvals = self.db.query(LevelMovementApprovalAudit).filter(
            LevelMovementApprovalAudit.request_id == request_id
        ).all()
        
        return WorkflowInstance(
            id=request.id,
            employee_id=request.employee_id,
            current_level=request.current_level or "Unknown",
            target_level=request.requested_level,
            status=WorkflowStatus(request.status),
            readiness_score=request.readiness_score,
            current_approver_role=self._get_current_approver_role(request.status).value,
            initiated_at=request.submission_date,
            approvals=[
                {
                    "role": a.approver_role,
                    "status": a.approval_status,
                    "comments": a.comments,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in approvals
            ]
        )
    
    def get_pending_requests(
        self,
        approver_role: Optional[ApproverRole] = None
    ) -> List[WorkflowInstance]:
        """Get pending requests, optionally filtered by approver role."""
        if not self.db:
            return []
        
        query = self.db.query(LevelMovementRequest).filter(
            LevelMovementRequest.status.notin_([
                WorkflowStatus.COMPLETED.value,
                WorkflowStatus.REJECTED.value,
                WorkflowStatus.HR_APPROVED.value
            ])
        )
        
        if approver_role:
            # Filter by status that matches the approver role
            role_to_status = {
                ApproverRole.MANAGER: WorkflowStatus.PENDING.value,
                ApproverRole.CAPABILITY_PARTNER: WorkflowStatus.MANAGER_APPROVED.value,
                ApproverRole.HR: WorkflowStatus.CP_APPROVED.value,
            }
            query = query.filter(
                LevelMovementRequest.status == role_to_status.get(approver_role)
            )
        
        requests = query.all()
        
        return [
            WorkflowInstance(
                id=r.id,
                employee_id=r.employee_id,
                current_level=r.current_level or "Unknown",
                target_level=r.requested_level,
                status=WorkflowStatus(r.status),
                readiness_score=r.readiness_score,
                current_approver_role=self._get_current_approver_role(r.status).value,
                initiated_at=r.submission_date,
                approvals=[]
            )
            for r in requests
        ]


class AuditTracker:
    """Maintains complete progression audit trails."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def get_employee_history(self, employee_id: int) -> List[Dict]:
        """Get complete level movement history for an employee."""
        if not self.db:
            return []
        
        requests = self.db.query(LevelMovementRequest).filter(
            LevelMovementRequest.employee_id == employee_id
        ).order_by(LevelMovementRequest.submission_date.desc()).all()
        
        history = []
        for r in requests:
            approvals = self.db.query(LevelMovementApprovalAudit).filter(
                LevelMovementApprovalAudit.request_id == r.id
            ).order_by(LevelMovementApprovalAudit.timestamp).all()
            
            history.append({
                "request_id": r.id,
                "from_level": r.current_level,
                "to_level": r.requested_level,
                "status": r.status,
                "readiness_score": r.readiness_score,
                "submitted_at": r.submission_date.isoformat(),
                "approvals": [
                    {
                        "role": a.approver_role,
                        "status": a.approval_status,
                        "comments": a.comments,
                        "timestamp": a.timestamp.isoformat()
                    }
                    for a in approvals
                ]
            })
        
        return history


# Factory functions
def get_level_criteria_engine(db: Session) -> LevelCriteriaEngine:
    """Create a LevelCriteriaEngine instance."""
    return LevelCriteriaEngine(db)


def get_workflow_manager(db: Session) -> WorkflowManager:
    """Create a WorkflowManager instance."""
    return WorkflowManager(db)

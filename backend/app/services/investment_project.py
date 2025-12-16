"""Investment Project Classification Service.

This service handles classification of investment projects without
exposing financial details while maintaining assignment visibility.
"""
from typing import List, Dict, Optional, Set
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import Project, HRMSProject, EmployeeProjectAssignment


class ProjectType(str, Enum):
    """Project type classification."""
    BILLABLE = "billable"
    INVESTMENT = "investment"
    INTERNAL = "internal"
    TRAINING = "training"
    BENCH = "bench"


class ProjectClassification(BaseModel):
    """Project classification result."""
    project_id: int
    project_name: str
    project_type: ProjectType
    is_investment: bool
    assignment_visible: bool = True
    # Financial details are explicitly excluded


class InvestmentProjectService:
    """
    Service for classifying and managing investment projects.
    
    Investment projects are flagged appropriately without exposing
    financial details while maintaining assignment visibility.
    """
    
    # Keywords that indicate investment projects
    INVESTMENT_KEYWORDS: Set[str] = {
        "investment",
        "r&d",
        "research",
        "development",
        "innovation",
        "poc",
        "proof of concept",
        "prototype",
        "internal project",
        "internal training",
        "internal",
        "capability building",
        "training project",
        "training",
        "bench",
        "non-billable",
    }
    
    # Project name patterns for investment projects
    INVESTMENT_PATTERNS: List[str] = [
        "inv-",
        "internal-",
        "r&d-",
        "poc-",
        "training-",
        "bench-",
    ]
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize with optional database session."""
        self.db = db
    
    def classify_project(
        self,
        project_id: int,
        project_name: str,
        project_type_hint: Optional[str] = None
    ) -> ProjectClassification:
        """
        Classify a project as investment or billable.
        
        Args:
            project_id: Project ID
            project_name: Project name
            project_type_hint: Optional type hint from HRMS
            
        Returns:
            ProjectClassification with type and visibility
        """
        is_investment = self._is_investment_project(project_name, project_type_hint)
        
        if is_investment:
            project_type = self._determine_investment_type(project_name)
        else:
            project_type = ProjectType.BILLABLE
        
        return ProjectClassification(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            is_investment=is_investment,
            assignment_visible=True  # Assignments always visible
        )
    
    def _is_investment_project(
        self,
        project_name: str,
        type_hint: Optional[str] = None
    ) -> bool:
        """Determine if a project is an investment project."""
        name_lower = project_name.lower()
        
        # Check type hint first
        if type_hint:
            hint_lower = type_hint.lower()
            if any(kw in hint_lower for kw in self.INVESTMENT_KEYWORDS):
                return True
        
        # Check name patterns
        for pattern in self.INVESTMENT_PATTERNS:
            if name_lower.startswith(pattern):
                return True
        
        # Check keywords in name
        for keyword in self.INVESTMENT_KEYWORDS:
            if keyword in name_lower:
                return True
        
        return False
    
    def _determine_investment_type(self, project_name: str) -> ProjectType:
        """Determine specific type of investment project."""
        name_lower = project_name.lower()
        
        if "training" in name_lower:
            return ProjectType.TRAINING
        elif "bench" in name_lower:
            return ProjectType.BENCH
        elif "r&d" in name_lower or "research" in name_lower:
            return ProjectType.INVESTMENT
        elif "internal" in name_lower:
            return ProjectType.INTERNAL
        
        return ProjectType.INVESTMENT
    
    def get_investment_projects(self) -> List[ProjectClassification]:
        """Get all investment projects."""
        if not self.db:
            return []
        
        projects = self.db.query(Project).all()
        
        investment_projects = []
        for project in projects:
            classification = self.classify_project(
                project.id,
                project.name
            )
            if classification.is_investment:
                investment_projects.append(classification)
        
        return investment_projects
    
    def get_employee_investment_assignments(
        self,
        employee_id: int
    ) -> List[Dict]:
        """
        Get investment project assignments for an employee.
        
        Returns assignment details without financial information.
        """
        if not self.db:
            return []
        
        assignments = self.db.query(EmployeeProjectAssignment).filter(
            EmployeeProjectAssignment.employee_id == employee_id
        ).all()
        
        result = []
        for assignment in assignments:
            project = self.db.query(Project).filter(
                Project.id == assignment.project_id
            ).first()
            
            if project:
                classification = self.classify_project(project.id, project.name)
                
                if classification.is_investment:
                    result.append({
                        "assignment_id": assignment.id,
                        "project_id": project.id,
                        "project_name": project.name,
                        "project_type": classification.project_type.value,
                        "is_primary": assignment.is_primary,
                        "allocation_percentage": assignment.percentage_allocation,
                        # No financial details included
                    })
        
        return result
    
    def filter_financial_from_project(self, project_data: Dict) -> Dict:
        """
        Remove any financial information from project data.
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            Filtered project data without financial fields
        """
        financial_fields = {
            "budget", "cost", "revenue", "billing_rate", "profit",
            "invoice", "financial", "rate", "price", "amount"
        }
        
        filtered = {}
        for key, value in project_data.items():
            key_lower = key.lower()
            is_financial = any(f in key_lower for f in financial_fields)
            
            if not is_financial:
                if isinstance(value, dict):
                    filtered[key] = self.filter_financial_from_project(value)
                else:
                    filtered[key] = value
        
        return filtered
    
    def get_project_summary(self) -> Dict:
        """
        Get summary of projects by type.
        
        Returns counts without financial details.
        """
        if not self.db:
            return {
                "total": 0,
                "billable": 0,
                "investment": 0,
                "internal": 0,
                "training": 0,
                "bench": 0
            }
        
        projects = self.db.query(Project).all()
        
        summary = {
            "total": len(projects),
            "billable": 0,
            "investment": 0,
            "internal": 0,
            "training": 0,
            "bench": 0
        }
        
        for project in projects:
            classification = self.classify_project(project.id, project.name)
            
            if classification.project_type == ProjectType.BILLABLE:
                summary["billable"] += 1
            elif classification.project_type == ProjectType.INVESTMENT:
                summary["investment"] += 1
            elif classification.project_type == ProjectType.INTERNAL:
                summary["internal"] += 1
            elif classification.project_type == ProjectType.TRAINING:
                summary["training"] += 1
            elif classification.project_type == ProjectType.BENCH:
                summary["bench"] += 1
        
        return summary


# Factory function
def get_investment_project_service(db: Session) -> InvestmentProjectService:
    """Create an InvestmentProjectService instance."""
    return InvestmentProjectService(db)

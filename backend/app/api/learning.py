"""API routes for learning platform - courses and assignments."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import database
from app.db.models import Course, CourseAssignment, CourseStatusEnum, Employee, Skill, User, EmployeeSkill, RoleRequirement, RatingEnum
from app.api.dependencies import get_current_active_user, get_admin_user
from pydantic import BaseModel
import os
import shutil

router = APIRouter(prefix="/api/learning", tags=["learning"])

# Pydantic models
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    skill_id: Optional[int] = None
    external_url: Optional[str] = None
    is_mandatory: bool = False


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    skill_id: Optional[int]
    skill_name: Optional[str]
    external_url: Optional[str]
    is_mandatory: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CourseAssignmentCreate(BaseModel):
    course_id: int
    employee_ids: List[int]
    due_date: Optional[str] = None  # ISO format string


class CourseAssignmentResponse(BaseModel):
    id: int
    course_id: int
    course_title: str
    course_external_url: Optional[str]
    employee_id: int
    employee_name: str
    assigned_at: datetime
    due_date: Optional[datetime]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    certificate_url: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class CourseAssignmentUpdate(BaseModel):
    status: Optional[CourseStatusEnum] = None
    notes: Optional[str] = None


# Admin endpoints
@router.post("/courses", response_model=CourseResponse)
def create_course(
    course: CourseCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new course (admin only)."""
    # Verify skill exists if provided
    if course.skill_id:
        skill = db.query(Skill).filter(Skill.id == course.skill_id).first()
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
    
    db_course = Course(
        title=course.title,
        description=course.description,
        skill_id=course.skill_id,
        external_url=course.external_url,
        is_mandatory=course.is_mandatory,
        created_by=current_user.id,
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    skill_name = None
    if db_course.skill_id:
        skill = db.query(Skill).filter(Skill.id == db_course.skill_id).first()
        skill_name = skill.name if skill else None
    
    return CourseResponse(
        id=db_course.id,
        title=db_course.title,
        description=db_course.description,
        skill_id=db_course.skill_id,
        skill_name=skill_name,
        external_url=db_course.external_url,
        is_mandatory=db_course.is_mandatory,
        created_at=db_course.created_at,
    )


@router.get("/courses", response_model=List[CourseResponse])
def get_all_courses(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all courses."""
    courses = db.query(Course).all()
    
    result = []
    for course in courses:
        skill_name = None
        if course.skill_id:
            skill = db.query(Skill).filter(Skill.id == course.skill_id).first()
            skill_name = skill.name if skill else None
        
        result.append(CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            skill_id=course.skill_id,
            skill_name=skill_name,
            external_url=course.external_url,
            is_mandatory=course.is_mandatory,
            created_at=course.created_at,
        ))
    
    return result


@router.post("/assignments", response_model=dict)
def assign_course(
    assignment: CourseAssignmentCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Assign a course to employees (admin only)."""
    # Verify course exists
    course = db.query(Course).filter(Course.id == assignment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    assigned_count = 0
    skipped_count = 0
    
    for employee_id in assignment.employee_ids:
        # Verify employee exists
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            skipped_count += 1
            continue
        
        # Check if already assigned
        existing = db.query(CourseAssignment).filter(
            CourseAssignment.employee_id == employee_id,
            CourseAssignment.course_id == assignment.course_id
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Create assignment
        due_date_obj = None
        if assignment.due_date:
            try:
                due_date_obj = datetime.fromisoformat(assignment.due_date.replace('Z', '+00:00'))
            except:
                pass
        
        db_assignment = CourseAssignment(
            course_id=assignment.course_id,
            employee_id=employee_id,
            assigned_by=current_user.id,
            due_date=due_date_obj,
            status=CourseStatusEnum.NOT_STARTED,
        )
        db.add(db_assignment)
        assigned_count += 1
    
    db.commit()
    
    return {
        "message": f"Course assigned to {assigned_count} employees",
        "assigned": assigned_count,
        "skipped": skipped_count,
    }


@router.get("/assignments/all", response_model=List[CourseAssignmentResponse])
def get_all_assignments(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get all course assignments (admin only)."""
    assignments = db.query(CourseAssignment).all()
    
    result = []
    for assignment in assignments:
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
        
        result.append(CourseAssignmentResponse(
            id=assignment.id,
            course_id=assignment.course_id,
            course_title=course.title if course else "Unknown",
            course_external_url=course.external_url if course else None,
            employee_id=assignment.employee_id,
            employee_name=employee.name if employee else "Unknown",
            assigned_at=assignment.assigned_at,
            due_date=assignment.due_date,
            status=assignment.status.value,
            started_at=assignment.started_at,
            completed_at=assignment.completed_at,
            certificate_url=assignment.certificate_url,
            notes=assignment.notes,
        ))
    
    return result


# Employee endpoints
@router.get("/my-assignments", response_model=List[CourseAssignmentResponse])
def get_my_assignments(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get courses assigned to current user."""
    print(f"=== get_my_assignments called for user: {current_user.email} ===")
    
    if not current_user.employee_id:
        print(f"ERROR: User {current_user.email} has no employee_id")
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    print(f"Looking for employee with employee_id: {current_user.employee_id}")
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        print(f"ERROR: No employee found with employee_id: {current_user.employee_id}")
        raise HTTPException(status_code=404, detail="Employee not found")
    
    print(f"Found employee: {employee.name} (id={employee.id})")
    
    assignments = db.query(CourseAssignment).filter(
        CourseAssignment.employee_id == employee.id
    ).all()
    
    print(f"Found {len(assignments)} assignments for employee {employee.id}")
    
    result = []
    for i, assignment in enumerate(assignments):
        try:
            print(f"Processing assignment {i+1}/{len(assignments)}: id={assignment.id}, course_id={assignment.course_id}, status={assignment.status}, status_type={type(assignment.status)}")
            
            course = db.query(Course).filter(Course.id == assignment.course_id).first()
            
            # Handle status - it might be a string or an enum
            status_value = assignment.status
            if hasattr(status_value, 'value'):
                status_str = status_value.value
            else:
                status_str = str(status_value)
            
            print(f"Status converted to: {status_str}")
            
            result.append(CourseAssignmentResponse(
                id=assignment.id,
                course_id=assignment.course_id,
                course_title=course.title if course else "Unknown",
                course_external_url=course.external_url if course else None,
                employee_id=assignment.employee_id,
                employee_name=employee.name,
                assigned_at=assignment.assigned_at,
                due_date=assignment.due_date,
                status=status_str,
                started_at=assignment.started_at,
                completed_at=assignment.completed_at,
                certificate_url=assignment.certificate_url,
                notes=assignment.notes,
            ))
            print(f"Successfully processed assignment {assignment.id}")
        except Exception as e:
            print(f"ERROR processing assignment {assignment.id}: {str(e)}")
            print(f"Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            # Skip this assignment and continue
            continue
    
    print(f"Returning {len(result)} assignments")
    return result


@router.patch("/assignments/{assignment_id}/start")
def start_course(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark course as started."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.id == assignment_id,
        CourseAssignment.employee_id == employee.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.status == CourseStatusEnum.NOT_STARTED:
        assignment.status = CourseStatusEnum.IN_PROGRESS
        assignment.started_at = datetime.utcnow()
        db.commit()
    
    return {"message": "Course started"}


@router.patch("/assignments/{assignment_id}/complete")
async def complete_course(
    assignment_id: int,
    certificate: Optional[UploadFile] = File(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark course as completed and upload certificate."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.id == assignment_id,
        CourseAssignment.employee_id == employee.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Handle certificate upload
    certificate_url = None
    if certificate:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/certificates"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_extension = os.path.splitext(certificate.filename)[1]
        filename = f"{employee.employee_id}_{assignment.course_id}_{datetime.utcnow().timestamp()}{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(certificate.file, buffer)
        
        certificate_url = f"/{file_path}"
    
    # Update assignment
    assignment.status = CourseStatusEnum.COMPLETED
    assignment.completed_at = datetime.utcnow()
    if certificate_url:
        assignment.certificate_url = certificate_url
    if notes:
        assignment.notes = notes
    
    if not assignment.started_at:
        assignment.started_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Course completed successfully", "certificate_url": certificate_url}


@router.patch("/assignments/{assignment_id}")
def update_assignment(
    assignment_id: int,
    update: CourseAssignmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update assignment status or notes."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="User is not linked to an employee")
    
    employee = db.query(Employee).filter(Employee.employee_id == current_user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    assignment = db.query(CourseAssignment).filter(
        CourseAssignment.id == assignment_id,
        CourseAssignment.employee_id == employee.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if update.status:
        assignment.status = update.status
    if update.notes is not None:
        assignment.notes = update.notes
    
    db.commit()
    
    return {"message": "Assignment updated"}


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a course (admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Delete all assignments first
    db.query(CourseAssignment).filter(CourseAssignment.course_id == course_id).delete()
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}


# Helper function to compare skill ratings
def rating_to_level(rating: Optional[RatingEnum]) -> int:
    """Convert rating enum to numeric level for comparison."""
    if rating is None:
        return 0
    rating_levels = {
        RatingEnum.BEGINNER: 1,
        RatingEnum.DEVELOPING: 2,
        RatingEnum.INTERMEDIATE: 3,
        RatingEnum.ADVANCED: 4,
        RatingEnum.EXPERT: 5,
    }
    return rating_levels.get(rating, 0)


# Default required ratings for each band when no specific requirement is defined
BAND_DEFAULT_RATINGS = {
    "A": RatingEnum.BEGINNER,      # 1
    "B": RatingEnum.DEVELOPING,    # 2
    "C": RatingEnum.INTERMEDIATE,   # 3
    "L1": RatingEnum.ADVANCED,     # 4
    "L2": RatingEnum.EXPERT,       # 5
}


@router.post("/auto-assign-by-skill-gap")
def auto_assign_courses_by_skill_gap(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Automatically assign courses to employees based on skill gaps.
    For each employee, if their skill level is below the required level for their band,
    assign all courses mapped to that skill as mandatory learning.
    
    This considers both explicit RoleRequirements AND default band requirements.
    """
    assigned_count = 0
    skipped_count = 0
    assignment_details = []
    
    # Get all employees
    employees = db.query(Employee).all()
    
    for employee in employees:
        if not employee.band:
            continue
        
        # Get explicit role requirements for this employee's band
        role_requirements = db.query(RoleRequirement).filter(
            RoleRequirement.band == employee.band
        ).all()
        
        # Create a set of skill IDs that have explicit requirements
        explicit_skill_ids = {req.skill_id for req in role_requirements}
        
        # Get all employee skills to check against default band requirements
        # EXCLUDE custom skills (is_custom=True) - they are not required for the role
        employee_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id,
            EmployeeSkill.is_interested == False,
            EmployeeSkill.is_custom == False  # Exclude custom skills from gap analysis
        ).all()
        
        # Get interested skills for auto-assignment (user wants to learn these)
        interested_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id,
            EmployeeSkill.is_interested == True
        ).all()
        
        # Get default required rating for this band
        default_required_rating = BAND_DEFAULT_RATINGS.get(employee.band, RatingEnum.INTERMEDIATE)
        
        # Process explicit role requirements
        for requirement in role_requirements:
            # Get employee's current skill level
            employee_skill = db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee.id,
                EmployeeSkill.skill_id == requirement.skill_id
            ).first()
            
            # Skip if this is a custom skill (not required for role)
            if employee_skill and employee_skill.is_custom:
                continue
            
            # Determine if employee is below required level
            current_level = rating_to_level(employee_skill.rating if employee_skill else None)
            required_level = rating_to_level(requirement.required_rating)
            
            if current_level < required_level:
                # Find all courses mapped to this skill
                courses = db.query(Course).filter(
                    Course.skill_id == requirement.skill_id
                ).all()
                
                for course in courses:
                    # Check if already assigned
                    existing = db.query(CourseAssignment).filter(
                        CourseAssignment.employee_id == employee.id,
                        CourseAssignment.course_id == course.id
                    ).first()
                    
                    if not existing:
                        # Create assignment
                        db_assignment = CourseAssignment(
                            course_id=course.id,
                            employee_id=employee.id,
                            assigned_by=current_user.id,
                            status=CourseStatusEnum.NOT_STARTED,
                        )
                        db.add(db_assignment)
                        assigned_count += 1
                        
                        skill = db.query(Skill).filter(Skill.id == requirement.skill_id).first()
                        assignment_details.append({
                            "employee_id": employee.employee_id,
                            "employee_name": employee.name,
                            "course_title": course.title,
                            "skill_name": skill.name if skill else "Unknown",
                            "current_level": employee_skill.rating.value if employee_skill and employee_skill.rating else "None",
                            "required_level": requirement.required_rating.value,
                        })
                    else:
                        skipped_count += 1
        
        # Also check employee skills against default band requirements
        # This handles skills that don't have explicit RoleRequirement records
        for emp_skill in employee_skills:
            # Skip if this skill already has an explicit requirement (already processed above)
            if emp_skill.skill_id in explicit_skill_ids:
                continue
            
            # Check against default band requirement
            current_level = rating_to_level(emp_skill.rating)
            required_level = rating_to_level(default_required_rating)
            
            if current_level < required_level:
                # Find all courses mapped to this skill
                courses = db.query(Course).filter(
                    Course.skill_id == emp_skill.skill_id
                ).all()
                
                for course in courses:
                    # Check if already assigned
                    existing = db.query(CourseAssignment).filter(
                        CourseAssignment.employee_id == employee.id,
                        CourseAssignment.course_id == course.id
                    ).first()
                    
                    if not existing:
                        # Create assignment
                        db_assignment = CourseAssignment(
                            course_id=course.id,
                            employee_id=employee.id,
                            assigned_by=current_user.id,
                            status=CourseStatusEnum.NOT_STARTED,
                        )
                        db.add(db_assignment)
                        assigned_count += 1
                        
                        skill = db.query(Skill).filter(Skill.id == emp_skill.skill_id).first()
                        assignment_details.append({
                            "employee_id": employee.employee_id,
                            "employee_name": employee.name,
                            "course_title": course.title,
                            "skill_name": skill.name if skill else "Unknown",
                            "current_level": emp_skill.rating.value if emp_skill.rating else "None",
                            "required_level": default_required_rating.value,
                        })
                    else:
                        skipped_count += 1
        
        # Auto-assign courses for INTERESTED skills (user wants to learn these)
        for interested_skill in interested_skills:
            # Find all courses mapped to this skill
            courses = db.query(Course).filter(
                Course.skill_id == interested_skill.skill_id
            ).all()
            
            for course in courses:
                # Check if already assigned
                existing = db.query(CourseAssignment).filter(
                    CourseAssignment.employee_id == employee.id,
                    CourseAssignment.course_id == course.id
                ).first()
                
                if not existing:
                    # Create assignment
                    db_assignment = CourseAssignment(
                        course_id=course.id,
                        employee_id=employee.id,
                        assigned_by=current_user.id,
                        status=CourseStatusEnum.NOT_STARTED,
                    )
                    db.add(db_assignment)
                    assigned_count += 1
                    
                    skill = db.query(Skill).filter(Skill.id == interested_skill.skill_id).first()
                    assignment_details.append({
                        "employee_id": employee.employee_id,
                        "employee_name": employee.name,
                        "course_title": course.title,
                        "skill_name": skill.name if skill else "Unknown",
                        "current_level": "Interested",
                        "required_level": "Learning Goal",
                        "reason": "interested_skill",
                    })
                else:
                    skipped_count += 1
    
    db.commit()
    
    return {
        "message": f"Auto-assigned {assigned_count} courses based on skill gaps and interests",
        "assigned": assigned_count,
        "skipped": skipped_count,
        "details": assignment_details,
    }


@router.post("/auto-assign-for-employee/{employee_id}")
def auto_assign_courses_for_employee(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Automatically assign courses to a specific employee based on their skill gaps.
    This considers both explicit RoleRequirements AND default band requirements.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if not employee.band:
        raise HTTPException(status_code=400, detail="Employee has no band assigned")
    
    assigned_count = 0
    skipped_count = 0
    assignment_details = []
    
    # Get explicit role requirements for this employee's band
    role_requirements = db.query(RoleRequirement).filter(
        RoleRequirement.band == employee.band
    ).all()
    
    # Create a set of skill IDs that have explicit requirements
    explicit_skill_ids = {req.skill_id for req in role_requirements}
    
    # Get all employee skills to check against default band requirements
    # EXCLUDE custom skills (is_custom=True) - they are not required for the role
    employee_skills = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == employee.id,
        EmployeeSkill.is_interested == False,
        EmployeeSkill.is_custom == False  # Exclude custom skills from gap analysis
    ).all()
    
    # Get interested skills for auto-assignment (user wants to learn these)
    interested_skills = db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == employee.id,
        EmployeeSkill.is_interested == True
    ).all()
    
    # Get default required rating for this band
    default_required_rating = BAND_DEFAULT_RATINGS.get(employee.band, RatingEnum.INTERMEDIATE)
    
    # Process explicit role requirements
    for requirement in role_requirements:
        # Get employee's current skill level
        employee_skill = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id,
            EmployeeSkill.skill_id == requirement.skill_id
        ).first()
        
        # Skip if this is a custom skill (not required for role)
        if employee_skill and employee_skill.is_custom:
            continue
        
        # Determine if employee is below required level
        current_level = rating_to_level(employee_skill.rating if employee_skill else None)
        required_level = rating_to_level(requirement.required_rating)
        
        if current_level < required_level:
            # Find all courses mapped to this skill
            courses = db.query(Course).filter(
                Course.skill_id == requirement.skill_id
            ).all()
            
            for course in courses:
                # Check if already assigned
                existing = db.query(CourseAssignment).filter(
                    CourseAssignment.employee_id == employee.id,
                    CourseAssignment.course_id == course.id
                ).first()
                
                if not existing:
                    # Create assignment
                    db_assignment = CourseAssignment(
                        course_id=course.id,
                        employee_id=employee.id,
                        assigned_by=current_user.id,
                        status=CourseStatusEnum.NOT_STARTED,
                    )
                    db.add(db_assignment)
                    assigned_count += 1
                    
                    skill = db.query(Skill).filter(Skill.id == requirement.skill_id).first()
                    assignment_details.append({
                        "course_title": course.title,
                        "skill_name": skill.name if skill else "Unknown",
                        "current_level": employee_skill.rating.value if employee_skill and employee_skill.rating else "None",
                        "required_level": requirement.required_rating.value,
                    })
                else:
                    skipped_count += 1
    
    # Also check employee skills against default band requirements
    for emp_skill in employee_skills:
        # Skip if this skill already has an explicit requirement
        if emp_skill.skill_id in explicit_skill_ids:
            continue
        
        # Check against default band requirement
        current_level = rating_to_level(emp_skill.rating)
        required_level = rating_to_level(default_required_rating)
        
        if current_level < required_level:
            # Find all courses mapped to this skill
            courses = db.query(Course).filter(
                Course.skill_id == emp_skill.skill_id
            ).all()
            
            for course in courses:
                # Check if already assigned
                existing = db.query(CourseAssignment).filter(
                    CourseAssignment.employee_id == employee.id,
                    CourseAssignment.course_id == course.id
                ).first()
                
                if not existing:
                    # Create assignment
                    db_assignment = CourseAssignment(
                        course_id=course.id,
                        employee_id=employee.id,
                        assigned_by=current_user.id,
                        status=CourseStatusEnum.NOT_STARTED,
                    )
                    db.add(db_assignment)
                    assigned_count += 1
                    
                    skill = db.query(Skill).filter(Skill.id == emp_skill.skill_id).first()
                    assignment_details.append({
                        "course_title": course.title,
                        "skill_name": skill.name if skill else "Unknown",
                        "current_level": emp_skill.rating.value if emp_skill.rating else "None",
                        "required_level": default_required_rating.value,
                    })
                else:
                    skipped_count += 1
    
    # Auto-assign courses for INTERESTED skills (user wants to learn these)
    for interested_skill in interested_skills:
        # Find all courses mapped to this skill
        courses = db.query(Course).filter(
            Course.skill_id == interested_skill.skill_id
        ).all()
        
        for course in courses:
            # Check if already assigned
            existing = db.query(CourseAssignment).filter(
                CourseAssignment.employee_id == employee.id,
                CourseAssignment.course_id == course.id
            ).first()
            
            if not existing:
                # Create assignment
                db_assignment = CourseAssignment(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=current_user.id,
                    status=CourseStatusEnum.NOT_STARTED,
                )
                db.add(db_assignment)
                assigned_count += 1
                
                skill = db.query(Skill).filter(Skill.id == interested_skill.skill_id).first()
                assignment_details.append({
                    "course_title": course.title,
                    "skill_name": skill.name if skill else "Unknown",
                    "current_level": "Interested",
                    "required_level": "Learning Goal",
                    "reason": "interested_skill",
                })
            else:
                skipped_count += 1
    
    db.commit()
    
    return {
        "message": f"Auto-assigned {assigned_count} courses to {employee.name}",
        "assigned": assigned_count,
        "skipped": skipped_count,
        "details": assignment_details,
    }


@router.get("/skill-gap-report")
def get_skill_gap_report(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Get a report of all employees with skill gaps and available courses.
    This considers both explicit RoleRequirements AND default band requirements.
    """
    report = []
    
    # Get all employees
    employees = db.query(Employee).all()
    
    for employee in employees:
        if not employee.band:
            continue
        
        employee_gaps = []
        
        # Get explicit role requirements for this employee's band
        role_requirements = db.query(RoleRequirement).filter(
            RoleRequirement.band == employee.band
        ).all()
        
        # Create a set of skill IDs that have explicit requirements
        explicit_skill_ids = {req.skill_id for req in role_requirements}
        
        # Get all employee skills - EXCLUDE custom skills from gap analysis
        employee_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id,
            EmployeeSkill.is_interested == False,
            EmployeeSkill.is_custom == False  # Exclude custom skills from gap analysis
        ).all()
        
        # Get default required rating for this band
        default_required_rating = BAND_DEFAULT_RATINGS.get(employee.band, RatingEnum.INTERMEDIATE)
        
        # Process explicit role requirements
        for requirement in role_requirements:
            # Get employee's current skill level
            employee_skill = db.query(EmployeeSkill).filter(
                EmployeeSkill.employee_id == employee.id,
                EmployeeSkill.skill_id == requirement.skill_id
            ).first()
            
            # Skip if employee doesn't have this skill at all (no rating)
            # We only show gaps for skills the employee has started learning
            if not employee_skill or not employee_skill.rating:
                continue
            
            # Skip if this is a custom skill (not required for role)
            if employee_skill.is_custom:
                continue
            
            # Determine if employee is below required level
            current_level = rating_to_level(employee_skill.rating)
            required_level = rating_to_level(requirement.required_rating)
            
            if current_level < required_level:
                # Find all courses mapped to this skill
                courses = db.query(Course).filter(
                    Course.skill_id == requirement.skill_id
                ).all()
                
                skill = db.query(Skill).filter(Skill.id == requirement.skill_id).first()
                
                # Check assignment status
                assigned_courses = []
                available_courses = []
                
                for course in courses:
                    assignment = db.query(CourseAssignment).filter(
                        CourseAssignment.employee_id == employee.id,
                        CourseAssignment.course_id == course.id
                    ).first()
                    
                    if assignment:
                        assigned_courses.append({
                            "course_id": course.id,
                            "course_title": course.title,
                            "status": assignment.status.value,
                        })
                    else:
                        available_courses.append({
                            "course_id": course.id,
                            "course_title": course.title,
                        })
                
                employee_gaps.append({
                    "skill_id": requirement.skill_id,
                    "skill_name": skill.name if skill else "Unknown",
                    "current_level": employee_skill.rating.value if employee_skill and employee_skill.rating else "None",
                    "required_level": requirement.required_rating.value,
                    "assigned_courses": assigned_courses,
                    "available_courses": available_courses,
                })
        
        # Also check employee skills against default band requirements
        for emp_skill in employee_skills:
            # Skip if this skill already has an explicit requirement
            if emp_skill.skill_id in explicit_skill_ids:
                continue
            
            # Check against default band requirement
            current_level = rating_to_level(emp_skill.rating)
            required_level = rating_to_level(default_required_rating)
            
            if current_level < required_level:
                # Find all courses mapped to this skill
                courses = db.query(Course).filter(
                    Course.skill_id == emp_skill.skill_id
                ).all()
                
                skill = db.query(Skill).filter(Skill.id == emp_skill.skill_id).first()
                
                # Check assignment status
                assigned_courses = []
                available_courses = []
                
                for course in courses:
                    assignment = db.query(CourseAssignment).filter(
                        CourseAssignment.employee_id == employee.id,
                        CourseAssignment.course_id == course.id
                    ).first()
                    
                    if assignment:
                        assigned_courses.append({
                            "course_id": course.id,
                            "course_title": course.title,
                            "status": assignment.status.value,
                        })
                    else:
                        available_courses.append({
                            "course_id": course.id,
                            "course_title": course.title,
                        })
                
                employee_gaps.append({
                    "skill_id": emp_skill.skill_id,
                    "skill_name": skill.name if skill else "Unknown",
                    "current_level": emp_skill.rating.value if emp_skill.rating else "None",
                    "required_level": default_required_rating.value,
                    "assigned_courses": assigned_courses,
                    "available_courses": available_courses,
                })
        
        # Get interested skills for this employee
        interested_skills_list = []
        interested_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == employee.id,
            EmployeeSkill.is_interested == True
        ).all()
        
        for interested_skill in interested_skills:
            skill = db.query(Skill).filter(Skill.id == interested_skill.skill_id).first()
            
            # Find courses for this interested skill
            courses = db.query(Course).filter(
                Course.skill_id == interested_skill.skill_id
            ).all()
            
            assigned_courses = []
            available_courses = []
            
            for course in courses:
                assignment = db.query(CourseAssignment).filter(
                    CourseAssignment.employee_id == employee.id,
                    CourseAssignment.course_id == course.id
                ).first()
                
                if assignment:
                    assigned_courses.append({
                        "course_id": course.id,
                        "course_title": course.title,
                        "status": assignment.status.value,
                    })
                else:
                    available_courses.append({
                        "course_id": course.id,
                        "course_title": course.title,
                    })
            
            interested_skills_list.append({
                "skill_id": interested_skill.skill_id,
                "skill_name": skill.name if skill else "Unknown",
                "assigned_courses": assigned_courses,
                "available_courses": available_courses,
            })
        
        if employee_gaps or interested_skills_list:
            report.append({
                "employee_id": employee.id,
                "employee_name": employee.name,
                "band": employee.band,
                "skill_gaps": employee_gaps,
                "interested_skills": interested_skills_list,
            })
    
    return report


@router.get("/debug-skill-gaps")
def debug_skill_gaps(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Debug endpoint to check why skill gaps might not be showing.
    """
    debug_info = {
        "employees": [],
        "courses_with_skills": [],
        "role_requirements": [],
    }
    
    # Get all employees with their bands
    employees = db.query(Employee).all()
    for emp in employees[:10]:  # Limit to 10 for debugging
        emp_skills = db.query(EmployeeSkill).filter(
            EmployeeSkill.employee_id == emp.id
        ).all()
        
        skills_info = []
        for es in emp_skills:
            skill = db.query(Skill).filter(Skill.id == es.skill_id).first()
            skills_info.append({
                "skill_id": es.skill_id,
                "skill_name": skill.name if skill else "Unknown",
                "rating": es.rating.value if es.rating else None,
                "is_interested": es.is_interested,
            })
        
        default_req = BAND_DEFAULT_RATINGS.get(emp.band, RatingEnum.INTERMEDIATE) if emp.band else None
        
        debug_info["employees"].append({
            "id": emp.id,
            "employee_id": emp.employee_id,
            "name": emp.name,
            "band": emp.band,
            "default_required_rating": default_req.value if default_req else None,
            "skills_count": len(emp_skills),
            "skills": skills_info[:5],  # Limit to 5 skills
        })
    
    # Get courses with skill mappings
    courses = db.query(Course).filter(Course.skill_id.isnot(None)).all()
    for course in courses:
        skill = db.query(Skill).filter(Skill.id == course.skill_id).first()
        debug_info["courses_with_skills"].append({
            "course_id": course.id,
            "course_title": course.title,
            "skill_id": course.skill_id,
            "skill_name": skill.name if skill else "Unknown",
        })
    
    # Get role requirements
    requirements = db.query(RoleRequirement).all()
    for req in requirements:
        skill = db.query(Skill).filter(Skill.id == req.skill_id).first()
        debug_info["role_requirements"].append({
            "band": req.band,
            "skill_id": req.skill_id,
            "skill_name": skill.name if skill else "Unknown",
            "required_rating": req.required_rating.value,
        })
    
    return debug_info

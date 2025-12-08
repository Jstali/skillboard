#!/usr/bin/env python3
"""Script to create sample courses and assign them to employees."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Course, CourseAssignment, Employee, User, CourseStatusEnum
from datetime import datetime

def create_sample_courses():
    db = SessionLocal()
    try:
        # Get admin user
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            print("ERROR: No admin user found")
            return
        
        print(f"Using admin user: {admin.email}")
        
        # Sample courses with real external links
        courses_data = [
            {
                "title": "Google Cloud Associate Cloud Engineer Certification",
                "description": "Prepare for the Google Cloud Associate Cloud Engineer certification. Learn to deploy applications, monitor operations, and manage enterprise solutions.",
                "external_url": "https://www.cloudskillsboost.google/paths/11",
                "is_mandatory": True
            },
            {
                "title": "AWS Certified Solutions Architect - Associate",
                "description": "Master AWS services and architecture. Learn to design distributed systems on AWS.",
                "external_url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
                "is_mandatory": True
            },
            {
                "title": "Python for Data Science - Coursera",
                "description": "Learn Python programming for data science and machine learning applications.",
                "external_url": "https://www.coursera.org/specializations/python-data-science",
                "is_mandatory": False
            },
            {
                "title": "Docker and Kubernetes Complete Guide",
                "description": "Master containerization with Docker and orchestration with Kubernetes.",
                "external_url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
                "is_mandatory": False
            }
        ]
        
        created_courses = []
        for course_data in courses_data:
            # Check if course already exists
            existing = db.query(Course).filter(Course.title == course_data["title"]).first()
            if existing:
                print(f"Course already exists: {course_data['title']}")
                created_courses.append(existing)
                continue
            
            # Create course
            course = Course(
                title=course_data["title"],
                description=course_data["description"],
                external_url=course_data["external_url"],
                is_mandatory=course_data["is_mandatory"],
                created_by=admin.id
            )
            db.add(course)
            db.flush()
            created_courses.append(course)
            print(f"✓ Created course: {course.title}")
        
        db.commit()
        
        # Assign mandatory courses to all employees
        employees = db.query(Employee).all()
        print(f"\nAssigning mandatory courses to {len(employees)} employees...")
        
        assigned_count = 0
        for course in created_courses:
            if not course.is_mandatory:
                continue
                
            for employee in employees:
                # Check if already assigned
                existing = db.query(CourseAssignment).filter(
                    CourseAssignment.course_id == course.id,
                    CourseAssignment.employee_id == employee.id
                ).first()
                
                if existing:
                    continue
                
                # Create assignment
                assignment = CourseAssignment(
                    course_id=course.id,
                    employee_id=employee.id,
                    assigned_by=admin.id,
                    status=CourseStatusEnum.NOT_STARTED
                )
                db.add(assignment)
                assigned_count += 1
        
        db.commit()
        print(f"✓ Created {assigned_count} course assignments")
        
        print("\n" + "="*60)
        print("SUMMARY:")
        print("="*60)
        for course in created_courses:
            print(f"\n📚 {course.title}")
            print(f"   Mandatory: {'Yes' if course.is_mandatory else 'No'}")
            print(f"   Link: {course.external_url}")
            
            if course.is_mandatory:
                count = db.query(CourseAssignment).filter(
                    CourseAssignment.course_id == course.id
                ).count()
                print(f"   Assigned to: {count} employees")
        
        print("\n✅ All done! Employees can now see their assigned courses in the Learning section.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_courses()

"""
Create test employees for Skillboard testing
"""
import psycopg2
from passlib.context import CryptContext
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_employees():
    print("Creating test employees for Skillboard...")
    
    # Test employees with different departments and bands
    employees = [
        {
            "employee_id": "EMP001",
            "name": "John Smith",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@company.com",
            "department": "Engineering",
            "role": "Senior Developer",
            "team": "technical_delivery",
            "band": "B",
            "category": "Technical"
        },
        {
            "employee_id": "EMP002",
            "name": "Sarah Johnson",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@company.com",
            "department": "Engineering",
            "role": "Tech Lead",
            "team": "technical_delivery",
            "band": "L1",
            "category": "Technical"
        },
        {
            "employee_id": "EMP003",
            "name": "Mike Chen",
            "first_name": "Mike",
            "last_name": "Chen",
            "email": "mike.chen@company.com",
            "department": "Consulting",
            "role": "Consultant",
            "team": "consulting",
            "band": "A",
            "category": "Consulting"
        },
        {
            "employee_id": "EMP004",
            "name": "Emily Davis",
            "first_name": "Emily",
            "last_name": "Davis",
            "email": "emily.davis@company.com",
            "department": "Engineering",
            "role": "Junior Developer",
            "team": "technical_delivery",
            "band": "A",
            "category": "Technical"
        },
        {
            "employee_id": "EMP005",
            "name": "David Wilson",
            "first_name": "David",
            "last_name": "Wilson",
            "email": "david.wilson@company.com",
            "department": "Data Science",
            "role": "Data Scientist",
            "team": "technical_delivery",
            "band": "B",
            "category": "Technical"
        },
    ]
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("\n1. Creating employees...")
        for emp in employees:
            try:
                cur.execute("""
                    INSERT INTO employees (
                        employee_id, name, first_name, last_name, company_email,
                        department, role, team, band, category
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        company_email = EXCLUDED.company_email,
                        department = EXCLUDED.department,
                        role = EXCLUDED.role,
                        team = EXCLUDED.team,
                        band = EXCLUDED.band,
                        category = EXCLUDED.category
                """, (
                    emp["employee_id"], emp["name"], emp["first_name"], emp["last_name"],
                    emp["email"], emp["department"], emp["role"], emp["team"],
                    emp["band"], emp["category"]
                ))
                print(f"   ✅ {emp['name']} ({emp['employee_id']}) - {emp['role']}")
            except Exception as e:
                print(f"   ⚠️  {emp['name']}: {e}")
        
        print("\n2. Creating user accounts for employees...")
        default_password = "password123"
        password_hash = pwd_context.hash(default_password)
        
        for emp in employees:
            try:
                cur.execute("""
                    INSERT INTO users (
                        employee_id, email, password_hash, is_active, is_admin, 
                        must_change_password, role_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET
                        employee_id = EXCLUDED.employee_id,
                        is_active = EXCLUDED.is_active
                """, (
                    emp["employee_id"], emp["email"], password_hash,
                    True, False, False, 6, datetime.utcnow()
                ))
                print(f"   ✅ User account: {emp['email']}")
            except Exception as e:
                print(f"   ⚠️  {emp['email']}: {e}")
        
        # Count total employees
        cur.execute("SELECT COUNT(*) FROM employees")
        total = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Test employees created successfully!")
        print(f"\n📊 Total employees in database: {total}")
        print("\n" + "="*60)
        print("TEST EMPLOYEE LOGIN CREDENTIALS:")
        print("="*60)
        print("Email: john.smith@company.com")
        print("Email: sarah.johnson@company.com")
        print("Email: mike.chen@company.com")
        print("Email: emily.davis@company.com")
        print("Email: david.wilson@company.com")
        print(f"\nPassword for all: {default_password}")
        print("="*60)
        print("\n✅ You can now test Skillboard features with these employees!")
        print("   - Login as any employee")
        print("   - Assign skill templates")
        print("   - Fill out skill assessments")
        print("   - View skill gaps")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    create_test_employees()

"""
HRMS Pre-Integration Database Migration
Creates new tables and adds fields for multi-project support, RBAC, and level movement workflow.
"""
import sqlite3
from datetime import datetime

def run_migration():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    print("Starting HRMS pre-integration migration...")
    
    try:
        # ============================================================================
        # 1. CREATE ROLES TABLE
        # ============================================================================
        print("Creating roles table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default roles
        print("Inserting default roles...")
        roles = [
            (1, 'System Admin', 'Full system access'),
            (2, 'HR', 'HR department access'),
            (3, 'Capability Partner', 'Capability group management'),
            (4, 'Delivery Manager', 'Project delivery management'),
            (5, 'Line Manager', 'Team management'),
            (6, 'Employee', 'Standard employee access')
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO roles (id, name, description) VALUES (?, ?, ?)
        ''', roles)
        
        # ============================================================================
        # 2. ADD ROLE_ID TO USERS TABLE
        # ============================================================================
        print("Adding role_id to users table...")
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN role_id INTEGER DEFAULT 6 REFERENCES roles(id)')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - role_id column already exists in users")
            else:
                raise
        
        # Update existing users to have Employee role
        cursor.execute('UPDATE users SET role_id = 6 WHERE role_id IS NULL')
        
        # Set admin users to System Admin role
        cursor.execute("UPDATE users SET role_id = 1 WHERE is_admin = 1 OR email = 'admin@skillboard.com'")
        
        # ============================================================================
        # 3. ADD FIELDS TO EMPLOYEES TABLE
        # ============================================================================
        print("Adding new fields to employees table...")
        new_employee_fields = [
            ('line_manager_id', 'INTEGER REFERENCES employees(id)'),
            ('grade', 'VARCHAR(50)'),
            ('capability', 'VARCHAR(100)'),
            ('capability_owner_id', 'INTEGER REFERENCES capability_owners(id)'),
            ('role_id', 'INTEGER DEFAULT 6 REFERENCES roles(id)')
        ]
        
        for field_name, field_type in new_employee_fields:
            try:
                cursor.execute(f'ALTER TABLE employees ADD COLUMN {field_name} {field_type}')
                print(f"  - Added {field_name}")
            except sqlite3.OperationalError as e:
                if 'duplicate column' in str(e).lower():
                    print(f"  - {field_name} already exists")
                else:
                    raise
        
        # Update existing employees to have Employee role
        cursor.execute('UPDATE employees SET role_id = 6 WHERE role_id IS NULL')
        
        # ============================================================================
        # 4. CREATE PROJECTS TABLE
        # ============================================================================
        print("Creating projects table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                capability_required VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================================
        # 5. CREATE CAPABILITY_OWNERS TABLE
        # ============================================================================
        print("Creating capability_owners table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capability_owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capability_name VARCHAR(100) UNIQUE NOT NULL,
                owner_employee_id INTEGER REFERENCES employees(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================================
        # 6. CREATE EMPLOYEE_PROJECT_ASSIGNMENTS TABLE
        # ============================================================================
        print("Creating employee_project_assignments table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_project_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                is_primary BOOLEAN DEFAULT 0 NOT NULL,
                percentage_allocation INTEGER CHECK (percentage_allocation >= 0 AND percentage_allocation <= 100),
                line_manager_id INTEGER REFERENCES employees(id),
                capability_owner_id INTEGER REFERENCES capability_owners(id),
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, project_id)
            )
        ''')
        
        # ============================================================================
        # 7. CREATE LEVEL_MOVEMENT_REQUESTS TABLE
        # ============================================================================
        print("Creating level_movement_requests table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_movement_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                current_level VARCHAR(50),
                requested_level VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                readiness_score REAL,
                submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                manager_approval_date TIMESTAMP,
                cp_approval_date TIMESTAMP,
                hr_approval_date TIMESTAMP,
                rejection_reason TEXT
            )
        ''')
        
        # ============================================================================
        # 8. CREATE LEVEL_MOVEMENT_APPROVAL_AUDIT TABLE
        # ============================================================================
        print("Creating level_movement_approval_audit table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_movement_approval_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL REFERENCES level_movement_requests(id) ON DELETE CASCADE,
                approver_id INTEGER REFERENCES employees(id),
                approver_role VARCHAR(50) NOT NULL,
                approval_status VARCHAR(50) NOT NULL,
                comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================================
        # 9. CREATE AUDIT_LOGS TABLE
        # ============================================================================
        print("Creating audit_logs table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                action VARCHAR(100) NOT NULL,
                target_id INTEGER,
                target_type VARCHAR(50),
                accessed_fields TEXT,
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ============================================================================
        # 10. CREATE ORG_STRUCTURE TABLE
        # ============================================================================
        print("Creating org_structure table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_structure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER UNIQUE NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                manager_id INTEGER REFERENCES employees(id),
                level INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nSummary:")
        print("  - Created roles table with 6 default roles")
        print("  - Added role_id to users and employees tables")
        print("  - Added line_manager_id, grade, capability, capability_owner_id to employees")
        print("  - Created projects table")
        print("  - Created capability_owners table")
        print("  - Created employee_project_assignments table")
        print("  - Created level_movement_requests table")
        print("  - Created level_movement_approval_audit table")
        print("  - Created audit_logs table")
        print("  - Created org_structure table")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()

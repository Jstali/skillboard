"""
Seed default roles for RBAC system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import text

def seed_roles():
    print("Seeding default roles...")
    
    roles = [
        (1, 'System Admin', 'Full system access'),
        (2, 'HR', 'HR department access'),
        (3, 'Capability Partner', 'Capability group management'),
        (4, 'Delivery Manager', 'Project delivery management'),
        (5, 'Line Manager', 'Team management'),
        (6, 'Employee', 'Standard employee access')
    ]
    
    with engine.begin() as conn:
        for role_id, name, description in roles:
            conn.execute(text("""
                INSERT INTO roles (id, name, description, created_at)
                VALUES (:id, :name, :description, NOW())
                ON CONFLICT (name) DO NOTHING
            """), {"id": role_id, "name": name, "description": description})
            print(f"  ✓ {name}")
        
        # Update existing users to have Employee role
        result = conn.execute(text("""
            UPDATE users SET role_id = 6 WHERE role_id IS NULL
        """))
        print(f"\n  ✓ Updated {result.rowcount} users to Employee role")
        
        # Set admin users to System Admin role
        result = conn.execute(text("""
            UPDATE users SET role_id = 1 
            WHERE is_admin = TRUE OR email = 'admin@skillboard.com'
        """))
        print(f"  ✓ Updated {result.rowcount} users to System Admin role")
        
        # Update existing employees to have Employee role
        result = conn.execute(text("""
            UPDATE employees SET role_id = 6 WHERE role_id IS NULL
        """))
        print(f"  ✓ Updated {result.rowcount} employees to Employee role")
    
    print("\n✅ Roles seeded successfully!")

if __name__ == "__main__":
    seed_roles()

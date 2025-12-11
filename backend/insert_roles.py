"""
Insert default roles into roles table
"""
import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"

def insert_roles():
    print("Inserting default roles...")
    
    roles = [
        (1, "System Admin", "Full system access"),
        (2, "HR", "HR management access"),
        (3, "Capability Partner", "Capability management access"),
        (4, "Delivery Manager", "Delivery management access"),
        (5, "Line Manager", "Team management access"),
        (6, "Employee", "Basic employee access"),
    ]
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        for role_id, name, description in roles:
            try:
                cur.execute("""
                    INSERT INTO roles (id, name, description, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (role_id, name, description, datetime.utcnow()))
                print(f"  ✅ {name} (ID: {role_id})")
            except Exception as e:
                print(f"  ⚠️  {name}: {e}")
        
        # Verify
        cur.execute("SELECT id, name FROM roles ORDER BY id")
        roles_in_db = cur.fetchall()
        print(f"\n✅ Total roles in database: {len(roles_in_db)}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Roles inserted successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    insert_roles()

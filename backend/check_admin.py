"""
Check if admin user exists and create if needed
"""
import sys
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/skillboard"
engine = create_engine(DATABASE_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_and_create_admin():
    with engine.connect() as conn:
        # Check if admin exists
        result = conn.execute(
            text("SELECT email, is_admin, is_active FROM users WHERE email = 'admin@skillboard.com'")
        )
        user = result.fetchone()
        
        if user:
            print(f"✅ Admin user found: {user[0]}")
            print(f"   Is admin: {user[1]}")
            print(f"   Is active: {user[2]}")
            
            # Test password
            result = conn.execute(
                text("SELECT password_hash FROM users WHERE email = 'admin@skillboard.com'")
            )
            password_hash = result.fetchone()[0]
            
            if pwd_context.verify("admin123", password_hash):
                print("   ✅ Password 'admin123' is CORRECT")
                print("\n📋 Login with:")
                print("   Email: admin@skillboard.com")
                print("   Password: admin123")
            else:
                print("   ❌ Password 'admin123' is INCORRECT")
                print("   Resetting password to 'admin123'...")
                
                new_hash = pwd_context.hash("admin123")
                conn.execute(
                    text("UPDATE users SET password_hash = :hash WHERE email = 'admin@skillboard.com'"),
                    {"hash": new_hash}
                )
                conn.commit()
                print("   ✅ Password reset complete!")
                print("\n📋 Login with:")
                print("   Email: admin@skillboard.com")
                print("   Password: admin123")
        else:
            print("❌ Admin user NOT FOUND")
            print("Creating admin user...")
            
            password_hash = pwd_context.hash("admin123")
            
            conn.execute(
                text("""
                    INSERT INTO users (email, password_hash, is_admin, is_active, must_change_password, created_at)
                    VALUES ('admin@skillboard.com', :hash, TRUE, TRUE, FALSE, NOW())
                """),
                {"hash": password_hash}
            )
            conn.commit()
            print("✅ Admin user created!")
            print("\n📋 Login with:")
            print("   Email: admin@skillboard.com")
            print("   Password: admin123")

if __name__ == "__main__":
    try:
        check_and_create_admin()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

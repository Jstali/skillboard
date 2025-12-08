"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment variable
# Defaults to localhost for local development. Docker Compose will override this via env var.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://skillboard:skillboard@localhost:5432/skillboard"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.db.models import Base

    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Try to add new columns if they don't exist (for existing databases)
    try:
        from sqlalchemy import text
        with engine.begin() as conn:  # Use begin() for auto-commit
            # Check and add first_name if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='first_name'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN first_name VARCHAR"))
            
            # Check and add last_name if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='last_name'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN last_name VARCHAR"))
            
            # Check and add company_email if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='company_email'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN company_email VARCHAR"))
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_employees_company_email ON employees(company_email)"))
                except Exception:
                    pass  # Index might already exist
            
            # Check and add department if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='department'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN department VARCHAR"))
            
            # Check and add role if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='role'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN role VARCHAR"))
            
            # Check and add team if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='team'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN team VARCHAR"))
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_employees_team ON employees(team)"))
                except Exception:
                    pass  # Index might already exist
            
            # Check and add band if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='band'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN band VARCHAR"))
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_employees_band ON employees(band)"))
                except Exception:
                    pass  # Index might already exist
            
            # Check and add category if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='category'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employees ADD COLUMN category VARCHAR"))
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_employees_category ON employees(category)"))
                except Exception:
                    pass  # Index might already exist
            
            # Migrate employee_skills table - add new columns
            # Check and add is_interested if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='is_interested'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employee_skills ADD COLUMN is_interested BOOLEAN DEFAULT FALSE NOT NULL"))
            
            # Check and add notes if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='notes'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employee_skills ADD COLUMN notes VARCHAR"))
            
            # Check and add match_score if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='match_score'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employee_skills ADD COLUMN match_score FLOAT"))
            
            # Check and add needs_review if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='needs_review'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employee_skills ADD COLUMN needs_review BOOLEAN DEFAULT FALSE NOT NULL"))
            
            # Make rating nullable for interested skills (if it's currently NOT NULL)
            result = conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='rating'
            """))
            rating_info = result.fetchone()
            if rating_info and rating_info[0] == 'NO':
                # Rating is currently NOT NULL, make it nullable
                conn.execute(text("ALTER TABLE employee_skills ALTER COLUMN rating DROP NOT NULL"))
            
            # Check and add initial_rating column if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employee_skills' AND column_name='initial_rating'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE employee_skills ADD COLUMN initial_rating VARCHAR(20)"))
                # Set initial_rating to current rating for existing records
                conn.execute(text("""
                    UPDATE employee_skills 
                    SET initial_rating = rating 
                    WHERE rating IS NOT NULL AND initial_rating IS NULL
                """))
            
            # Check and add category column to skills table if missing
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='skills' AND column_name='category'
            """))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE skills ADD COLUMN category VARCHAR(100)"))
            
            # Update ratingenum enum type to include new values (Developing and Expert)
            # Note: Since native_enum=False is used in models, this is stored as VARCHAR, not a PostgreSQL enum
            # However, if a PostgreSQL enum type exists (from previous migrations), we should update it
            try:
                # First check if the enum type exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type WHERE typname = 'ratingenum'
                    )
                """))
                enum_exists = result.fetchone()[0]
                
                if enum_exists:
                    # Check current enum values
                    result = conn.execute(text("""
                        SELECT enumlabel 
                        FROM pg_enum 
                        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'ratingenum')
                        ORDER BY enumsortorder
                    """))
                    enum_values = [row[0] for row in result.fetchall()]
                    
                    # Add 'Developing' if it doesn't exist
                    if 'Developing' not in enum_values:
                        try:
                            conn.execute(text("ALTER TYPE ratingenum ADD VALUE 'Developing'"))
                        except Exception as e:
                            # Value might already exist
                            import logging
                            logging.warning(f"Could not add Developing to ratingenum (may already exist): {e}")
                    
                    # Add 'Expert' if it doesn't exist
                    if 'Expert' not in enum_values:
                        try:
                            conn.execute(text("ALTER TYPE ratingenum ADD VALUE 'Expert'"))
                        except Exception as e:
                            # Value might already exist
                            import logging
                            logging.warning(f"Could not add Expert to ratingenum (may already exist): {e}")
            except Exception as e:
                # Enum type might not exist (which is fine with native_enum=False)
                # Or there's another issue - log but don't fail
                import logging
                logging.warning(f"Could not check/update ratingenum (may not exist, which is fine): {e}")
            
            # Check if users table exists, if not it will be created by Base.metadata.create_all above
            # But we can verify and add any missing columns
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='users'
            """))
            if result.fetchone():
                # Users table exists, check for must_change_password column
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='must_change_password'
                """))
                if not result.fetchone():
                    conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE NOT NULL"))
    except Exception as e:
        # If migration fails, log but don't crash - tables might already be correct
        import logging
        logging.warning(f"Could not migrate database tables: {e}")


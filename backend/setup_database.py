#!/usr/bin/env python3
"""
Complete database setup script for Skillboard.
This script will:
1. Create all base tables from SQLAlchemy models
2. Apply all SQL migrations
3. Set up indexes and constraints
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from app.db.models import Base
from sqlalchemy import text

def create_base_tables():
    """Create all base tables from SQLAlchemy models."""
    print("=" * 60)
    print("STEP 1: Creating base tables from models...")
    print("=" * 60)
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Base tables created successfully!")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"\nCreated tables: {', '.join(tables)}")
            
    except Exception as e:
        print(f"✗ Error creating base tables: {e}")
        raise

def apply_sql_migration(filename, description):
    """Apply a SQL migration file."""
    print(f"\n→ Applying: {description}")
    
    filepath = os.path.join(os.path.dirname(__file__), 'migrations', filename)
    
    if not os.path.exists(filepath):
        print(f"  ⚠ Warning: Migration file not found: {filename}")
        return
    
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
        
        with engine.begin() as conn:
            # Execute the SQL (PostgreSQL can handle multiple statements)
            conn.execute(text(sql))
            
        print(f"  ✓ {description} applied successfully!")
        
    except Exception as e:
        print(f"  ⚠ Warning: {description} - {e}")
        # Don't fail the entire migration if one step fails (might already exist)

def apply_migrations():
    """Apply all SQL migrations in order."""
    print("\n" + "=" * 60)
    print("STEP 2: Applying SQL migrations...")
    print("=" * 60)
    
    migrations = [
        ('add_is_custom_column.sql', 'Add is_custom column to employee_skills'),
        ('create_role_requirements.sql', 'Create role requirements table'),
        ('add_learning_tables.sql', 'Create learning platform tables'),
    ]
    
    for filename, description in migrations:
        apply_sql_migration(filename, description)

def verify_database():
    """Verify database setup."""
    print("\n" + "=" * 60)
    print("STEP 3: Verifying database setup...")
    print("=" * 60)
    
    try:
        with engine.connect() as conn:
            # Count tables
            result = conn.execute(text("""
                SELECT COUNT(*) FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            table_count = result.scalar()
            
            # List all tables
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n✓ Total tables: {table_count}")
            print("\nAll tables:")
            for table in tables:
                # Count rows
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  • {table} ({count} rows)")
                except Exception:
                    print(f"  • {table}")
            
    except Exception as e:
        print(f"✗ Error verifying database: {e}")
        raise

def main():
    """Run all migration steps."""
    print("\n" + "=" * 60)
    print("SKILLBOARD DATABASE SETUP")
    print("=" * 60)
    
    try:
        # Step 1: Create base tables
        create_base_tables()
        
        # Step 2: Apply migrations
        apply_migrations()
        
        # Step 3: Verify setup
        verify_database()
        
        print("\n" + "=" * 60)
        print("✓ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start the backend: ./run_local.sh")
        print("  2. Create an admin user: python -m app.scripts.create_admin")
        print("  3. Access the API at: http://localhost:8000/docs")
        print()
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ DATABASE SETUP FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


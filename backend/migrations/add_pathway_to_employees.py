"""Migration script to add pathway and lock columns to employees table.

Adds:
- pathway: Career pathway (Technical, SAP, Cloud, Data, etc.)
- band_locked_at: Timestamp when band was locked (for audit)
- pathway_locked_at: Timestamp when pathway was locked (for audit)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

MIGRATION_SQL = """
-- Add pathway column to employees table
ALTER TABLE employees ADD COLUMN IF NOT EXISTS pathway VARCHAR(100);

-- Add lock timestamp columns for audit trail
ALTER TABLE employees ADD COLUMN IF NOT EXISTS band_locked_at TIMESTAMP;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS pathway_locked_at TIMESTAMP;

-- Create index on pathway for efficient queries
CREATE INDEX IF NOT EXISTS idx_employees_pathway ON employees(pathway);

-- Add comments
COMMENT ON COLUMN employees.pathway IS 'Career pathway: Technical, SAP, Cloud, Data, etc. Can only be changed via Level Movement workflow.';
COMMENT ON COLUMN employees.band_locked_at IS 'Timestamp when band was last set/changed via Level Movement';
COMMENT ON COLUMN employees.pathway_locked_at IS 'Timestamp when pathway was last set/changed via Level Movement';
"""


def run_migration():
    """Execute the migration."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_engine(database_url)
    
    print("Adding pathway and lock columns to employees table...")
    
    with engine.connect() as conn:
        conn.execute(text(MIGRATION_SQL))
        conn.commit()
    
    print("✅ Pathway columns added to employees table successfully!")


if __name__ == "__main__":
    run_migration()

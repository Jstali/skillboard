"""Migration script to create skill_assessments table for manager-driven skill assessment model.

This table replaces employee self-service skill ratings with manager-assessed skills.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

MIGRATION_SQL = """
-- Create skill_assessments table
CREATE TABLE IF NOT EXISTS skill_assessments (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    level VARCHAR(50) NOT NULL,  -- Beginner, Developing, Intermediate, Advanced, Expert
    assessment_type VARCHAR(20) NOT NULL,  -- 'baseline', 'manager', 'legacy'
    assessor_id INTEGER REFERENCES employees(id),  -- NULL for SYSTEM baseline
    assessor_role VARCHAR(50) NOT NULL,  -- 'SYSTEM', 'LINE_MANAGER', 'DELIVERY_MANAGER', 'LEGACY_SELF_REPORTED'
    comments TEXT,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_skill_assessment_employee_skill UNIQUE(employee_id, skill_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_skill_assessments_employee ON skill_assessments(employee_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_skill ON skill_assessments(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_assessor ON skill_assessments(assessor_id);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_type ON skill_assessments(assessment_type);
CREATE INDEX IF NOT EXISTS idx_skill_assessments_assessed_at ON skill_assessments(assessed_at DESC);

-- Add comment for documentation
COMMENT ON TABLE skill_assessments IS 'Manager-assessed skill levels for employees. Replaces self-service skill ratings.';
COMMENT ON COLUMN skill_assessments.assessment_type IS 'Type of assessment: baseline (system-generated), manager (LM/DM assessed), legacy (migrated from old system)';
COMMENT ON COLUMN skill_assessments.assessor_role IS 'Role of assessor: SYSTEM, LINE_MANAGER, DELIVERY_MANAGER, or LEGACY_SELF_REPORTED';
"""


def run_migration():
    """Execute the migration."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_engine(database_url)
    
    print("Creating skill_assessments table...")
    
    with engine.connect() as conn:
        # Execute migration
        conn.execute(text(MIGRATION_SQL))
        conn.commit()
    
    print("✅ skill_assessments table created successfully!")


if __name__ == "__main__":
    run_migration()

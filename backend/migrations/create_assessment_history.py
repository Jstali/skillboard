"""Migration script to create assessment_history table for immutable audit trail.

This table stores all assessment changes for GDPR compliance and audit purposes.
Records in this table are immutable - no updates or deletes allowed.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

MIGRATION_SQL = """
-- Create assessment_history table (immutable audit trail)
CREATE TABLE IF NOT EXISTS assessment_history (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    previous_level VARCHAR(50),  -- NULL for first assessment
    new_level VARCHAR(50) NOT NULL,
    assessment_type VARCHAR(20) NOT NULL,  -- 'baseline', 'manager', 'legacy'
    assessor_id INTEGER REFERENCES employees(id),  -- NULL for SYSTEM
    assessor_role VARCHAR(50) NOT NULL,  -- 'SYSTEM', 'LINE_MANAGER', 'DELIVERY_MANAGER', 'LEGACY_SELF_REPORTED'
    comments TEXT,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_assessment_history_employee ON assessment_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_assessment_history_skill ON assessment_history(skill_id);
CREATE INDEX IF NOT EXISTS idx_assessment_history_employee_skill ON assessment_history(employee_id, skill_id);
CREATE INDEX IF NOT EXISTS idx_assessment_history_assessed_at ON assessment_history(assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessment_history_assessor ON assessment_history(assessor_id);

-- Add comments for documentation
COMMENT ON TABLE assessment_history IS 'Immutable audit trail of all skill assessment changes. No updates or deletes allowed.';
COMMENT ON COLUMN assessment_history.previous_level IS 'Previous skill level before this assessment. NULL for first assessment.';
COMMENT ON COLUMN assessment_history.new_level IS 'New skill level after this assessment.';

-- Create a rule to prevent updates (application-level enforcement)
-- Note: This is enforced at application level, but we add a trigger for extra safety
CREATE OR REPLACE FUNCTION prevent_assessment_history_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Assessment history records are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS prevent_assessment_history_update ON assessment_history;
DROP TRIGGER IF EXISTS prevent_assessment_history_delete ON assessment_history;

-- Create triggers to prevent modification
CREATE TRIGGER prevent_assessment_history_update
    BEFORE UPDATE ON assessment_history
    FOR EACH ROW
    EXECUTE FUNCTION prevent_assessment_history_modification();

CREATE TRIGGER prevent_assessment_history_delete
    BEFORE DELETE ON assessment_history
    FOR EACH ROW
    EXECUTE FUNCTION prevent_assessment_history_modification();
"""


def run_migration():
    """Execute the migration."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_engine(database_url)
    
    print("Creating assessment_history table with immutability triggers...")
    
    with engine.connect() as conn:
        conn.execute(text(MIGRATION_SQL))
        conn.commit()
    
    print("✅ assessment_history table created successfully!")


if __name__ == "__main__":
    run_migration()

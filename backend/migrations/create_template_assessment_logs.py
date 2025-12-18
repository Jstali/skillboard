"""Migration script to create template_assessment_logs table for audit trail.

This table stores audit records when managers assess employees using skill templates.
Records template_id, assessor_id, and timestamp for audit purposes.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

MIGRATION_SQL = """
-- Create template_assessment_logs table (audit trail for template assessments)
CREATE TABLE IF NOT EXISTS template_assessment_logs (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES skill_templates(id),
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    assessor_id INTEGER NOT NULL REFERENCES employees(id),
    skills_assessed INTEGER NOT NULL,
    total_skills INTEGER NOT NULL,
    assessed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_template_assessment_logs_template ON template_assessment_logs(template_id);
CREATE INDEX IF NOT EXISTS idx_template_assessment_logs_employee ON template_assessment_logs(employee_id);
CREATE INDEX IF NOT EXISTS idx_template_assessment_logs_assessor ON template_assessment_logs(assessor_id);

-- Add comments for documentation
COMMENT ON TABLE template_assessment_logs IS 'Audit trail for template-based skill assessments by managers.';
COMMENT ON COLUMN template_assessment_logs.template_id IS 'Reference to the skill template used for assessment.';
COMMENT ON COLUMN template_assessment_logs.employee_id IS 'Employee being assessed.';
COMMENT ON COLUMN template_assessment_logs.assessor_id IS 'Manager who performed the assessment.';
COMMENT ON COLUMN template_assessment_logs.skills_assessed IS 'Number of skills assessed in this submission.';
COMMENT ON COLUMN template_assessment_logs.total_skills IS 'Total number of skills in the template.';
COMMENT ON COLUMN template_assessment_logs.assessed_at IS 'Timestamp when the assessment was submitted.';
"""


def run_migration():
    """Execute the migration."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_engine(database_url)
    
    print("Creating template_assessment_logs table...")
    
    with engine.connect() as conn:
        conn.execute(text(MIGRATION_SQL))
        conn.commit()
    
    print("✅ template_assessment_logs table created successfully!")


if __name__ == "__main__":
    run_migration()

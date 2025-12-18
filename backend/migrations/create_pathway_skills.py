"""Migration script to create pathway_skills table.

This table defines which skills belong to each career pathway (Technical, SAP, Cloud, Data, etc.)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

MIGRATION_SQL = """
-- Create pathway_skills table
CREATE TABLE IF NOT EXISTS pathway_skills (
    id SERIAL PRIMARY KEY,
    pathway VARCHAR(100) NOT NULL,  -- Technical, SAP, Cloud, Data, etc.
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    is_core BOOLEAN DEFAULT TRUE NOT NULL,  -- Core vs optional skill for the pathway
    display_order INTEGER,  -- Order for UI display
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_pathway_skill UNIQUE(pathway, skill_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pathway_skills_pathway ON pathway_skills(pathway);
CREATE INDEX IF NOT EXISTS idx_pathway_skills_skill ON pathway_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_pathway_skills_is_core ON pathway_skills(is_core);

-- Add comments
COMMENT ON TABLE pathway_skills IS 'Defines which skills belong to each career pathway';
COMMENT ON COLUMN pathway_skills.pathway IS 'Career pathway name: Technical, SAP, Cloud, Data, etc.';
COMMENT ON COLUMN pathway_skills.is_core IS 'Whether this is a core skill for the pathway (vs optional)';
"""


def run_migration():
    """Execute the migration."""
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    engine = create_engine(database_url)
    
    print("Creating pathway_skills table...")
    
    with engine.connect() as conn:
        conn.execute(text(MIGRATION_SQL))
        conn.commit()
    
    print("✅ pathway_skills table created successfully!")


if __name__ == "__main__":
    run_migration()

"""Add template assignment workflow tables

Revision ID: add_template_workflow
Revises: 
Create Date: 2025-12-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_template_workflow'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add category_hr column to template_assignments
    op.add_column('template_assignments', sa.Column('category_hr', sa.String(), nullable=True))
    
    # Create employee_template_responses table
    op.create_table(
        'employee_template_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('employee_category', sa.String(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('employee_level', sa.String(), nullable=True),
        sa.Column('years_experience', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['template_assignments.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'skill_id', name='uq_assignment_skill_response')
    )
    op.create_index(op.f('ix_employee_template_responses_id'), 'employee_template_responses', ['id'], unique=False)
    
    # Create skill_gap_results table
    op.create_table(
        'skill_gap_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('required_level', sa.String(), nullable=False),
        sa.Column('employee_level', sa.String(), nullable=True),
        sa.Column('gap_status', sa.String(), nullable=False),
        sa.Column('gap_value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['template_assignments.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'skill_id', name='uq_assignment_skill_gap')
    )
    op.create_index(op.f('ix_skill_gap_results_id'), 'skill_gap_results', ['id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_skill_gap_results_id'), table_name='skill_gap_results')
    op.drop_table('skill_gap_results')
    op.drop_index(op.f('ix_employee_template_responses_id'), table_name='employee_template_responses')
    op.drop_table('employee_template_responses')
    
    # Remove category_hr column
    op.drop_column('template_assignments', 'category_hr')

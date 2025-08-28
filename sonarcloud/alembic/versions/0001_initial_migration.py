"""Initial migration for SonarCloud metrics database

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sonarcloud_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sonarcloud_id', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.String(length=50), nullable=True),
        sa.Column('last_analysis_date', sa.DateTime(), nullable=True),
        sa.Column('coverage', sa.Float(), nullable=False),
        sa.Column('duplications', sa.Float(), nullable=False),
        sa.Column('maintainability_rating', sa.Integer(), nullable=False),
        sa.Column('reliability_rating', sa.Integer(), nullable=False),
        sa.Column('security_rating', sa.Integer(), nullable=False),
        sa.Column('security_review_rating', sa.Integer(), nullable=False),
        sa.Column('bugs_count', sa.Integer(), nullable=False),
        sa.Column('vulnerabilities_count', sa.Integer(), nullable=False),
        sa.Column('code_smells_count', sa.Integer(), nullable=False),
        sa.Column('new_issues_count', sa.Integer(), nullable=False),
        sa.Column('security_hotspots_count', sa.Integer(), nullable=False),
        sa.Column('lines_of_code', sa.Integer(), nullable=False),
        sa.Column('ncloc', sa.Integer(), nullable=False),
        sa.Column('alert_status', sa.String(length=50), nullable=True),
        sa.Column('quality_gate_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create quality_gates table
    op.create_table('quality_gates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create metrics table
    op.create_table('metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('string_value', sa.String(length=1000), nullable=True),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('direction', sa.String(length=20), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create issues table
    op.create_table('issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=255), nullable=False),
        sa.Column('rule', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('resolution', sa.String(length=50), nullable=True),
        sa.Column('component', sa.String(length=500), nullable=True),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at_db', sa.DateTime(), nullable=False),
        sa.Column('updated_at_db', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create security_hotspots table
    op.create_table('security_hotspots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=255), nullable=False),
        sa.Column('rule_key', sa.String(length=255), nullable=False),
        sa.Column('vulnerability_probability', sa.String(length=50), nullable=False),
        sa.Column('security_category', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('resolution', sa.String(length=50), nullable=True),
        sa.Column('component', sa.String(length=500), nullable=True),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at_db', sa.DateTime(), nullable=False),
        sa.Column('updated_at_db', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_organizations_key'), 'organizations', ['key'], unique=False)
    op.create_index(op.f('ix_organizations_sonarcloud_id'), 'organizations', ['sonarcloud_id'], unique=False)
    op.create_index(op.f('ix_projects_key'), 'projects', ['key'], unique=False)
    op.create_index(op.f('ix_projects_sonarcloud_id'), 'projects', ['sonarcloud_id'], unique=False)
    op.create_index(op.f('ix_projects_organization_id'), 'projects', ['organization_id'], unique=False)
    op.create_index(op.f('ix_projects_last_analysis_date'), 'projects', ['last_analysis_date'], unique=False)
    op.create_index(op.f('ix_projects_coverage'), 'projects', ['coverage'], unique=False)
    op.create_index(op.f('ix_projects_quality_gate_status'), 'projects', ['quality_gate_status'], unique=False)
    op.create_index(op.f('ix_quality_gates_project_id'), 'quality_gates', ['project_id'], unique=False)
    op.create_index(op.f('ix_quality_gates_status'), 'quality_gates', ['status'], unique=False)
    op.create_index(op.f('ix_metrics_project_id'), 'metrics', ['project_id'], unique=False)
    op.create_index(op.f('ix_metrics_key'), 'metrics', ['key'], unique=False)
    op.create_index(op.f('ix_issues_project_id'), 'issues', ['project_id'], unique=False)
    op.create_index(op.f('ix_issues_severity'), 'issues', ['severity'], unique=False)
    op.create_index(op.f('ix_issues_status'), 'issues', ['status'], unique=False)
    op.create_index(op.f('ix_issues_type'), 'issues', ['type'], unique=False)
    op.create_index(op.f('ix_security_hotspots_project_id'), 'security_hotspots', ['project_id'], unique=False)
    op.create_index(op.f('ix_security_hotspots_vulnerability_probability'), 'security_hotspots', ['vulnerability_probability'], unique=False)
    op.create_index(op.f('ix_security_hotspots_status'), 'security_hotspots', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_security_hotspots_status'), table_name='security_hotspots')
    op.drop_index(op.f('ix_security_hotspots_vulnerability_probability'), table_name='security_hotspots')
    op.drop_index(op.f('ix_security_hotspots_project_id'), table_name='security_hotspots')
    op.drop_index(op.f('ix_issues_type'), table_name='issues')
    op.drop_index(op.f('ix_issues_status'), table_name='issues')
    op.drop_index(op.f('ix_issues_severity'), table_name='issues')
    op.drop_index(op.f('ix_issues_project_id'), table_name='issues')
    op.drop_index(op.f('ix_metrics_key'), table_name='metrics')
    op.drop_index(op.f('ix_metrics_project_id'), table_name='metrics')
    op.drop_index(op.f('ix_quality_gates_status'), table_name='quality_gates')
    op.drop_index(op.f('ix_quality_gates_project_id'), table_name='quality_gates')
    op.drop_index(op.f('ix_projects_quality_gate_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_coverage'), table_name='projects')
    op.drop_index(op.f('ix_projects_last_analysis_date'), table_name='projects')
    op.drop_index(op.f('ix_projects_organization_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_sonarcloud_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_key'), table_name='projects')
    op.drop_index(op.f('ix_organizations_sonarcloud_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_key'), table_name='organizations')
    
    # Drop tables
    op.drop_table('security_hotspots')
    op.drop_table('issues')
    op.drop_table('metrics')
    op.drop_table('quality_gates')
    op.drop_table('projects')
    op.drop_table('organizations')

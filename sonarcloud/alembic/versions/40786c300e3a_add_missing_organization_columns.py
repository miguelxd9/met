"""add_missing_organization_columns

Revision ID: 40786c300e3a
Revises: 0001
Create Date: 2025-08-28 15:20:32.686876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40786c300e3a'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to organizations table
    op.add_column('organizations', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('organizations', sa.Column('url', sa.String(length=500), nullable=True))
    op.add_column('organizations', sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('organizations', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('organizations', sa.Column('total_projects', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('organizations', sa.Column('total_quality_gates', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('organizations', sa.Column('total_issues', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('organizations', sa.Column('total_security_hotspots', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove added columns from organizations table
    op.drop_column('organizations', 'total_security_hotspots')
    op.drop_column('organizations', 'total_issues')
    op.drop_column('organizations', 'total_quality_gates')
    op.drop_column('organizations', 'total_projects')
    op.drop_column('organizations', 'is_default')
    op.drop_column('organizations', 'is_private')
    op.drop_column('organizations', 'url')
    op.drop_column('organizations', 'avatar_url')
    op.drop_column('organizations', 'description')

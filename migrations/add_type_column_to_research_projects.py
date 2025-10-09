"""
Add type column to research_projects table

This migration adds the missing 'type' column to the research_projects table.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_10_09_add_type_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add type column to research_projects table
    op.add_column('research_projects', sa.Column('type', sa.String(length=50), nullable=True))
    
    # Update existing rows to have a default value
    op.execute("UPDATE research_projects SET type = 'general' WHERE type IS NULL")
    
    # Make the column not nullable after setting default values
    op.alter_column('research_projects', 'type', nullable=False)


def downgrade():
    # Remove type column from research_projects table
    op.drop_column('research_projects', 'type')

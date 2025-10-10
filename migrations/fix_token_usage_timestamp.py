"""
Fix token_usage timestamp column issue

This migration adds the missing 'timestamp' column to the token_usage table
or modifies the code to use the existing 'date' column instead.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '2023_10_09_fix_token_usage_timestamp'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Add timestamp column to token_usage table if it doesn't exist.
    """
    # Check if timestamp column exists
    connection = op.get_bind()
    result = connection.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'token_usage' AND column_name = 'timestamp'
        )
    """)
    column_exists = result.scalar()
    
    if not column_exists:
        print("Adding 'timestamp' column to token_usage table...")
        op.add_column('token_usage', sa.Column('timestamp', sa.DateTime, nullable=True))
        
        # Update existing rows to have timestamp = date
        op.execute("UPDATE token_usage SET timestamp = date WHERE timestamp IS NULL")
        
        print("Successfully added 'timestamp' column to token_usage table")
    else:
        print("'timestamp' column already exists in token_usage table")


def downgrade():
    """
    Remove timestamp column from token_usage table if it exists.
    """
    # Check if timestamp column exists
    connection = op.get_bind()
    result = connection.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'token_usage' AND column_name = 'timestamp'
        )
    """)
    column_exists = result.scalar()
    
    if column_exists:
        print("Removing 'timestamp' column from token_usage table...")
        op.drop_column('token_usage', 'timestamp')
        print("Successfully removed 'timestamp' column from token_usage table")
    else:
        print("'timestamp' column does not exist in token_usage table")

"""
Fix token_usage tokens_used null constraint issue

This migration addresses the NOT NULL constraint violation in the token_usage table
by making the tokens_used column nullable or setting a default value.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '2023_10_09_fix_token_usage_null_constraint'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Make the tokens_used column nullable or set a default value.
    """
    # Check if tokens_used column exists and is NOT NULL
    connection = op.get_bind()
    result = connection.execute("""
        SELECT is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'token_usage' AND column_name = 'tokens_used'
    """)
    row = result.fetchone()
    
    if row and row[0] == 'NO':  # Column exists and is NOT NULL
        print("Making tokens_used column nullable...")
        op.execute("ALTER TABLE token_usage ALTER COLUMN tokens_used DROP NOT NULL")
        print("Successfully made tokens_used column nullable")
    else:
        print("tokens_used column is already nullable or doesn't exist")


def downgrade():
    """
    Revert changes by making tokens_used NOT NULL again.
    """
    # Check if tokens_used column exists and is nullable
    connection = op.get_bind()
    result = connection.execute("""
        SELECT is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'token_usage' AND column_name = 'tokens_used'
    """)
    row = result.fetchone()
    
    if row and row[0] == 'YES':  # Column exists and is nullable
        print("Making tokens_used column NOT NULL again...")
        op.execute("ALTER TABLE token_usage ALTER COLUMN tokens_used SET NOT NULL")
        print("Successfully made tokens_used column NOT NULL")
    else:
        print("tokens_used column is already NOT NULL or doesn't exist")

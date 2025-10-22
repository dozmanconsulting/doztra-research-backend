"""
Set default for user_usage.updated_at and auto-update on row updates.

 - Adds DEFAULT now() to updated_at
 - Backfills NULL updated_at values
 - Adds trigger to set updated_at = now() on UPDATE

This prevents NOT NULL violations on inserts and keeps the timestamp fresh.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025_10_22_user_usage_updated_at_default"
# Align to your base migration; if different, adjust accordingly
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Ensure column exists
    res = conn.execute(sa.text(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_usage' AND column_name = 'updated_at'
        """
    )).fetchone()
    if not res:
        op.add_column('user_usage', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # Set default now() and not-null
    op.execute("ALTER TABLE user_usage ALTER COLUMN updated_at SET DEFAULT NOW();")

    # Backfill existing nulls
    op.execute("UPDATE user_usage SET updated_at = NOW() WHERE updated_at IS NULL;")

    # Enforce NOT NULL
    op.execute("ALTER TABLE user_usage ALTER COLUMN updated_at SET NOT NULL;")

    # Create or replace trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION trigger_set_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = NOW();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Drop and recreate trigger to avoid duplicates
    op.execute("DROP TRIGGER IF EXISTS set_timestamp ON user_usage;")
    op.execute(
        """
        CREATE TRIGGER set_timestamp
        BEFORE UPDATE ON user_usage
        FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
        """
    )


def downgrade():
    # Best-effort downgrade: drop trigger, remove default; keep column NOT NULL
    op.execute("DROP TRIGGER IF EXISTS set_timestamp ON user_usage;")
    op.execute("DROP FUNCTION IF EXISTS trigger_set_timestamp();")
    op.execute("ALTER TABLE user_usage ALTER COLUMN updated_at DROP DEFAULT;")

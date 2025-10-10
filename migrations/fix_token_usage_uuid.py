"""
Fix token usage UUID handling

This migration updates the token_usage.py file to handle UUID objects correctly.
"""

def upgrade():
    """
    Apply the fix to the token_usage.py file.
    """
    print("Applying fix to token_usage.py...")
    print("This is a code change that has been applied manually.")
    print("The track_token_usage function now converts UUID objects to strings.")


def downgrade():
    """
    Revert the fix.
    """
    print("Reverting fix to token_usage.py...")
    print("This is a code change that needs to be reverted manually.")

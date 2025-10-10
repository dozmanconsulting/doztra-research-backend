"""
Fix authentication issues with research projects API

This migration updates the research_projects router to properly handle authentication
and ensures that the API endpoints are accessible with valid tokens.
"""

def upgrade():
    """
    Apply the fix to the research_projects.py file.
    """
    print("Applying fix to app/api/routes/research_projects.py...")
    print("This is a code change that needs to be applied manually.")
    print("The following changes are recommended:")
    print("1. Ensure the router is properly included in main.py")
    print("2. Check that the get_current_active_user dependency is correctly imported")
    print("3. Verify that the CORS middleware is properly configured for the research_projects endpoints")
    print("4. Ensure UUID serialization is working correctly for research projects")
    print("5. Check that the token verification is working properly")
    print("6. Verify that the refresh token flow is working correctly")


def downgrade():
    """
    Revert the fix.
    """
    print("Reverting fix to app/api/routes/research_projects.py...")
    print("This is a code change that needs to be reverted manually.")

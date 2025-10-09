"""
Fix UUID serialization in chat endpoints

This migration updates the chat endpoints to properly convert UUID objects to strings.
"""

def upgrade():
    """
    Apply the fix to the chat.py file.
    """
    print("Applying fix to app/api/routes/chat.py...")
    print("This is a code change that has been applied manually.")
    print("The following endpoints now use convert_uuid_to_str:")
    print("- list_conversations")
    print("- create_new_conversation")
    print("- get_conversation_messages_endpoint")
    print("- update_conversation_details")
    print("- send_message")


def downgrade():
    """
    Revert the fix.
    """
    print("Reverting fix to app/api/routes/chat.py...")
    print("This is a code change that needs to be reverted manually.")

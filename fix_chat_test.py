#!/usr/bin/env python3
"""
Fix for the chat test endpoints.

This script updates the test_chat_simple.py file to use the correct API endpoints.
"""

import os
import sys

def fix_chat_test():
    """
    Update the test_chat_simple.py file to use the correct API endpoints.
    """
    test_file_path = os.path.join('tests', 'test_chat_simple.py')
    
    # Read the test file
    with open(test_file_path, 'r') as f:
        content = f.read()
    
    # Update the endpoints
    # 1. Change /api/chat/conversations to /api/conversations
    content = content.replace('/api/chat/conversations', '/api/conversations')
    
    # 2. Change /api/chat/message to /api/messages
    content = content.replace('/api/chat/message', '/api/messages')
    
    # Write the updated content back to the file
    with open(test_file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {test_file_path} with correct API endpoints.")

if __name__ == "__main__":
    fix_chat_test()

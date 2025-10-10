#!/usr/bin/env python3
"""
Run test_chat_simple.py with exception handling
"""
import traceback

try:
    from tests.test_chat_simple import setup_module, test_create_conversation, test_send_message, teardown_module
    
    print("Setting up test module...")
    setup_module()
    
    print("Running test_create_conversation...")
    test_create_conversation()
    
    print("Running test_send_message...")
    test_send_message()
    
    print("All tests passed!")
except Exception as e:
    print(f"Error: {str(e)}")
    print(traceback.format_exc())
finally:
    try:
        print("Tearing down test module...")
        teardown_module()
    except Exception as e:
        print(f"Error during teardown: {str(e)}")

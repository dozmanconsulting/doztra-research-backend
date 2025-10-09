#!/usr/bin/env python3
"""
Script to test the chat endpoint directly
"""
import requests
import json
import sys

def test_chat_endpoint(token, message="Tell me about AI", model="gpt-3.5-turbo"):
    """Test the chat endpoint with a token"""
    url = "http://localhost:8001/api/chat/message"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "message": message,
        "model": model
    }
    
    print(f"Sending request to {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("\nServer error details:")
            try:
                error_details = response.json()
                print(json.dumps(error_details, indent=2))
            except:
                print("Could not parse error details as JSON")
        
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    # Use the token from the command line or use the default token
    token = sys.argv[1] if len(sys.argv) > 1 else "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NzVhNGI5NS01NzRhLTRkNWMtYTY3NC03NmQ0MWNiMTNlOWEiLCJleHAiOjE3NjAzNjYwNTl9.AJ02KCdCON2c0Q7mkZuX6m8k5o0EMkoT_xDRQCeRymQ"
    test_chat_endpoint(token)

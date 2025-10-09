#!/usr/bin/env python3
"""
Script to test the OpenAI API directly
"""
import httpx
import asyncio
from app.core.config import settings

async def test_openai_api():
    """Test the OpenAI API directly"""
    url = f"{settings.OPENAI_API_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about AI"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY[:10]}..., Length: {len(settings.OPENAI_API_KEY)}")
    print(f"OpenAI API URL: {settings.OPENAI_API_URL}")
    print(f"Sending request to {url}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data['choices'][0]['message']['content']}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_api())

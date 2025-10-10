"""
Check if the OpenAI API key is set in the environment.
"""

import os
from app.core.config import settings

print(f"OPENAI_API_KEY is {'set' if settings.OPENAI_API_KEY else 'not set'}")
if settings.OPENAI_API_KEY:
    print(f"API key length: {len(settings.OPENAI_API_KEY)}")
    print(f"API key starts with: {settings.OPENAI_API_KEY[:5]}...")
else:
    print("API key is empty")

print(f"OPENAI_API_URL: {settings.OPENAI_API_URL}")

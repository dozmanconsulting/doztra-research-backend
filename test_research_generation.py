"""
Test script for research generation endpoints
Run this after starting the server to verify all endpoints work correctly
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api"
# TODO: Replace with actual JWT token after authentication
AUTH_TOKEN = "YOUR_JWT_TOKEN_HERE"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}


def test_improve_topic():
    """Test the improve-topic endpoint"""
    print("\n" + "="*50)
    print("Testing: POST /api/improve-topic")
    print("="*50)
    
    payload = {
        "originalInput": "Digital marketing in Africa",
        "type": "Dissertation",
        "citation": "APA 7",
        "length": "10-20 pages",
        "discipline": "Business Administration",
        "faculty": "Marketing",
        "country": "Nigeria",
        "uploadedDocuments": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/improve-topic",
            headers=headers,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED")
            return response.json()
        else:
            print("❌ Test FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_alternative_topic(previous_topic=None):
    """Test the alternative-topic endpoint"""
    print("\n" + "="*50)
    print("Testing: POST /api/alternative-topic")
    print("="*50)
    
    payload = {
        "originalInput": "Digital marketing in Africa",
        "previousTopic": previous_topic,
        "type": "Dissertation",
        "discipline": "Business Administration",
        "faculty": "Marketing",
        "country": "Nigeria",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/alternative-topic",
            headers=headers,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED")
            return response.json()
        else:
            print("❌ Test FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_generate_outline():
    """Test the generate-outline endpoint"""
    print("\n" + "="*50)
    print("Testing: POST /api/generate-outline")
    print("="*50)
    
    payload = {
        "topic": "Digital Marketing Strategy for African Markets",
        "type": "Dissertation",
        "citation": "APA 7",
        "length": "10-20 pages",
        "discipline": "Business Administration",
        "faculty": "Marketing",
        "country": "Nigeria",
        "researchGuidelines": "Focus on Nigerian market with case studies",
        "uploadedDocuments": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-outline",
            headers=headers,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED")
            return response.json()
        else:
            print("❌ Test FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_upload_documents():
    """Test the upload-documents endpoint"""
    print("\n" + "="*50)
    print("Testing: POST /api/upload-documents")
    print("="*50)
    
    # Create a test text file
    test_content = "This is a test document for research guidelines."
    
    files = {
        'files': ('test_document.txt', test_content, 'text/plain')
    }
    
    data = {
        'metadata': json.dumps({
            "discipline": "Business Administration",
            "country": "Nigeria"
        })
    }
    
    upload_headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload-documents",
            headers=upload_headers,
            files=files,
            data=data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED")
            return response.json()
        else:
            print("❌ Test FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_generate_draft():
    """Test the generate-draft endpoint"""
    print("\n" + "="*50)
    print("Testing: POST /api/generate-draft")
    print("="*50)
    
    payload = {
        "topic": "Digital Marketing Strategy for African Markets",
        "outline": [
            "Title Page",
            "Abstract",
            "Chapter 1: Introduction",
            "  1.1 Background",
            "Chapter 2: Literature Review"
        ],
        "type": "Dissertation",
        "citation": "APA 7",
        "length": "10-20 pages",
        "discipline": "Business Administration",
        "faculty": "Marketing",
        "country": "Nigeria",
        "sources": "8-12",
        "researchGuidelines": "Focus on Nigerian market",
        "uploadedDocuments": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-draft",
            headers=headers,
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Test PASSED")
            return response.json()
        else:
            print("❌ Test FAILED")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "🚀 "*25)
    print("RESEARCH GENERATION API - TEST SUITE")
    print("🚀 "*25)
    
    if AUTH_TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n⚠️  WARNING: Please update AUTH_TOKEN in the script")
        print("Get a valid JWT token by logging in first")
        return
    
    # Test 1: Improve Topic
    improve_result = test_improve_topic()
    
    # Test 2: Alternative Topic
    previous_topic = None
    if improve_result and improve_result.get('improvedTopic'):
        previous_topic = improve_result['improvedTopic']
    test_alternative_topic(previous_topic)
    
    # Test 3: Generate Outline
    test_generate_outline()
    
    # Test 4: Upload Documents
    test_upload_documents()
    
    # Test 5: Generate Draft
    test_generate_draft()
    
    print("\n" + "="*50)
    print("TEST SUITE COMPLETED")
    print("="*50 + "\n")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════╗
    ║   Research Generation API Test Script         ║
    ║   ----------------------------------------     ║
    ║   Make sure the server is running:            ║
    ║   uvicorn app.main:app --reload --port 5000   ║
    ║                                                ║
    ║   Update AUTH_TOKEN before running!           ║
    ╚════════════════════════════════════════════════╝
    """)
    
    run_all_tests()

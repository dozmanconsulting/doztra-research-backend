#!/usr/bin/env python3
"""
Test script for API integrations
Tests AssemblyAI and Firecrawl API connections
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

async def test_assemblyai():
    """Test AssemblyAI API connection"""
    print("🎵 Testing AssemblyAI API...")
    
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }
    
    # Test with a sample audio URL
    test_data = {
        "audio_url": "https://assembly.ai/wildfires.mp3",
        "speech_model": "universal"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Submit transcription job
            async with session.post(
                "https://api.assemblyai.com/v2/transcript",
                headers=headers,
                json=test_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    transcript_id = result.get("id")
                    print(f"✅ AssemblyAI API connected successfully!")
                    print(f"   Transcript ID: {transcript_id}")
                    print(f"   Status: {result.get('status', 'unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ AssemblyAI API error: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ AssemblyAI connection failed: {e}")
        return False

async def test_firecrawl():
    """Test Firecrawl API connection"""
    print("\n🌐 Testing Firecrawl API...")
    
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Test with a simple webpage
    test_data = {
        "url": "https://example.com",
        "formats": ["markdown"],
        "onlyMainContent": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers=headers,
                json=test_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", {})
                    content_length = len(data.get("markdown", ""))
                    print(f"✅ Firecrawl API connected successfully!")
                    print(f"   Scraped content length: {content_length} characters")
                    print(f"   Page title: {data.get('metadata', {}).get('title', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Firecrawl API error: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Firecrawl connection failed: {e}")
        return False

async def test_youtube_api():
    """Test YouTube Data API connection"""
    print("\n📺 Testing YouTube Data API...")
    
    # Test with YouTube Data API v3
    test_url = f"https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": "dQw4w9WgXcQ",  # Rick Roll video ID for testing
        "key": YOUTUBE_API_KEY
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    items = result.get("items", [])
                    if items:
                        video = items[0]
                        snippet = video.get("snippet", {})
                        stats = video.get("statistics", {})
                        
                        print(f"✅ YouTube API connected successfully!")
                        print(f"   Video title: {snippet.get('title', 'N/A')}")
                        print(f"   Channel: {snippet.get('channelTitle', 'N/A')}")
                        print(f"   View count: {stats.get('viewCount', 'N/A')}")
                        return True
                    else:
                        print("❌ YouTube API: No video data returned")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ YouTube API error: {response.status}")
                    print(f"   Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ YouTube API connection failed: {e}")
        return False

async def test_vector_embeddings():
    """Test sentence-transformers for vector embeddings"""
    print("\n🔍 Testing Vector Embeddings...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load a lightweight model for testing
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test embedding generation
        test_texts = [
            "This is a test sentence for embedding generation.",
            "Knowledge base content processing with AI."
        ]
        
        embeddings = model.encode(test_texts)
        print(f"✅ Vector embeddings working!")
        print(f"   Model: all-MiniLM-L6-v2")
        print(f"   Embedding dimension: {embeddings.shape[1]}")
        print(f"   Test embeddings shape: {embeddings.shape}")
        return True
        
    except ImportError:
        print("❌ sentence-transformers not installed")
        print("   Run: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ Vector embeddings failed: {e}")
        return False

def test_milvus_connection():
    """Test Milvus vector database connection (local or Zilliz Cloud)"""
    print("\n🗄️  Testing Milvus Connection...")
    
    try:
        from pymilvus import connections, utility
        
        # Get connection parameters
        host = os.getenv("MILVUS_HOST", "localhost")
        port = int(os.getenv("MILVUS_PORT", "19530"))
        user = os.getenv("MILVUS_USER")
        password = os.getenv("MILVUS_PASSWORD")
        use_secure = os.getenv("MILVUS_USE_SECURE", "false").lower() == "true"
        
        # Prepare connection parameters
        connection_params = {
            "alias": "default",
            "host": host,
            "port": port
        }
        
        # Add authentication for Zilliz Cloud
        if user and password:
            connection_params["user"] = user
            connection_params["password"] = password
            
        # Add secure connection for Zilliz Cloud
        if use_secure:
            connection_params["secure"] = True
        
        # Try to connect
        connections.connect(**connection_params)
        
        # Test connection
        if connections.has_connection("default"):
            connection_type = "Zilliz Cloud" if use_secure else "Local Milvus"
            print(f"✅ {connection_type} connected successfully!")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            if user:
                print(f"   User: {user}")
            print(f"   Secure: {use_secure}")
            
            # Test basic operations
            try:
                # List collections to verify we can perform operations
                collections = utility.list_collections()
                print(f"   Collections: {len(collections)} found")
                return True
            except Exception as e:
                print(f"   ⚠️  Connected but operations failed: {e}")
                return True  # Connection works, operations might need setup
        else:
            print("❌ Milvus connection failed")
            return False
            
    except ImportError:
        print("❌ pymilvus not installed")
        print("   Run: pip install pymilvus")
        return False
    except Exception as e:
        print(f"❌ Milvus connection failed: {e}")
        if use_secure:
            print("   Check Zilliz Cloud credentials:")
            print(f"   - Host: {host}")
            print(f"   - User: {user}")
            print("   - Password: [check if correct]")
        else:
            print("   Make sure Milvus is running:")
            print("   docker run -d --name milvus-standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest standalone")
        return False

async def main():
    """Run all API tests"""
    print("🚀 Testing Knowledge Base API Integrations")
    print("=" * 50)
    
    results = []
    
    # Test APIs
    results.append(await test_assemblyai())
    results.append(await test_firecrawl())
    results.append(await test_youtube_api())
    results.append(await test_vector_embeddings())
    results.append(test_milvus_connection())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    services = ["AssemblyAI", "Firecrawl", "YouTube API", "Vector Embeddings", "Milvus"]
    for i, (service, result) in enumerate(zip(services, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service:20} {status}")
    
    total_passed = sum(results)
    print(f"\nTotal: {total_passed}/{len(results)} services working")
    
    if total_passed == len(results):
        print("🎉 All services are ready for production!")
    elif total_passed >= 2:
        print("⚠️  Some services need setup, but core functionality available")
    else:
        print("🔧 Multiple services need configuration")
    
    print("\n📝 Next Steps:")
    if not results[0]:  # AssemblyAI
        print("   - Check AssemblyAI API key in .env file")
    if not results[1]:  # Firecrawl  
        print("   - Check Firecrawl API key in .env file")
    if not results[2]:  # YouTube
        print("   - Check YouTube API key in .env file")
        print("   - Ensure YouTube Data API v3 is enabled in Google Cloud Console")
    if not results[3]:  # Embeddings
        print("   - Install: pip install sentence-transformers")
    if not results[4]:  # Milvus
        print("   - Start Milvus: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:latest standalone")

if __name__ == "__main__":
    asyncio.run(main())

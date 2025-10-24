#!/usr/bin/env python3
"""
Comprehensive YouTube Integration Test
Tests both YouTube Data API and transcript extraction
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our YouTube processor
from app.services.youtube_processing import youtube_processor

async def test_youtube_video_processing():
    """Test complete YouTube video processing"""
    print("🎬 Testing Complete YouTube Video Processing")
    print("=" * 50)
    
    # Test video URLs
    test_videos = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",
            "description": "Classic music video with transcript"
        },
        {
            "url": "https://youtu.be/dQw4w9WgXcQ", 
            "title": "Same video, different URL format",
            "description": "Testing youtu.be format"
        }
    ]
    
    for i, video in enumerate(test_videos, 1):
        print(f"\n📺 Test {i}: {video['title']}")
        print("-" * 40)
        
        try:
            # Extract video ID
            video_id = youtube_processor.extract_video_id(video["url"])
            print(f"✅ Video ID extracted: {video_id}")
            
            # Get metadata
            print("📊 Getting video metadata...")
            metadata = await youtube_processor.get_video_metadata(video_id)
            
            if not metadata.get("error"):
                print(f"✅ Metadata retrieved successfully")
                print(f"   Title: {metadata.get('title', 'N/A')}")
                print(f"   Channel: {metadata.get('channel_title', 'N/A')}")
                print(f"   Duration: {metadata.get('duration', 'N/A')}")
                print(f"   Views: {metadata.get('view_count', 'N/A'):,}")
                print(f"   Published: {metadata.get('published_at', 'N/A')}")
            else:
                print(f"❌ Metadata error: {metadata.get('error')}")
            
            # Get transcript
            print("📝 Getting video transcript...")
            transcript = await youtube_processor.get_video_transcript(video_id)
            
            if not transcript.get("error"):
                print(f"✅ Transcript retrieved successfully")
                print(f"   Language: {transcript.get('language', 'N/A')}")
                print(f"   Generated: {transcript.get('is_generated', 'N/A')}")
                print(f"   Word count: {transcript.get('word_count', 0):,}")
                print(f"   Duration: {transcript.get('duration_seconds', 0):.1f} seconds")
                
                # Show first 200 characters of transcript
                full_text = transcript.get('full_transcript', '')
                preview = full_text[:200] + "..." if len(full_text) > 200 else full_text
                print(f"   Preview: {preview}")
            else:
                print(f"❌ Transcript error: {transcript.get('error')}")
            
            # Test complete processing
            print("🔄 Testing complete processing...")
            result = await youtube_processor.process_youtube_video(video["url"])
            
            if not result.get("error"):
                print(f"✅ Complete processing successful")
                print(f"   Content length: {result.get('content_length', 0):,} characters")
                print(f"   Word count: {result.get('word_count', 0):,}")
                print(f"   Processing status: {result.get('processing_status', 'unknown')}")
            else:
                print(f"❌ Processing error: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print()

async def test_youtube_search():
    """Test YouTube search functionality"""
    print("🔍 Testing YouTube Search")
    print("=" * 30)
    
    try:
        # Search for videos
        search_results = await youtube_processor.search_videos(
            query="python programming tutorial",
            max_results=5
        )
        
        if search_results:
            print(f"✅ Search successful - found {len(search_results)} videos")
            for i, video in enumerate(search_results[:3], 1):
                print(f"   {i}. {video.get('title', 'N/A')}")
                print(f"      Channel: {video.get('channel_title', 'N/A')}")
                print(f"      Video ID: {video.get('video_id', 'N/A')}")
        else:
            print("❌ No search results returned")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")

async def test_transcript_extraction():
    """Test transcript extraction with different languages"""
    print("\n🌍 Testing Transcript Languages")
    print("=" * 35)
    
    # Test video with multiple language options
    video_id = "dQw4w9WgXcQ"  # Rick Roll has multiple language transcripts
    
    try:
        # Test different language preferences
        language_tests = [
            (["en"], "English"),
            (["es"], "Spanish"), 
            (["fr"], "French"),
            (["de"], "German"),
            (None, "Auto-detect")
        ]
        
        for languages, description in language_tests:
            print(f"\n🔤 Testing {description} transcript...")
            
            transcript = await youtube_processor.get_video_transcript(
                video_id, 
                languages=languages
            )
            
            if not transcript.get("error"):
                print(f"✅ {description} transcript available")
                print(f"   Language: {transcript.get('language', 'N/A')}")
                print(f"   Language code: {transcript.get('language_code', 'N/A')}")
                print(f"   Word count: {transcript.get('word_count', 0):,}")
            else:
                print(f"❌ {description} transcript not available: {transcript.get('error')}")
                
    except Exception as e:
        print(f"❌ Language test failed: {e}")

def test_video_id_extraction():
    """Test video ID extraction from various URL formats"""
    print("\n🔗 Testing Video ID Extraction")
    print("=" * 35)
    
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "invalid-url",
        ""
    ]
    
    for url in test_urls:
        video_id = youtube_processor.extract_video_id(url)
        status = "✅" if video_id == "dQw4w9WgXcQ" else "❌" if video_id else "⚠️"
        print(f"{status} {url[:50]:<50} → {video_id or 'None'}")

async def main():
    """Run all YouTube tests"""
    print("🚀 YouTube Integration Test Suite")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("❌ YouTube API key not configured")
        print("   Please set YOUTUBE_API_KEY in your .env file")
        return
    
    print(f"🔑 API Key configured: {api_key[:20]}...")
    
    # Run tests
    test_video_id_extraction()
    await test_youtube_video_processing()
    await test_youtube_search()
    await test_transcript_extraction()
    
    print("\n🎉 YouTube integration tests completed!")
    print("\n💡 Tips:")
    print("   - Some videos may not have transcripts available")
    print("   - Generated transcripts are usually available for popular videos")
    print("   - API quotas apply - use sparingly in production")
    print("   - Consider caching results to reduce API calls")

if __name__ == "__main__":
    asyncio.run(main())

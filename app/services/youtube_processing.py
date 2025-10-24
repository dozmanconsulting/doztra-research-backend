"""
YouTube Video Processing Service
Extract transcripts, metadata, and process video content
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import logging
import re
from urllib.parse import urlparse, parse_qs

# YouTube transcript extraction
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False

# YouTube Data API
try:
    import googleapiclient.discovery
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

logger = logging.getLogger(__name__)

class YouTubeProcessor:
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube_service = None
        
        if YOUTUBE_API_AVAILABLE and self.youtube_api_key:
            try:
                self.youtube_service = googleapiclient.discovery.build(
                    "youtube", "v3", developerKey=self.youtube_api_key
                )
                logger.info("YouTube Data API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize YouTube API: {e}")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata using YouTube Data API"""
        if not self.youtube_service:
            return {"error": "YouTube Data API not available"}
        
        try:
            request = self.youtube_service.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return {"error": "Video not found"}
            
            video = response["items"][0]
            snippet = video["snippet"]
            statistics = video.get("statistics", {})
            content_details = video.get("contentDetails", {})
            
            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": content_details.get("duration", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
                "default_language": snippet.get("defaultLanguage", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("maxres", {}).get("url", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to get video metadata: {e}")
            return {"error": str(e)}
    
    async def get_video_transcript(
        self, 
        video_id: str, 
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """Get video transcript"""
        if not TRANSCRIPT_API_AVAILABLE:
            return {"error": "YouTube transcript API not available"}
        
        try:
            # Default to English if no languages specified
            if not languages:
                languages = ['en', 'en-US', 'en-GB']
            
            # Try to get transcript in preferred languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = None
            
            # Try to find transcript in preferred languages
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except:
                    continue
            
            # If no preferred language found, try auto-generated English
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Get any available transcript
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0]
            
            if not transcript:
                return {"error": "No transcript available"}
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            
            # Format transcript
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            # Extract detailed transcript with timestamps
            detailed_transcript = []
            for entry in transcript_data:
                detailed_transcript.append({
                    "start": entry.get("start", 0),
                    "duration": entry.get("duration", 0),
                    "text": entry.get("text", "")
                })
            
            return {
                "video_id": video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable,
                "full_transcript": formatted_transcript,
                "detailed_transcript": detailed_transcript,
                "word_count": len(formatted_transcript.split()),
                "duration_seconds": sum(entry.get("duration", 0) for entry in transcript_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get transcript for video {video_id}: {e}")
            return {"error": str(e)}
    
    async def process_youtube_video(self, url: str) -> Dict[str, Any]:
        """Complete YouTube video processing"""
        video_id = self.extract_video_id(url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
        
        try:
            # Get metadata and transcript concurrently
            metadata_task = self.get_video_metadata(video_id)
            transcript_task = self.get_video_transcript(video_id)
            
            metadata, transcript = await asyncio.gather(
                metadata_task, transcript_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(metadata, Exception):
                metadata = {"error": str(metadata)}
            if isinstance(transcript, Exception):
                transcript = {"error": str(transcript)}
            
            # Fallback: if YouTube Data API is unavailable, scrape OG tags directly from page
            if metadata.get("error"):
                try:
                    og = await self._fetch_og_from_page(url)
                    if og:
                        metadata = {
                            "video_id": video_id,
                            "title": og.get("og:title", ""),
                            "description": og.get("og:description", ""),
                            "channel_title": og.get("og:site_name", ""),
                            "thumbnail_url": og.get("og:image", ""),
                        }
                except Exception as e:
                    logger.warning(f"OG fallback failed for {url}: {e}")

            # Combine results
            result = {
                "video_id": video_id,
                "url": url,
                "metadata": metadata,
                "transcript": transcript,
                "processing_status": "completed"
            }
            
            # Extract content for knowledge base
            content = ""
            if transcript and not transcript.get("error"):
                content = transcript.get("full_transcript", "")
            
            if metadata and not metadata.get("error"):
                title = metadata.get("title", "") or ""
                description = metadata.get("description", "") or ""
                # Always include title/description even if transcript is empty
                content = f"Title: {title}\n\nDescription: {description}\n\nTranscript:\n{content}".strip()
            
            result["extracted_content"] = content
            result["content_length"] = len(content)
            result["word_count"] = len(content.split()) if content else 0
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process YouTube video: {e}")
            return {
                "video_id": video_id,
                "url": url,
                "error": str(e),
                "processing_status": "failed"
            }
    
    async def get_channel_videos(
        self, 
        channel_id: str, 
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get videos from a YouTube channel"""
        if not self.youtube_service:
            return []
        
        try:
            # Get channel's uploads playlist
            channel_request = self.youtube_service.channels().list(
                part="contentDetails",
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response.get("items"):
                return []
            
            uploads_playlist_id = (
                channel_response["items"][0]
                ["contentDetails"]
                ["relatedPlaylists"]
                ["uploads"]
            )
            
            # Get videos from uploads playlist
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_request = self.youtube_service.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                playlist_response = playlist_request.execute()
                
                for item in playlist_response.get("items", []):
                    snippet = item["snippet"]
                    videos.append({
                        "video_id": snippet["resourceId"]["videoId"],
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
                    })
                
                next_page_token = playlist_response.get("nextPageToken")
                if not next_page_token:
                    break
            
            return videos[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 25,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """Search YouTube videos"""
        if not self.youtube_service:
            return []
        
        try:
            search_request = self.youtube_service.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order=order
            )
            search_response = search_request.execute()
            
            videos = []
            for item in search_response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to search videos: {e}")
            return []
    
    def extract_key_moments(self, transcript_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key moments from transcript"""
        key_moments = []
        
        # Simple keyword-based extraction (can be enhanced with NLP)
        keywords = [
            "important", "key", "main", "summary", "conclusion",
            "first", "second", "third", "finally", "in conclusion"
        ]
        
        for entry in transcript_data:
            text = entry.get("text", "").lower()
            if any(keyword in text for keyword in keywords):
                key_moments.append({
                    "timestamp": entry.get("start", 0),
                    "text": entry.get("text", ""),
                    "duration": entry.get("duration", 0)
                })
        
        return key_moments

# Global service instance
youtube_processor = YouTubeProcessor()

    

"""
AssemblyAI Audio Transcription Service
Handles audio file transcription with advanced features
"""

import asyncio
import aiohttp
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AssemblyAIService:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.base_url = "https://api.assemblyai.com/v2"
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
    
    async def upload_audio_file(self, file_path: str) -> str:
        """Upload audio file to AssemblyAI and get upload URL"""
        upload_url = f"{self.base_url}/upload"
        
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                async with session.post(
                    upload_url,
                    headers={"authorization": self.api_key},
                    data=f
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["upload_url"]
                    else:
                        raise Exception(f"Failed to upload audio: {response.status}")
    
    async def transcribe_audio(
        self, 
        audio_url: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Transcribe audio with advanced options"""
        
        # Default transcription options
        transcript_request = {
            "audio_url": audio_url,
            "speaker_labels": True,  # Speaker diarization
            "auto_chapters": True,   # Automatic chapter detection
            "sentiment_analysis": True,  # Sentiment analysis
            "entity_detection": True,    # Named entity recognition
            "iab_categories": True,      # Content categorization
            "content_safety": True,      # Content moderation
            "auto_highlights": True,     # Key phrase extraction
            "summarization": True,       # Automatic summarization
            "summary_model": "informative",
            "summary_type": "bullets"
        }
        
        # Override with custom options
        if options:
            transcript_request.update(options)
        
        # Submit transcription job
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/transcript",
                headers=self.headers,
                json=transcript_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    transcript_id = result["id"]
                    
                    # Poll for completion
                    return await self._poll_transcription(transcript_id)
                else:
                    raise Exception(f"Failed to start transcription: {response.status}")
    
    async def _poll_transcription(self, transcript_id: str) -> Dict[str, Any]:
        """Poll transcription status until complete"""
        polling_url = f"{self.base_url}/transcript/{transcript_id}"
        
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(polling_url, headers=self.headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result["status"]
                        
                        if status == "completed":
                            return result
                        elif status == "error":
                            raise Exception(f"Transcription failed: {result.get('error')}")
                        else:
                            # Wait 5 seconds before polling again
                            await asyncio.sleep(5)
                    else:
                        raise Exception(f"Failed to check transcription status: {response.status}")
    
    async def transcribe_from_url(self, audio_url: str) -> Dict[str, Any]:
        """Transcribe audio directly from URL"""
        return await self.transcribe_audio(audio_url)
    
    async def transcribe_from_file(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio from local file"""
        # First upload the file
        upload_url = await self.upload_audio_file(file_path)
        
        # Then transcribe
        return await self.transcribe_audio(upload_url)
    
    def extract_transcript_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format transcript data"""
        return {
            "transcript_id": result.get("id"),
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0),
            "audio_duration": result.get("audio_duration"),
            "speakers": self._extract_speakers(result),
            "chapters": result.get("chapters", []),
            "sentiment": result.get("sentiment_analysis_results", []),
            "entities": result.get("entities", []),
            "categories": result.get("iab_categories_result", {}),
            "content_safety": result.get("content_safety_labels", {}),
            "highlights": result.get("auto_highlights_result", {}),
            "summary": result.get("summary", ""),
            "words": result.get("words", [])
        }
    
    def _extract_speakers(self, result: Dict[str, Any]) -> list:
        """Extract speaker information"""
        utterances = result.get("utterances", [])
        speakers = {}
        
        for utterance in utterances:
            speaker = utterance.get("speaker")
            if speaker not in speakers:
                speakers[speaker] = {
                    "speaker_id": speaker,
                    "total_time": 0,
                    "utterance_count": 0
                }
            
            speakers[speaker]["total_time"] += utterance.get("end", 0) - utterance.get("start", 0)
            speakers[speaker]["utterance_count"] += 1
        
        return list(speakers.values())

# Global service instance
audio_service = AssemblyAIService()

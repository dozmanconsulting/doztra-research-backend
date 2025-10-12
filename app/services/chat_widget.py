"""
Dedicated service for ChatWidget functionality.
Handles conversation management and OpenAI integration specifically for the landing page chat widget.
"""

import logging
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc, asc, func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI client
import openai
import os

class ChatWidgetService:
    """
    Service class for ChatWidget-specific functionality.
    Handles conversation management, message processing, and OpenAI integration.
    """
    
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Chat widget specific system prompts
        self.system_prompts = {
            "default": """You are Doztra AI, a helpful research assistant specializing in academic research. 
            You help students and researchers with finding academic sources, research paper assistance, 
            literature reviews, dissertation support, summarizing academic articles, and research methodology.
            
            Keep responses concise, helpful, and focused on academic research needs. 
            Always be encouraging and supportive of the user's research goals.""",
            
            "find-academic-sources": """You are Doztra AI, specialized in helping users find academic sources. 
            Focus on providing guidance on where to find reliable academic papers, databases to search, 
            and how to evaluate source credibility. Offer specific suggestions for academic databases 
            and search strategies.""",
            
            "research-paper-help": """You are Doztra AI, specialized in research paper assistance. 
            Help with paper structure, writing techniques, citation formats, and research methodologies. 
            Provide guidance on organizing research, developing arguments, and academic writing best practices.""",
            
            "literature-review": """You are Doztra AI, specialized in literature review assistance. 
            Help with organizing sources, identifying themes, synthesizing research, and structuring 
            literature reviews. Provide guidance on critical analysis and academic writing.""",
            
            "dissertation-thesis": """You are Doztra AI, specialized in dissertation and thesis support. 
            Help with research planning, methodology selection, data analysis, and academic writing. 
            Provide guidance on the dissertation process and academic requirements.""",
            
            "summarize-articles": """You are Doztra AI, specialized in summarizing academic articles. 
            Help users understand complex academic papers by providing clear, concise summaries 
            that highlight key findings, methodologies, and implications.""",
            
            "methodology-selection": """You are Doztra AI, specialized in research methodology guidance. 
            Help users select appropriate research methods, understand different methodological approaches, 
            and design effective research studies."""
        }
    
    async def process_widget_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        selected_option: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a message from the chat widget and generate an AI response.
        
        Args:
            message: The user's message
            conversation_history: Previous messages in the conversation
            selected_option: Selected chat option (e.g., 'find-academic-sources')
            user_id: Optional user ID for tracking
            
        Returns:
            Dictionary containing the AI response and metadata
        """
        try:
            # Select appropriate system prompt based on selected option
            system_prompt = self.system_prompts.get(selected_option, self.system_prompts["default"])
            
            # Build conversation messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Generate response using OpenAI
            response = await self._generate_openai_response(messages)
            
            # Generate tool recommendation based on the message
            tool_recommendation = self._generate_tool_recommendation(message)
            
            return {
                "response": response["content"],
                "conversation_id": str(uuid.uuid4()),  # Generate session ID
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": tool_recommendation,
                "usage": response.get("usage", {}),
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": selected_option
            }
            
        except Exception as e:
            logger.error(f"Error processing widget message: {str(e)}")
            return {
                "response": "I'm having trouble connecting right now. Please try again or explore our research tools using the options below.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": None,
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _generate_openai_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate response using OpenAI API.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary containing response content and usage info
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,  # Keep responses concise for widget
                temperature=0.7,
                stream=False
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
    
    def _generate_tool_recommendation(self, message: str) -> Optional[str]:
        """
        Generate tool recommendation based on user message content.
        
        Args:
            message: User's message
            
        Returns:
            Recommended tool/option or None
        """
        message_lower = message.lower()
        
        # Simple keyword-based recommendation logic
        if any(keyword in message_lower for keyword in ["find", "source", "paper", "article", "journal"]):
            return "find-academic-sources"
        elif any(keyword in message_lower for keyword in ["write", "writing", "paper", "essay", "structure"]):
            return "research-paper-help"
        elif any(keyword in message_lower for keyword in ["literature", "review", "synthesis", "analyze"]):
            return "literature-review"
        elif any(keyword in message_lower for keyword in ["dissertation", "thesis", "phd", "masters"]):
            return "dissertation-thesis"
        elif any(keyword in message_lower for keyword in ["summarize", "summary", "abstract", "key points"]):
            return "summarize-articles"
        elif any(keyword in message_lower for keyword in ["methodology", "method", "approach", "research design"]):
            return "methodology-selection"
        
        return None
    
    def get_chat_options(self) -> List[Dict[str, str]]:
        """
        Get available chat options for the widget.
        
        Returns:
            List of chat options with IDs and labels
        """
        return [
            {"id": "find-academic-sources", "label": "Find Academic Sources"},
            {"id": "research-paper-help", "label": "Research Paper Help"},
            {"id": "literature-review", "label": "Literature Review Assistance"},
            {"id": "dissertation-thesis", "label": "Dissertation/Thesis Support"},
            {"id": "summarize-articles", "label": "Summarize Academic Articles"},
            {"id": "methodology-selection", "label": "Research Methodology Help"}
        ]
    
    async def get_option_response(self, option_id: str) -> Dict[str, Any]:
        """
        Get a predefined response for a selected chat option.
        
        Args:
            option_id: ID of the selected option
            
        Returns:
            Dictionary containing the response and metadata
        """
        option_responses = {
            "find-academic-sources": "Great choice! I can help you find reliable academic sources for your research. What's your research topic or field of study?",
            "research-paper-help": "I'd be happy to help you with your research paper! What specific aspect would you like assistance with - structure, writing, citations, or something else?",
            "literature-review": "Excellent! Literature reviews are crucial for good research. What's your research area, and are you looking for help with organizing sources or writing the review?",
            "dissertation-thesis": "I'm here to support your dissertation or thesis work! What stage are you at, and what specific help do you need?",
            "summarize-articles": "I can help you summarize academic articles effectively. Do you have specific papers you'd like me to help summarize, or do you need guidance on summarization techniques?",
            "methodology-selection": "Research methodology is a key part of any study! What type of research are you conducting, and what methodological guidance do you need?"
        }
        
        response_text = option_responses.get(
            option_id, 
            "I'm here to help with your research needs! Could you tell me more about what you're working on?"
        )
        
        return {
            "response": response_text,
            "conversation_id": str(uuid.uuid4()),
            "message_id": str(uuid.uuid4()),
            "tool_recommendation": option_id,
            "usage": {},
            "timestamp": datetime.utcnow().isoformat(),
            "selected_option": option_id
        }
    
    def get_initial_message(self) -> Dict[str, Any]:
        """
        Get the initial welcome message for the chat widget.
        
        Returns:
            Dictionary containing the initial message
        """
        return {
            "id": str(uuid.uuid4()),
            "text": "Need help finding academic sources for your research? I can help you find and summarize relevant papers quickly.",
            "isBot": True,
            "timestamp": datetime.utcnow().isoformat(),
            "options": self.get_chat_options()
        }


# Create a singleton instance
chat_widget_service = ChatWidgetService()

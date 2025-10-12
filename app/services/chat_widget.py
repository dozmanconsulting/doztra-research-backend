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

# Import academic search service
from app.services.academic_search import academic_search_service

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
            # Check if this is a request for academic sources
            if selected_option == "find-academic-sources" or self._is_source_search_request(message):
                return await self._handle_academic_source_search(message, selected_option)
            
            # Check for other specialized requests
            if selected_option == "literature-review" or self._is_literature_review_request(message):
                return await self._handle_literature_review_assistance(message, selected_option)
            
            if selected_option == "dissertation-thesis" or self._is_dissertation_request(message):
                return await self._handle_dissertation_assistance(message, selected_option)
            
            if selected_option == "summarize-articles" or self._is_summarization_request(message):
                return await self._handle_article_summarization(message, selected_option)
            
            if selected_option == "methodology-selection" or self._is_methodology_request(message):
                return await self._handle_methodology_guidance(message, selected_option)
            
            # For other requests, use regular AI chat
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
    
    def _is_source_search_request(self, message: str) -> bool:
        """
        Check if the message is requesting academic source search.
        
        Args:
            message: User's message
            
        Returns:
            True if this is a source search request
        """
        message_lower = message.lower()
        source_keywords = [
            "find sources", "find papers", "find articles", "find research",
            "search for", "look for", "need sources", "academic sources",
            "research papers", "scholarly articles", "peer reviewed",
            "literature on", "studies about", "papers about"
        ]
        
        return any(keyword in message_lower for keyword in source_keywords)
    
    def _is_literature_review_request(self, message: str) -> bool:
        """Check if the message is requesting literature review help."""
        message_lower = message.lower()
        lit_review_keywords = [
            "literature review", "lit review", "review paper", "systematic review",
            "meta-analysis", "review of literature", "synthesize research",
            "organize sources", "thematic analysis"
        ]
        return any(keyword in message_lower for keyword in lit_review_keywords)
    
    def _is_dissertation_request(self, message: str) -> bool:
        """Check if the message is requesting dissertation/thesis help."""
        message_lower = message.lower()
        dissertation_keywords = [
            "dissertation", "thesis", "phd", "doctoral", "masters",
            "research proposal", "chapter", "defense", "committee"
        ]
        return any(keyword in message_lower for keyword in dissertation_keywords)
    
    def _is_summarization_request(self, message: str) -> bool:
        """Check if the message is requesting article summarization."""
        message_lower = message.lower()
        summary_keywords = [
            "summarize", "summary", "abstract", "key points",
            "main findings", "tldr", "brief overview", "condense"
        ]
        return any(keyword in message_lower for keyword in summary_keywords)
    
    def _is_methodology_request(self, message: str) -> bool:
        """Check if the message is requesting methodology guidance."""
        message_lower = message.lower()
        methodology_keywords = [
            "methodology", "method", "research design", "approach",
            "qualitative", "quantitative", "mixed methods", "data collection",
            "analysis", "framework", "paradigm"
        ]
        return any(keyword in message_lower for keyword in methodology_keywords)
    
    async def _handle_academic_source_search(self, message: str, selected_option: Optional[str]) -> Dict[str, Any]:
        """
        Handle academic source search requests.
        
        Args:
            message: User's search query/message
            selected_option: Selected option (if any)
            
        Returns:
            Dictionary containing search results and response
        """
        try:
            # Extract search query from message
            search_query = self._extract_search_query(message)
            
            if not search_query:
                return {
                    "response": "I'd be happy to help you find academic sources! Could you please tell me what topic or research area you're interested in?",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "find-academic-sources",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
            
            # Search for academic sources
            logger.info(f"Searching for academic sources: {search_query}")
            search_results = await academic_search_service.search_academic_sources(
                query=search_query,
                max_results=8
            )
            
            if search_results["success"] and search_results["sources"]:
                # Format the response with found sources
                response = self._format_source_search_response(search_results, search_query)
                
                return {
                    "response": response,
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "find-academic-sources",
                    "usage": {"sources_found": len(search_results["sources"])},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option,
                    "sources": search_results["sources"]  # Include raw source data
                }
            else:
                return {
                    "response": f"I searched for academic sources on '{search_query}' but couldn't find specific results at the moment. This might be due to API limitations or the search terms used. You can try:\n\n• Refining your search terms\n• Using more specific keywords\n• Checking academic databases like Google Scholar, PubMed, or IEEE Xplore directly\n\nWould you like me to help you refine your search terms or suggest alternative research strategies?",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "find-academic-sources",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
                
        except Exception as e:
            logger.error(f"Error handling academic source search: {str(e)}")
            return {
                "response": "I encountered an issue while searching for academic sources. Please try again with a more specific research topic, or I can help you develop a research strategy instead.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "find-academic-sources",
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _extract_search_query(self, message: str) -> str:
        """
        Extract the actual search query from the user's message.
        
        Args:
            message: User's message
            
        Returns:
            Cleaned search query
        """
        # Remove common phrases to get to the core topic
        message_lower = message.lower()
        
        # Remove action phrases
        remove_phrases = [
            "find sources on", "find papers on", "find articles about",
            "search for", "look for", "i need sources on", "help me find",
            "can you find", "sources about", "papers about", "research on",
            "find academic sources", "find research papers"
        ]
        
        query = message_lower
        for phrase in remove_phrases:
            query = query.replace(phrase, "").strip()
        
        # Remove common words
        stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = query.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return " ".join(filtered_words).strip()
    
    def _format_source_search_response(self, search_results: Dict[str, Any], query: str) -> str:
        """
        Format the academic source search results into a readable response.
        
        Args:
            search_results: Results from academic search
            query: Original search query
            
        Returns:
            Formatted response string
        """
        sources = search_results["sources"]
        metadata = search_results["metadata"]
        
        response = f"I found {len(sources)} relevant academic sources on '{query}':\n\n"
        
        for i, source in enumerate(sources[:6], 1):  # Limit to top 6 for chat
            title = source.get("title", "Untitled")
            authors = source.get("authors", [])
            year = source.get("year", "Unknown year")
            venue = source.get("venue", "")
            abstract = source.get("abstract", "")
            
            # Format authors
            if authors:
                if len(authors) == 1:
                    author_str = authors[0]
                elif len(authors) == 2:
                    author_str = f"{authors[0]} & {authors[1]}"
                else:
                    author_str = f"{authors[0]} et al."
            else:
                author_str = "Unknown authors"
            
            response += f"**{i}. {title}**\n"
            response += f"*{author_str} ({year})*\n"
            
            if venue:
                response += f"Published in: {venue}\n"
            
            if abstract:
                # Truncate abstract for chat display
                short_abstract = abstract[:200] + "..." if len(abstract) > 200 else abstract
                response += f"Abstract: {short_abstract}\n"
            
            response += "\n"
        
        databases_searched = ", ".join(metadata.get("databases_searched", []))
        response += f"*Sources searched: {databases_searched}*\n\n"
        response += "Would you like me to help you with any specific aspect of these sources, such as summarizing key findings or helping you evaluate their relevance to your research?"
        
        return response
    
    async def _handle_literature_review_assistance(self, message: str, selected_option: Optional[str]) -> Dict[str, Any]:
        """Handle literature review assistance requests."""
        try:
            # Extract research topic from message
            topic = self._extract_research_topic(message)
            
            if not topic:
                return {
                    "response": "I'd be happy to help with your literature review! Please tell me:\n\n• What's your research topic or field?\n• What specific aspect do you need help with (organizing sources, identifying themes, writing structure)?\n• Do you have sources already or need help finding them?\n\nJust share your research topic and I'll provide targeted literature review guidance!",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "literature-review",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
            
            # Generate literature review guidance
            guidance = await self._generate_literature_review_guidance(topic)
            
            return {
                "response": guidance,
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "literature-review",
                "usage": {"guidance_generated": True},
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": selected_option
            }
            
        except Exception as e:
            logger.error(f"Error handling literature review assistance: {str(e)}")
            return {
                "response": "I encountered an issue while generating literature review guidance. Please try again with your specific research topic, and I'll help you structure an effective literature review.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "literature-review",
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _handle_dissertation_assistance(self, message: str, selected_option: Optional[str]) -> Dict[str, Any]:
        """Handle dissertation/thesis assistance requests."""
        try:
            topic = self._extract_research_topic(message)
            
            if not topic:
                return {
                    "response": "I'm here to support your dissertation/thesis journey! Please share:\n\n• Your research topic or field\n• What stage you're at (proposal, literature review, methodology, writing, etc.)\n• Specific challenges you're facing\n• Your academic level (Masters, PhD)\n\nTell me about your dissertation topic and I'll provide targeted guidance!",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "dissertation-thesis",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
            
            # Generate dissertation guidance
            guidance = await self._generate_dissertation_guidance(topic)
            
            return {
                "response": guidance,
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "dissertation-thesis",
                "usage": {"guidance_generated": True},
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": selected_option
            }
            
        except Exception as e:
            logger.error(f"Error handling dissertation assistance: {str(e)}")
            return {
                "response": "I encountered an issue while generating dissertation guidance. Please share your research topic and current stage, and I'll provide comprehensive support for your dissertation work.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "dissertation-thesis",
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _handle_article_summarization(self, message: str, selected_option: Optional[str]) -> Dict[str, Any]:
        """Handle article summarization requests."""
        try:
            # Check if user provided article content or URL
            article_content = self._extract_article_content(message)
            
            if not article_content:
                return {
                    "response": "I can help you summarize academic articles! Please provide:\n\n• **Article text/content** - Paste the article content\n• **Article title and authors** - For context\n• **Specific focus** - What aspects to emphasize (methodology, findings, implications)\n\n**Example**: \"Summarize this article: [paste content here]\"\n\nOr tell me what type of summarization help you need!",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "summarize-articles",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
            
            # Generate article summary
            summary = await self._generate_article_summary(article_content)
            
            return {
                "response": summary,
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "summarize-articles",
                "usage": {"summary_generated": True},
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": selected_option
            }
            
        except Exception as e:
            logger.error(f"Error handling article summarization: {str(e)}")
            return {
                "response": "I encountered an issue while summarizing the article. Please try again by pasting the article content or providing more details about what you'd like summarized.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "summarize-articles",
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _handle_methodology_guidance(self, message: str, selected_option: Optional[str]) -> Dict[str, Any]:
        """Handle research methodology guidance requests."""
        try:
            topic = self._extract_research_topic(message)
            
            if not topic:
                return {
                    "response": "I can help you select the right research methodology! Please tell me:\n\n• **Research topic/question** - What are you studying?\n• **Research type** - Exploratory, descriptive, explanatory?\n• **Data preference** - Numbers (quantitative), interviews (qualitative), or both?\n• **Academic level** - Undergraduate, Masters, PhD?\n\nShare your research focus and I'll recommend appropriate methodologies!",
                    "conversation_id": str(uuid.uuid4()),
                    "message_id": str(uuid.uuid4()),
                    "tool_recommendation": "methodology-selection",
                    "usage": {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "selected_option": selected_option
                }
            
            # Generate methodology guidance
            guidance = await self._generate_methodology_guidance(topic)
            
            return {
                "response": guidance,
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "methodology-selection",
                "usage": {"guidance_generated": True},
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": selected_option
            }
            
        except Exception as e:
            logger.error(f"Error handling methodology guidance: {str(e)}")
            return {
                "response": "I encountered an issue while generating methodology guidance. Please share your research topic and questions, and I'll help you select the most appropriate research methodology.",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": "methodology-selection",
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    def _extract_research_topic(self, message: str) -> str:
        """Extract research topic from user message."""
        # Similar to search query extraction but for research topics
        message_lower = message.lower()
        
        # Remove action phrases
        remove_phrases = [
            "help me with", "i need help with", "working on", "research on",
            "studying", "looking at", "focusing on", "about", "regarding"
        ]
        
        topic = message_lower
        for phrase in remove_phrases:
            topic = topic.replace(phrase, "").strip()
        
        # Clean up and return
        return topic.strip()
    
    def _extract_article_content(self, message: str) -> str:
        """Extract article content from user message."""
        # Look for common patterns indicating article content
        message_lower = message.lower()
        
        if "summarize this" in message_lower or "summary of" in message_lower:
            # Extract content after the instruction
            parts = message.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
        
        # If message is long, assume it's article content
        if len(message) > 200:
            return message
        
        return ""
    
    async def _generate_literature_review_guidance(self, topic: str) -> str:
        """Generate comprehensive literature review guidance."""
        prompt = f"""
        Provide comprehensive literature review guidance for the research topic: "{topic}"
        
        Include:
        1. Key themes and areas to explore
        2. Suggested search terms and databases
        3. Structure for organizing the literature review
        4. Critical analysis approaches
        5. Common gaps to look for
        6. Tips for synthesis and writing
        
        Make it practical and actionable for a student.
        """
        
        response = await self._generate_openai_response([
            {"role": "system", "content": "You are an expert academic writing advisor specializing in literature reviews."},
            {"role": "user", "content": prompt}
        ])
        
        return response["content"]
    
    async def _generate_dissertation_guidance(self, topic: str) -> str:
        """Generate comprehensive dissertation guidance."""
        prompt = f"""
        Provide comprehensive dissertation guidance for the research topic: "{topic}"
        
        Include:
        1. Potential research questions and objectives
        2. Dissertation structure and chapters
        3. Timeline and milestone suggestions
        4. Key methodological considerations
        5. Common challenges and how to overcome them
        6. Resources and next steps
        
        Make it encouraging and practical for a graduate student.
        """
        
        response = await self._generate_openai_response([
            {"role": "system", "content": "You are an experienced dissertation advisor and academic mentor."},
            {"role": "user", "content": prompt}
        ])
        
        return response["content"]
    
    async def _generate_article_summary(self, article_content: str) -> str:
        """Generate a comprehensive article summary."""
        prompt = f"""
        Provide a comprehensive summary of this academic article:
        
        {article_content[:3000]}  # Limit content to avoid token limits
        
        Include:
        1. Main research question/objective
        2. Methodology used
        3. Key findings
        4. Implications and significance
        5. Limitations mentioned
        6. Relevance for further research
        
        Keep it concise but comprehensive.
        """
        
        response = await self._generate_openai_response([
            {"role": "system", "content": "You are an expert at summarizing academic articles clearly and comprehensively."},
            {"role": "user", "content": prompt}
        ])
        
        return response["content"]
    
    async def _generate_methodology_guidance(self, topic: str) -> str:
        """Generate research methodology guidance."""
        prompt = f"""
        Provide research methodology guidance for the topic: "{topic}"
        
        Include:
        1. Recommended research approaches (qualitative, quantitative, mixed)
        2. Suitable data collection methods
        3. Sampling strategies
        4. Analysis techniques
        5. Ethical considerations
        6. Practical implementation tips
        
        Explain the rationale for each recommendation.
        """
        
        response = await self._generate_openai_response([
            {"role": "system", "content": "You are a research methodology expert helping students design robust studies."},
            {"role": "user", "content": prompt}
        ])
        
        return response["content"]

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
        # For find-academic-sources, provide a helpful prompt to get started
        if option_id == "find-academic-sources":
            return {
                "response": "Great choice! I can help you find reliable academic sources for your research. Please tell me:\n\n• What's your research topic or field of study?\n• Are you looking for recent papers or historical research?\n• Any specific type of sources (journal articles, conference papers, etc.)?\n\nJust type your research topic and I'll search for relevant academic sources!",
                "conversation_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "tool_recommendation": option_id,
                "usage": {},
                "timestamp": datetime.utcnow().isoformat(),
                "selected_option": option_id
            }
        
        # Other option responses
        option_responses = {
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

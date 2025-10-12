"""
API routes for AI-powered prompt generation.
This is a core feature that helps users create effective prompts for various use cases.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json
import logging

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import openai_service
from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

class PromptGenerationRequest(BaseModel):
    """Request model for prompt generation"""
    prompt_type: str = Field(..., description="Type of prompt (general, content, creative, technical, business, marketing, academic)")
    topic: str = Field(..., description="Main topic or subject for the prompt")
    additional_context: Optional[str] = Field(None, description="Additional context, requirements, or details")
    tags: List[str] = Field(default=[], description="Tags to categorize the prompt (ai, writing, technical, business)")
    user_intent: Optional[str] = Field(None, description="What the user wants to achieve with this prompt")

class PromptGenerationResponse(BaseModel):
    """Response model for generated prompt"""
    prompt_id: str
    generated_prompt: str
    prompt_type: str
    topic: str
    tags: List[str]
    usage_tips: List[str]
    variations: List[str]
    created_at: str
    user_id: str

class SavedPrompt(BaseModel):
    """Model for saved prompts"""
    prompt_id: str
    title: str
    generated_prompt: str
    prompt_type: str
    topic: str
    tags: List[str]
    created_at: str
    is_favorite: bool = False

# Prompt generation templates and strategies
PROMPT_STRATEGIES = {
    "general": {
        "template": "Create a comprehensive and clear prompt for {topic}. {context}",
        "structure": "Context + Task + Format + Examples",
        "tips": [
            "Be specific about what you want",
            "Include context for better results",
            "Specify the desired output format",
            "Add examples when helpful"
        ]
    },
    "content": {
        "template": "Generate engaging content about {topic}. {context}",
        "structure": "Audience + Purpose + Tone + Content Type",
        "tips": [
            "Define your target audience clearly",
            "Specify the content format (blog, social media, etc.)",
            "Include tone and style preferences",
            "Mention key points to cover"
        ]
    },
    "creative": {
        "template": "Create imaginative and original content for {topic}. {context}",
        "structure": "Creative Brief + Style + Constraints + Inspiration",
        "tips": [
            "Encourage creative thinking and originality",
            "Specify the creative medium or format",
            "Include style or mood preferences",
            "Mention any constraints or requirements"
        ]
    },
    "technical": {
        "template": "Provide technical guidance and solutions for {topic}. {context}",
        "structure": "Problem + Technical Requirements + Solution Format",
        "tips": [
            "Be precise about technical requirements",
            "Specify the technical level (beginner, intermediate, advanced)",
            "Include relevant technologies or frameworks",
            "Request code examples when applicable"
        ]
    },
    "business": {
        "template": "Generate business-focused insights and strategies for {topic}. {context}",
        "structure": "Business Context + Objectives + Stakeholders + Deliverables",
        "tips": [
            "Define business objectives clearly",
            "Identify key stakeholders",
            "Specify desired business outcomes",
            "Include relevant industry context"
        ]
    },
    "marketing": {
        "template": "Create compelling marketing content for {topic}. {context}",
        "structure": "Target Audience + Value Proposition + Channel + Call-to-Action",
        "tips": [
            "Define your target audience demographics",
            "Highlight unique value propositions",
            "Specify marketing channels and platforms",
            "Include clear calls-to-action"
        ]
    },
    "academic": {
        "template": "Develop scholarly and research-oriented content for {topic}. {context}",
        "structure": "Research Question + Methodology + Sources + Academic Standards",
        "tips": [
            "Frame clear research questions",
            "Specify academic level and discipline",
            "Include citation and formatting requirements",
            "Mention required scholarly sources"
        ]
    }
}

def generate_intelligent_prompt(prompt_type: str, topic: str, additional_context: str = "", tags: List[str] = []) -> Dict[str, Any]:
    """
    Generate an intelligent, tailored prompt based on user input
    """
    try:
        # Get strategy for prompt type
        strategy = PROMPT_STRATEGIES.get(prompt_type, PROMPT_STRATEGIES["general"])
        
        # Build context string
        context_parts = []
        if additional_context:
            context_parts.append(f"Additional context: {additional_context}")
        
        if tags:
            tag_context = {
                "ai": "Focus on AI and machine learning applications",
                "writing": "Emphasize writing quality and style",
                "technical": "Include technical depth and accuracy",
                "business": "Consider business impact and ROI"
            }
            for tag in tags:
                if tag in tag_context:
                    context_parts.append(tag_context[tag])
        
        context = " ".join(context_parts)
        
        # Generate the main prompt using AI
        system_prompt = f"""You are an expert prompt engineer. Create a high-quality, effective prompt for {prompt_type} use cases.

The user wants help with: {topic}
Additional context: {context}
Tags: {', '.join(tags)}

Generate a comprehensive prompt that:
1. Is clear and specific
2. Includes proper context and instructions
3. Specifies desired output format
4. Is optimized for AI language models
5. Follows the {strategy['structure']} structure

Make it professional, actionable, and tailored to the user's specific needs."""

        user_prompt = f"Create an effective AI prompt for: {topic}"
        
        # Use OpenAI to generate the prompt
        generated_prompt = openai_service.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.7
        )
        
        # Generate variations
        variations = []
        for i in range(3):
            variation_prompt = f"Create a variation of this prompt with a different approach: {generated_prompt}"
            variation = openai_service.generate_completion(
                system_prompt="You are a prompt engineering expert. Create variations of prompts with different approaches while maintaining effectiveness.",
                user_prompt=variation_prompt,
                max_tokens=400,
                temperature=0.8
            )
            variations.append(variation)
        
        return {
            "generated_prompt": generated_prompt,
            "usage_tips": strategy["tips"],
            "variations": variations,
            "strategy_used": strategy["structure"]
        }
        
    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        # Fallback to template-based generation
        return generate_template_prompt(prompt_type, topic, additional_context, tags)

def generate_template_prompt(prompt_type: str, topic: str, additional_context: str = "", tags: List[str] = []) -> Dict[str, Any]:
    """
    Fallback method using templates when AI generation fails
    """
    strategy = PROMPT_STRATEGIES.get(prompt_type, PROMPT_STRATEGIES["general"])
    
    # Build a comprehensive prompt using templates
    prompt_parts = []
    
    # Add context setting
    prompt_parts.append(f"You are an expert assistant helping with {topic}.")
    
    # Add specific instructions based on type
    if prompt_type == "content":
        prompt_parts.append(f"Create engaging, well-structured content about {topic}.")
    elif prompt_type == "technical":
        prompt_parts.append(f"Provide detailed, accurate technical information about {topic}.")
    elif prompt_type == "business":
        prompt_parts.append(f"Generate business-focused insights and strategies for {topic}.")
    elif prompt_type == "creative":
        prompt_parts.append(f"Use creativity and imagination to explore {topic}.")
    elif prompt_type == "marketing":
        prompt_parts.append(f"Create compelling marketing content for {topic}.")
    elif prompt_type == "academic":
        prompt_parts.append(f"Provide scholarly, research-based information about {topic}.")
    else:
        prompt_parts.append(f"Provide comprehensive, helpful information about {topic}.")
    
    # Add additional context
    if additional_context:
        prompt_parts.append(f"Additional requirements: {additional_context}")
    
    # Add tag-specific instructions
    tag_instructions = {
        "ai": "Focus on AI and machine learning aspects.",
        "writing": "Emphasize clear, engaging writing style.",
        "technical": "Include technical details and specifications.",
        "business": "Consider business implications and ROI."
    }
    
    for tag in tags:
        if tag in tag_instructions:
            prompt_parts.append(tag_instructions[tag])
    
    # Add output format instructions
    prompt_parts.append("Please provide a detailed, well-structured response.")
    
    generated_prompt = " ".join(prompt_parts)
    
    # Generate simple variations
    variations = [
        generated_prompt.replace("Please provide", "Can you give me"),
        generated_prompt.replace("detailed, well-structured", "comprehensive"),
        f"I need help with {topic}. {additional_context if additional_context else ''} Please provide specific guidance."
    ]
    
    return {
        "generated_prompt": generated_prompt,
        "usage_tips": strategy["tips"],
        "variations": variations[:3],
        "strategy_used": strategy["structure"]
    }

@router.post("/generate", response_model=PromptGenerationResponse)
async def generate_prompt(
    request: PromptGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate an AI-powered prompt based on user input.
    This is the core endpoint for the prompt generation feature.
    """
    try:
        logger.info(f"Generating prompt for user {current_user.id}: {request.topic}")
        
        # Validate input
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Topic is required")
        
        if request.prompt_type not in PROMPT_STRATEGIES:
            raise HTTPException(status_code=400, detail=f"Invalid prompt type. Must be one of: {list(PROMPT_STRATEGIES.keys())}")
        
        # Generate the prompt
        result = generate_intelligent_prompt(
            prompt_type=request.prompt_type,
            topic=request.topic,
            additional_context=request.additional_context or "",
            tags=request.tags
        )
        
        # Create response
        prompt_id = str(uuid.uuid4())
        response = PromptGenerationResponse(
            prompt_id=prompt_id,
            generated_prompt=result["generated_prompt"],
            prompt_type=request.prompt_type,
            topic=request.topic,
            tags=request.tags,
            usage_tips=result["usage_tips"],
            variations=result["variations"],
            created_at=datetime.utcnow().isoformat(),
            user_id=str(current_user.id)
        )
        
        logger.info(f"Successfully generated prompt {prompt_id} for user {current_user.id}")
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in generate_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate prompt")

@router.get("/templates")
async def get_prompt_templates(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available prompt templates and strategies.
    """
    try:
        templates = {}
        for prompt_type, strategy in PROMPT_STRATEGIES.items():
            templates[prompt_type] = {
                "name": prompt_type.title(),
                "description": strategy["template"].split(".")[0],
                "structure": strategy["structure"],
                "tips": strategy["tips"][:3]  # First 3 tips
            }
        
        return {
            "templates": templates,
            "available_types": list(PROMPT_STRATEGIES.keys()),
            "available_tags": ["ai", "writing", "technical", "business"]
        }
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get templates")

@router.post("/save")
async def save_prompt(
    prompt_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Save a generated prompt for later use.
    """
    try:
        # In a real implementation, this would save to database
        # For now, we'll return a success response
        prompt_id = prompt_data.get("prompt_id", str(uuid.uuid4()))
        
        saved_prompt = SavedPrompt(
            prompt_id=prompt_id,
            title=prompt_data.get("title", f"Prompt for {prompt_data.get('topic', 'Unknown')}"),
            generated_prompt=prompt_data.get("generated_prompt", ""),
            prompt_type=prompt_data.get("prompt_type", "general"),
            topic=prompt_data.get("topic", ""),
            tags=prompt_data.get("tags", []),
            created_at=datetime.utcnow().isoformat(),
            is_favorite=False
        )
        
        logger.info(f"Saved prompt {prompt_id} for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Prompt saved successfully",
            "prompt_id": prompt_id,
            "saved_prompt": saved_prompt.dict()
        }
        
    except Exception as e:
        logger.error(f"Error saving prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save prompt")

@router.get("/saved")
async def get_saved_prompts(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's saved prompts.
    """
    try:
        # In a real implementation, this would fetch from database
        # For now, return empty list with success message
        return {
            "saved_prompts": [],
            "total_count": 0,
            "message": "No saved prompts found. Generated prompts will appear here."
        }
        
    except Exception as e:
        logger.error(f"Error getting saved prompts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get saved prompts")

@router.delete("/saved/{prompt_id}")
async def delete_saved_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a saved prompt.
    """
    try:
        # In a real implementation, this would delete from database
        logger.info(f"Deleted prompt {prompt_id} for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Prompt deleted successfully",
            "prompt_id": prompt_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete prompt")

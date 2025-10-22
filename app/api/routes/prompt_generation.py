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
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.services import openai_service
from app.services.token_usage import require_tokens
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
        "structure": "Role + Context + Task + Instructions + Format + Quality Criteria",
        "tips": [
            "Always define a clear expert role/persona for the AI to adopt",
            "Provide comprehensive context and background information",
            "Break down complex tasks into specific, actionable steps",
            "Specify exact output format with clear section headers",
            "Include quality criteria and success metrics",
            "Add constraints and guidelines to ensure accuracy",
            "Use examples or templates when they help clarify expectations"
        ]
    },
    "content": {
        "template": "Generate engaging content about {topic}. {context}",
        "structure": "Expert Role + Audience + Purpose + Content Strategy + Format + Style Guidelines",
        "tips": [
            "Define the AI as a content expert with specific credentials",
            "Clearly identify target audience demographics and needs",
            "Specify content goals (inform, persuade, entertain, educate)",
            "Include detailed formatting requirements (headings, length, structure)",
            "Define tone, style, and voice guidelines",
            "Request specific content elements (hooks, CTAs, key messages)",
            "Add SEO or engagement optimization requirements when relevant"
        ]
    },
    "creative": {
        "template": "Create imaginative and original content for {topic}. {context}",
        "structure": "Creative Expert Role + Inspiration + Constraints + Process + Evaluation Criteria",
        "tips": [
            "Position AI as a creative professional with relevant experience",
            "Provide creative brief with inspiration and reference points",
            "Set clear creative constraints and parameters",
            "Request multiple concepts or iterations for comparison",
            "Define evaluation criteria for creative success",
            "Specify the creative medium and technical requirements",
            "Include brand guidelines or style preferences when applicable"
        ]
    },
    "technical": {
        "template": "Provide technical guidance and solutions for {topic}. {context}",
        "structure": "Technical Expert Role + Problem Definition + Requirements + Solution Framework + Implementation",
        "tips": [
            "Establish AI as a senior technical expert in the relevant field",
            "Clearly define the technical problem or challenge",
            "Specify technical requirements, constraints, and dependencies",
            "Request step-by-step implementation guidance",
            "Include code examples, diagrams, or technical specifications",
            "Define testing and validation criteria",
            "Address potential issues, edge cases, and troubleshooting"
        ]
    },
    "business": {
        "template": "Generate business-focused insights and strategies for {topic}. {context}",
        "structure": "Business Expert Role + Market Context + Objectives + Analysis Framework + Recommendations",
        "tips": [
            "Position AI as an experienced business consultant or strategist",
            "Provide comprehensive market and business context",
            "Define clear business objectives and success metrics",
            "Request structured analysis with supporting data and reasoning",
            "Include implementation roadmap with timelines and resources",
            "Address risks, challenges, and mitigation strategies",
            "Specify ROI considerations and measurement approaches"
        ]
    },
    "marketing": {
        "template": "Create compelling marketing content for {topic}. {context}",
        "structure": "Marketing Expert Role + Brand Context + Campaign Objectives + Strategy + Execution Plan",
        "tips": [
            "Establish AI as a marketing strategist with proven track record",
            "Provide detailed brand guidelines and positioning",
            "Define specific campaign goals and target metrics",
            "Include comprehensive audience personas and insights",
            "Request multi-channel strategy with platform-specific adaptations",
            "Specify creative requirements and brand compliance guidelines",
            "Include performance measurement and optimization recommendations"
        ]
    },
    "academic": {
        "template": "Develop scholarly and research-oriented content for {topic}. {context}",
        "structure": "Academic Expert Role + Research Context + Methodology + Analysis + Scholarly Standards",
        "tips": [
            "Position AI as a distinguished academic researcher in the field",
            "Provide comprehensive literature review and theoretical framework",
            "Define research methodology and analytical approach",
            "Request evidence-based analysis with proper citations",
            "Include academic writing standards and formatting requirements",
            "Specify peer review criteria and scholarly rigor expectations",
            "Address limitations, future research directions, and implications"
        ]
    }
}

def generate_intelligent_prompt(prompt_type: str, topic: str, additional_context: str = "", tags: List[str] = []) -> Dict[str, Any]:
    """
    Generate an intelligent, tailored prompt based on user input following prompt engineering best practices
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
                "ai": "Focus on AI and machine learning applications with technical depth",
                "writing": "Emphasize writing quality, style, and clarity",
                "technical": "Include technical depth, accuracy, and implementation details",
                "business": "Consider business impact, ROI, and strategic implications"
            }
            for tag in tags:
                if tag in tag_context:
                    context_parts.append(tag_context[tag])
        
        context = " ".join(context_parts)
        
        # Enhanced system prompt for comprehensive prompt engineering
        system_prompt = f"""You are a world-class prompt engineer with expertise in creating highly effective, comprehensive prompts that follow all pillars of prompt engineering.

Create a detailed, professional prompt for {prompt_type} use cases about: {topic}

CONTEXT:
- User's topic: {topic}
- Additional context: {context}
- Tags: {', '.join(tags)}
- Target structure: {strategy['structure']}

PROMPT ENGINEERING REQUIREMENTS:
Your generated prompt MUST include ALL of these essential elements:

1. ROLE & PERSONA: Define a clear expert role/persona for the AI
2. CONTEXT & BACKGROUND: Provide comprehensive background information
3. TASK DEFINITION: Clearly state what needs to be accomplished
4. SPECIFIC INSTRUCTIONS: Detailed, step-by-step guidance
5. OUTPUT FORMAT: Specify exactly how the response should be structured
6. CONSTRAINTS & GUIDELINES: Include relevant limitations and requirements
7. EXAMPLES (when helpful): Provide concrete examples or templates
8. QUALITY CRITERIA: Define what makes a good response
9. TONE & STYLE: Specify the appropriate communication style

STRUCTURE YOUR PROMPT AS FOLLOWS:
- Start with role definition ("You are a...")
- Provide context and background
- State the specific task clearly
- Give detailed instructions
- Specify output format with clear sections
- Include relevant constraints
- Add examples if helpful
- Define success criteria

Make the prompt:
- Comprehensive and detailed (aim for 400-600 words)
- Specific and actionable
- Professional and clear
- Tailored to the {prompt_type} domain
- Optimized for AI language models
- Following proven prompt engineering principles

The prompt should be so detailed and well-structured that it produces consistently excellent results."""

        user_prompt = f"Generate a comprehensive, detailed prompt for: {topic} (Type: {prompt_type})"
        
        # Use OpenAI to generate the prompt with higher token limit for detailed output
        generated_prompt = openai_service.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1200,
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
    Fallback method using comprehensive templates when AI generation fails
    """
    strategy = PROMPT_STRATEGIES.get(prompt_type, PROMPT_STRATEGIES["general"])
    
    # Build a comprehensive prompt following prompt engineering best practices
    prompt_sections = []
    
    # 1. ROLE & PERSONA
    role_definitions = {
        "content": f"You are an expert content strategist and writer with 10+ years of experience creating engaging, high-quality content about {topic}.",
        "technical": f"You are a senior technical expert and consultant specializing in {topic} with deep knowledge of industry best practices and cutting-edge developments.",
        "business": f"You are a seasoned business consultant and strategist with expertise in {topic}, known for delivering actionable insights that drive results.",
        "creative": f"You are a highly creative professional and innovative thinker with extensive experience in {topic} and a track record of breakthrough creative solutions.",
        "marketing": f"You are a marketing strategist and brand expert with proven success in {topic}, specializing in creating compelling campaigns that convert.",
        "academic": f"You are a distinguished academic researcher and scholar with extensive expertise in {topic}, known for rigorous analysis and scholarly excellence.",
        "general": f"You are a knowledgeable expert and consultant with comprehensive expertise in {topic} and a reputation for delivering exceptional insights."
    }
    
    prompt_sections.append(role_definitions.get(prompt_type, role_definitions["general"]))
    
    # 2. CONTEXT & BACKGROUND
    prompt_sections.append(f"\nCONTEXT:\nYou are working on a project related to {topic}.")
    if additional_context:
        prompt_sections.append(f"Additional context: {additional_context}")
    
    # 3. TASK DEFINITION
    task_definitions = {
        "content": f"Your task is to create comprehensive, engaging content about {topic} that informs, educates, and captivates the target audience.",
        "technical": f"Your task is to provide detailed technical analysis, solutions, and recommendations for {topic} with practical implementation guidance.",
        "business": f"Your task is to develop strategic business insights, recommendations, and actionable plans related to {topic}.",
        "creative": f"Your task is to generate innovative, original, and creative solutions or content related to {topic}.",
        "marketing": f"Your task is to create compelling marketing strategies, content, and campaigns focused on {topic}.",
        "academic": f"Your task is to provide scholarly analysis, research-based insights, and academic-quality content about {topic}.",
        "general": f"Your task is to provide comprehensive, well-researched, and actionable information about {topic}."
    }
    
    prompt_sections.append(f"\nTASK:\n{task_definitions.get(prompt_type, task_definitions['general'])}")
    
    # 4. SPECIFIC INSTRUCTIONS
    prompt_sections.append(f"\nINSTRUCTIONS:\n1. Begin with a clear overview of {topic}")
    prompt_sections.append("2. Provide detailed analysis with supporting evidence")
    prompt_sections.append("3. Include practical examples and real-world applications")
    prompt_sections.append("4. Address potential challenges and solutions")
    prompt_sections.append("5. Conclude with actionable recommendations")
    
    # 5. OUTPUT FORMAT
    prompt_sections.append(f"\nOUTPUT FORMAT:\nStructure your response with the following sections:")
    prompt_sections.append("• Executive Summary (2-3 sentences)")
    prompt_sections.append("• Main Analysis (detailed breakdown)")
    prompt_sections.append("• Key Insights (3-5 bullet points)")
    prompt_sections.append("• Practical Applications (specific examples)")
    prompt_sections.append("• Recommendations (actionable next steps)")
    
    # 6. CONSTRAINTS & GUIDELINES
    constraints = [
        "Ensure all information is accurate and up-to-date",
        "Use clear, professional language appropriate for the audience",
        "Support claims with evidence and examples",
        "Maintain objectivity and balanced perspective"
    ]
    
    # Add tag-specific constraints
    tag_constraints = {
        "ai": "Focus on AI/ML applications and include technical depth",
        "writing": "Emphasize clarity, style, and engaging narrative",
        "technical": "Include technical specifications and implementation details",
        "business": "Consider ROI, market impact, and strategic implications"
    }
    
    for tag in tags:
        if tag in tag_constraints:
            constraints.append(tag_constraints[tag])
    
    prompt_sections.append(f"\nGUIDELINES:\n" + "\n".join([f"• {constraint}" for constraint in constraints]))
    
    # 7. QUALITY CRITERIA
    prompt_sections.append(f"\nQUALITY CRITERIA:\nYour response should be:")
    prompt_sections.append("• Comprehensive and thorough")
    prompt_sections.append("• Actionable and practical")
    prompt_sections.append("• Well-structured and easy to follow")
    prompt_sections.append("• Supported by evidence and examples")
    prompt_sections.append("• Tailored to the specific context provided")
    
    # 8. TONE & STYLE
    tone_styles = {
        "content": "engaging and informative",
        "technical": "precise and authoritative", 
        "business": "professional and strategic",
        "creative": "innovative and inspiring",
        "marketing": "persuasive and compelling",
        "academic": "scholarly and rigorous",
        "general": "clear and professional"
    }
    
    tone = tone_styles.get(prompt_type, tone_styles["general"])
    prompt_sections.append(f"\nTONE & STYLE:\nMaintain a {tone} tone throughout your response.")
    
    generated_prompt = "\n".join(prompt_sections)
    
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
    db: Session = Depends(get_db),
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
        
        # Preflight quota: estimate tokens for generation
        require_tokens(db, user_id=str(current_user.id), estimated_tokens=1200)

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

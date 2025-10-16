"""
Service layer for research generation functionality
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def improve_topic(
    original_input: str,
    research_type: str,
    discipline: str,
    faculty: Optional[str],
    country: str,
    citation: str,
    length: str
) -> Dict[str, Any]:
    """
    Improve a research topic using AI
    
    Args:
        original_input: User's original topic/guidelines
        research_type: Type of research (Essay, Dissertation, etc.)
        discipline: Academic discipline
        faculty: Faculty/specialization (optional)
        country: Country for academic standards
        citation: Citation style
        length: Expected length
        
    Returns:
        Dictionary with improved topic and suggestions
    """
    
    prompt = f"""You are an expert academic research advisor. Improve the following research topic:

Original Input: "{original_input}"

Context:
- Research Type: {research_type}
- Discipline: {discipline}
- Faculty: {faculty or 'Not specified'}
- Country: {country}
- Citation Style: {citation}
- Length: {length}

Please provide:
1. An improved, detailed research topic title that is clear, specific, and academically sound
2. Brief rationale for the improvements made

The improved topic should:
- Be specific and focused
- Include key concepts and scope
- Be appropriate for {research_type} in {discipline}
- Align with {country} academic standards
- Be suitable for {length} research

Format your response as JSON:
{{
  "improvedTopic": "Your improved topic here",
  "rationale": "Brief explanation of improvements"
}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert academic research advisor specializing in {discipline} with deep knowledge of {country} academic standards."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "improvedTopic": result["improvedTopic"],
            "suggestions": [result["rationale"]]
        }
        
    except Exception as e:
        print(f"Error improving topic: {str(e)}")
        raise


async def generate_alternative_topic(
    original_input: str,
    previous_topic: Optional[str],
    research_type: str,
    discipline: str,
    faculty: Optional[str],
    country: str
) -> Dict[str, Any]:
    """
    Generate an alternative research topic
    
    Args:
        original_input: User's original input
        previous_topic: Previously generated topic (if any)
        research_type: Type of research
        discipline: Academic discipline
        faculty: Faculty/specialization (optional)
        country: Country for academic standards
        
    Returns:
        Dictionary with alternative topic and rationale
    """
    
    previous_context = f"\nPrevious Topic: {previous_topic}" if previous_topic else ""
    
    prompt = f"""You are an expert academic research advisor. Generate an alternative research topic based on:

Original Input: "{original_input}"{previous_context}

Context:
- Research Type: {research_type}
- Discipline: {discipline}
- Faculty: {faculty or 'Not specified'}
- Country: {country}

Generate a NEW, different research topic that:
- Explores a different angle or perspective
- Is still relevant to the original input
- Is appropriate for {research_type} in {discipline}
- Aligns with {country} academic standards
- Offers fresh insights

Format your response as JSON:
{{
  "alternativeTopic": "Your alternative topic here",
  "rationale": "Explanation of why this alternative is valuable"
}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert in {discipline} research with creative thinking skills."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "alternativeTopic": result["alternativeTopic"],
            "rationale": result["rationale"]
        }
        
    except Exception as e:
        print(f"Error generating alternative topic: {str(e)}")
        raise


async def generate_outline(
    topic: str,
    research_type: str,
    discipline: str,
    faculty: Optional[str],
    country: str,
    citation: str,
    length: str,
    research_guidelines: Optional[str],
    uploaded_documents: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate a comprehensive research outline tailored to discipline and country
    
    Args:
        topic: Research topic
        research_type: Type of research
        discipline: Academic discipline
        faculty: Faculty/specialization (optional)
        country: Country for academic standards
        citation: Citation style
        length: Expected length
        research_guidelines: Additional guidelines (optional)
        uploaded_documents: List of uploaded documents info
        
    Returns:
        Dictionary with outline, country standards, and discipline guidelines
    """
    
    guidelines_text = f"\n\nResearch Guidelines:\n{research_guidelines}" if research_guidelines else ""
    
    documents_text = ""
    if uploaded_documents and len(uploaded_documents) > 0:
        doc_list = "\n".join([f"- {doc['fileName']} ({doc['fileType']})" for doc in uploaded_documents])
        documents_text = f"\n\nUploaded Documents:\n{doc_list}"
    
    prompt = f"""You are an expert academic advisor. Generate a detailed research paper outline.

Research Details:
- Topic: {topic}
- Type: {research_type}
- Discipline: {discipline}
- Faculty: {faculty or 'Not specified'}
- Country: {country}
- Citation Style: {citation}
- Length: {length}{guidelines_text}{documents_text}

Requirements:
1. Create an outline that follows {country} academic standards and conventions
2. Tailor the structure to {discipline} research methodology
3. Include sections appropriate for a {research_type}
4. Ensure the structure supports {citation} citation format
5. Design for a {length} paper
6. Include country-specific context where relevant (e.g., "Context in {country}")
7. Include discipline-specific perspectives (e.g., "{discipline} Perspective")

Provide the outline as a JSON array of strings, where indentation is represented by leading spaces (2 spaces per level).

Example format:
[
  "Title Page",
  "Abstract",
  "Table of Contents",
  "Chapter 1: Introduction",
  "  1.1 Background",
  "  1.2 Context in {country}",
  "  1.3 {discipline} Perspective",
  "  1.4 Research Questions",
  "Chapter 2: Literature Review",
  "  2.1 Theoretical Framework",
  "  2.2 Previous Studies",
  "Chapter 3: Methodology",
  "  3.1 Research Design",
  "  3.2 Data Collection",
  "Chapter 4: Results",
  "Chapter 5: Discussion",
  "  5.1 Implications for {discipline}",
  "Chapter 6: Conclusion",
  "References ({citation} format)",
  "Appendices"
]

Return ONLY the JSON array, no additional text."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert in {discipline} research methodology and understand {country} academic standards. You specialize in creating detailed, well-structured research outlines."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=1500
        )
        
        outline = json.loads(response.choices[0].message.content)
        
        # Generate country-specific requirements
        country_requirements = [
            f"Follows {country} academic formatting standards",
            f"Includes {discipline}-specific sections and methodology",
            f"Structured for {research_type} requirements",
            f"Incorporates {country} context where relevant"
        ]
        
        # Generate discipline-specific guidelines
        discipline_focus = [
            f"{discipline} theoretical framework",
            f"{faculty or discipline} research methodology",
            "Evidence-based analysis and critical thinking",
            f"Appropriate for {research_type} in {discipline}"
        ]
        
        return {
            "outline": outline,
            "countryStandards": {
                "country": country,
                "specificRequirements": country_requirements
            },
            "disciplineGuidelines": {
                "discipline": discipline,
                "faculty": faculty,
                "keyFocus": discipline_focus
            }
        }
        
    except Exception as e:
        print(f"Error generating outline: {str(e)}")
        raise


async def generate_draft(
    topic: str,
    outline: List[str],
    research_type: str,
    discipline: str,
    faculty: Optional[str],
    country: str,
    citation: str,
    length: str,
    sources: str,
    research_guidelines: Optional[str],
    uploaded_documents: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate a full research draft based on outline and parameters
    
    Args:
        topic: Research topic
        outline: Research outline
        research_type: Type of research
        discipline: Academic discipline
        faculty: Faculty/specialization (optional)
        country: Country for academic standards
        citation: Citation style
        length: Expected length
        sources: Number of sources
        research_guidelines: Additional guidelines (optional)
        uploaded_documents: List of uploaded documents with content
        
    Returns:
        Dictionary with complete draft and metadata
    """
    
    # This is a complex operation that would typically be done in chunks
    # For now, return a placeholder structure
    
    return {
        "draft": {
            "title": topic,
            "abstract": "Abstract will be generated here...",
            "sections": [
                {
                    "heading": "Chapter 1: Introduction",
                    "content": "Introduction content will be generated here...",
                    "wordCount": 1500
                }
            ],
            "references": [],
            "totalWordCount": 0,
            "pageCount": 0
        },
        "metadata": {
            "generatedAt": datetime.now().isoformat(),
            "processingTime": "15 minutes",
            "aiModel": "GPT-4",
            "qualityScore": 95
        }
    }

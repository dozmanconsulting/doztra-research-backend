"""
Improved prompt for content generation to ensure topic-specific content.
"""

def get_improved_prompt(section_title, project_title, project_type_readable, 
                       section_specific_guidance, academic_level, target_audience,
                       research_methodology, discipline, country, keywords, context):
    """
    Generate an improved prompt that ensures content is specific to the project topic.
    """
    # Determine if this is a technical/software project
    is_software_project = any(kw in project_title.lower() for kw in [
        'software', 'system', 'application', 'app', 'platform', 'tool', 
        'ai', 'ml', 'algorithm', 'framework', 'database', 'interface', 
        'api', 'web', 'mobile', 'cloud', 'service', 'question-answering',
        'assistant', 'automation'
    ])
    
    prompt = f"""
    Generate detailed, specific content for the "{section_title}" section of a {project_type_readable} titled "{project_title}".
    
    IMPORTANT: This content MUST be specifically about the exact topic in the title "{project_title}". 
    DO NOT generate generic content about academic writing or research methodologies unless that is explicitly the topic of the project.
    
    {section_specific_guidance}
    
    Project details:
    - Title: "{project_title}"
    - Type: {project_type_readable}
    {f"- Academic Level: {academic_level}" if academic_level else ""}
    {f"- Target Audience: {target_audience}" if target_audience else ""}
    {f"- Research Methodology: {research_methodology}" if research_methodology else ""}
    {f"- Discipline: {discipline}" if discipline else ""}
    {f"- Country/Region Focus: {country}" if country else ""}
    {f"- Keywords: {', '.join(keywords)}" if keywords else ""}
    
    The content must be:
    1. DIRECTLY FOCUSED on the specific project title "{project_title}" - do not deviate from this topic
    2. Written at a distinction level academic standard appropriate for {academic_level or 'graduate'} level
    3. Include specific technical details, examples, and applications relevant to the exact project topic
    4. Well-structured with clear subsections and logical flow
    5. Include domain-specific examples and use cases that are directly relevant to the project title
    6. Include placeholders for citations where appropriate, formatted as [Author, Year]
    7. Formatted in markdown with proper headings, lists, and emphasis
    8. Tailored specifically for {target_audience or 'academic'} audience
    9. Using appropriate technical language and terminology specific to the project's domain
    
    Additional context from the user:
    {context if context else "No additional context provided."}
    
    {"If the project involves software, systems, or technical components, focus on technical specifications, architecture, implementation details, and relevant technologies." if is_software_project else ""}
    
    CRITICAL: The content MUST be about "{project_title}" and not generic academic content. Every paragraph should directly relate to the specific project topic.
    
    Create comprehensive, detailed content that appears to be written by an expert in the specific field of the project.
    """
    
    return prompt

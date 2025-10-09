#!/usr/bin/env python3
"""
Script to fix the prompt in openai_service.py to ensure content is specific to the project topic.
"""
import re

# Path to the file
file_path = 'app/services/openai_service.py'

# Read the file
with open(file_path, 'r') as file:
    content = file.read()

# Define the old and new prompt patterns
old_prompt_pattern = r'prompt = f""".*?Generate detailed, specific content for the.*?Create comprehensive, detailed content that appears to be written by an expert in the field\..*?"""'
new_prompt = '''prompt = f"""
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
        
        CRITICAL: The content MUST be about "{project_title}" and not generic academic content. Every paragraph should directly relate to the specific project topic.
        
        Create comprehensive, detailed content that appears to be written by an expert in the specific field of the project.
        """'''

# Add software detection code before the prompt
software_detection_code = '''        # Determine if this is a technical/software project
        is_software_project = any(kw in project_title.lower() for kw in [
            'software', 'system', 'application', 'app', 'platform', 'tool', 
            'ai', 'ml', 'algorithm', 'framework', 'database', 'interface', 
            'api', 'web', 'mobile', 'cloud', 'service', 'question-answering',
            'assistant', 'automation'
        ])
        
        # Log the project focus detection
        logger.info(f"Project title: '{project_title}' - Detected as software project: {is_software_project}")
        '''

# Find the position to insert the software detection code
section_guidance_pattern = r'# Get section-specific guidance\n\s+section_specific_guidance = get_section_guidance\(section_title, research_methodology\)'
match = re.search(section_guidance_pattern, content)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + '\n' + software_detection_code + content[insert_pos:]

# Replace the prompt
content = re.sub(old_prompt_pattern, new_prompt, content, flags=re.DOTALL)

# Add software-specific instruction to the prompt
software_instruction = '''        {'If the project involves software, systems, or technical components, focus on technical specifications, architecture, implementation details, and relevant technologies.' if is_software_project else ''}
        '''
additional_context_pattern = r'Additional context from the user:.*?{context if context else "No additional context provided\."}'
match = re.search(additional_context_pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + '\n' + software_instruction + content[insert_pos:]

# Write the modified content back to the file
with open(file_path, 'w') as file:
    file.write(content)

print("Successfully updated the prompt in openai_service.py")

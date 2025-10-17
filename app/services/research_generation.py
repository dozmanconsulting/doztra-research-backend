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
6. Include country-specific sections where relevant (e.g., "{country} Landscape", "Industry Overview in {country}", or "{country} Perspective")
7. Include discipline-specific perspectives (e.g., "{discipline} Perspective")

Provide the outline as a JSON array of strings, where indentation is represented by leading spaces (2 spaces per level).

Example format:
[
  "Title Page",
  "Abstract",
  "Table of Contents",
  "Chapter 1: Introduction",
  "  1.1 Background",
  "  1.2 {country} Landscape",
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
    selected_sources: List[Dict[str, Any]],
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
    
    start_time = datetime.now()
    
    # Prepare context from uploaded documents
    documents_context = ""
    if uploaded_documents and len(uploaded_documents) > 0:
        docs_list = []
        for doc in uploaded_documents:
            if doc.get('content'):
                docs_list.append(f"Document: {doc['fileName']}\n{doc['content'][:1000]}...")
        if docs_list:
            documents_context = f"\n\nReference Documents:\n" + "\n\n".join(docs_list)
    
    guidelines_text = f"\n\nResearch Guidelines:\n{research_guidelines}" if research_guidelines else ""
    
    # Format outline for prompt
    outline_text = "\n".join(outline)
    
    # Format selected sources for prompt
    sources_text = ""
    if selected_sources and len(selected_sources) > 0:
        sources_list = []
        for source in selected_sources:
            authors_str = ", ".join(source['authors'])
            source_entry = f"[{source['citationKey']}] {authors_str} ({source['year']}). {source['title']}. {source['publication']}."
            if source.get('doi'):
                source_entry += f" DOI: {source['doi']}"
            sources_list.append(source_entry)
        sources_text = "\n\nSelected Academic Sources (USE THESE FOR CITATIONS):\n" + "\n".join(sources_list)
        sources_text += f"\n\nIMPORTANT: Use these exact sources for your in-text citations. Cite them using their citation keys (e.g., {selected_sources[0]['citationKey']}, {source['year']}) in {citation} format."
    
    prompt = f"""WRITE THE COMPLETE ACADEMIC PAPER NOW. Do not write any disclaimers, explanations, or meta-commentary. Start directly with the title.

Research Details:
- Topic: {topic}
- Type: {research_type}
- Discipline: {discipline}
- Faculty: {faculty or 'Not specified'}
- Country: {country}
- Citation Style: {citation}
- Length: {length}
- Required Sources: {sources}{guidelines_text}{documents_context}{sources_text}

Outline to Follow:
{outline_text}

MANDATORY REQUIREMENTS - NO EXCEPTIONS:
1. START IMMEDIATELY with "# [Title]" - NO introductory text, NO disclaimers, NO explanations
2. Write the COMPLETE academic paper following the outline
3. Include proper {citation} in-text citations using the PROVIDED sources
4. Follow {country} academic writing standards
5. Use {discipline}-appropriate methodology and terminology
6. Write in formal academic tone for {research_type}
7. Each section must be substantive and well-developed
8. Aim for {length} in total length
9. **CRITICAL**: End with a "## References" section containing ACTUAL FORMATTED REFERENCES in {citation} format
   - DO NOT write "[Proper references would be listed here]" or any placeholder text
   - DO NOT write "based on the citation keys provided" or similar meta-commentary
   - WRITE THE ACTUAL FULL REFERENCES for each source you cited
   - Format each reference properly in {citation} style with authors, year, title, publication, etc.

CRITICAL: Your response must begin with "# " followed by the paper title. Nothing else. No disclaimers. No explanations. Just the paper.
The References section must contain actual formatted references, not placeholder text.

START WRITING THE PAPER NOW:"""

    try:
        # Note: GPT-4 Turbo Preview has a max output of 4096 tokens (~3000 words)
        # For longer papers, consider:
        # - Using "gpt-4o" or "gpt-4o-mini" (supports up to 16k output tokens)
        # - Generating sections separately and combining them
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert academic writer. You write complete academic papers immediately without any disclaimers, explanations, or meta-commentary. You NEVER mention platform constraints, limitations, or inability to complete tasks. You start every response with the paper title using markdown format. You write the full paper as requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096  # Maximum for GPT-4 Turbo Preview model
        )
        
        draft_content = response.choices[0].message.content
        
        # Post-process to remove any disclaimers that GPT might have added
        # Look for common disclaimer patterns at the start
        disclaimer_patterns = [
            "Due to the constraints of this platform",
            "I cannot generate a full",
            "I am unable to generate",
            "However, I can provide",
            "I can help you with creating an outline",
            "Let me know how I can assist you further"
        ]
        
        # Check if content starts with a disclaimer
        for pattern in disclaimer_patterns:
            if pattern.lower() in draft_content[:500].lower():
                # Find where the actual content starts (usually after "---" or first heading)
                lines = draft_content.split('\n')
                start_index = 0
                for i, line in enumerate(lines):
                    # Look for the first markdown heading or "---"
                    if line.strip().startswith('#') or line.strip() == '---':
                        start_index = i
                        break
                
                # Remove everything before the actual content
                if start_index > 0:
                    draft_content = '\n'.join(lines[start_index:])
                    print(f"Removed disclaimer from draft. Started content from line {start_index}")
                break
        
        # Check for placeholder references and replace with actual references if needed
        placeholder_ref_patterns = [
            "[Proper references",
            "would be listed here",
            "based on the citation keys",
            "[References formatted in"
        ]
        
        references_section_has_placeholder = False
        for pattern in placeholder_ref_patterns:
            if pattern.lower() in draft_content.lower():
                references_section_has_placeholder = True
                print(f"Warning: Detected placeholder reference text: '{pattern}'")
                break
        
        # If placeholder detected and we have selected sources, generate proper references
        if references_section_has_placeholder and selected_sources and len(selected_sources) > 0:
            print("Generating proper references from selected sources...")
            
            # Format references based on citation style
            formatted_refs = []
            for source in selected_sources:
                authors_str = ", ".join(source['authors'])
                if citation.lower() == 'apa 7' or citation.lower() == 'apa':
                    ref = f"{authors_str} ({source['year']}). {source['title']}. *{source['publication']}*."
                elif citation.lower() == 'mla 9' or citation.lower() == 'mla':
                    ref = f"{authors_str}. \"{source['title']}.\" *{source['publication']}*, {source['year']}."
                elif citation.lower() == 'chicago':
                    ref = f"{authors_str}. \"{source['title']}.\" *{source['publication']}* ({source['year']})."
                else:  # Harvard or default
                    ref = f"{authors_str} ({source['year']}) '{source['title']}', *{source['publication']}*."
                
                if source.get('doi'):
                    ref += f" https://doi.org/{source['doi']}"
                
                formatted_refs.append(ref)
            
            # Replace the References section
            if "## References" in draft_content or "## REFERENCES" in draft_content:
                # Find and replace the References section
                lines = draft_content.split('\n')
                ref_start_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().lower() == "## references":
                        ref_start_idx = i
                        break
                
                if ref_start_idx >= 0:
                    # Keep everything before References section and add new references
                    new_content = '\n'.join(lines[:ref_start_idx + 1])
                    new_content += "\n\n" + '\n\n'.join(formatted_refs)
                    draft_content = new_content
                    print(f"Replaced placeholder references with {len(formatted_refs)} actual references")
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Estimate word count (rough approximation)
        word_count = len(draft_content.split())
        page_count = word_count // 250  # Approximate pages (250 words per page)
        
        return {
            "draft": draft_content,
            "metadata": {
                "generatedAt": end_time.isoformat(),
                "processingTime": f"{processing_time:.1f} seconds",
                "aiModel": "GPT-4 Turbo",
                "wordCount": word_count,
                "pageCount": page_count,
                "citationStyle": citation,
                "discipline": discipline,
                "country": country
            }
        }
        
    except Exception as e:
        print(f"Error generating draft: {str(e)}")
        raise


async def generate_sources(
    topic: str,
    discipline: str,
    faculty: Optional[str],
    country: str,
    research_type: str,
    number_of_sources: str,
    research_guidelines: Optional[str]
) -> Dict[str, Any]:
    """
    Generate academic sources/references for a research topic
    
    Args:
        topic: Research topic
        discipline: Academic discipline
        faculty: Faculty/specialization (optional)
        country: Country for academic standards
        research_type: Type of research
        number_of_sources: Number of sources to generate
        research_guidelines: Additional guidelines (optional)
        
    Returns:
        Dictionary with list of academic sources
    """
    
    guidelines_text = f"\n\nResearch Guidelines:\n{research_guidelines}" if research_guidelines else ""
    
    # Parse number of sources
    source_count = 8  # default
    if "3-4" in number_of_sources:
        source_count = 4
    elif "4-7" in number_of_sources:
        source_count = 6
    elif "8-12" in number_of_sources:
        source_count = 10
    elif "12+" in number_of_sources:
        source_count = 15
    
    prompt = f"""You are an expert academic librarian. Generate {source_count} realistic academic sources for a research paper.

Research Details:
- Topic: {topic}
- Discipline: {discipline}
- Faculty: {faculty or 'Not specified'}
- Country: {country}
- Type: {research_type}{guidelines_text}

Requirements:
1. Generate {source_count} REALISTIC academic sources (journal articles, books, reports)
2. Sources should be from reputable publishers and journals in {discipline}
3. Include recent sources (last 5-10 years) and some seminal works
4. Each source should be directly relevant to the topic
5. Include proper metadata (authors, year, title, publication, DOI/URL)
6. Provide brief abstracts (2-3 sentences)
7. Explain relevance to the research topic
8. **MANDATORY**: Create short citation keys (e.g., "Smith2020", "JonesEtAl2019") - THIS FIELD IS REQUIRED

Return as a JSON object with this EXACT structure (ALL fields are required):
{{
  "sources": [
    {{
      "id": "unique-id-1",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2020,
      "title": "Article Title Here",
      "publication": "Journal of {discipline}",
      "doi": "10.1234/example.2020.001",
      "url": "https://doi.org/10.1234/example.2020.001",
      "abstract": "Brief abstract explaining the research...",
      "relevance": "This source is relevant because...",
      "citationKey": "SmithDoe2020"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON
- ALL fields must be present for each source
- citationKey is MANDATORY (format: AuthorYear or AuthorEtAlYear)
- No explanatory text, no markdown formatting, no code blocks"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert academic librarian. You ONLY respond with valid JSON arrays, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        sources_json = response.choices[0].message.content
        
        # Parse JSON response
        import json
        import re
        
        # Clean up the response - remove markdown code blocks if present
        cleaned_json = sources_json.strip()
        
        # Remove ```json and ``` markers if present
        if cleaned_json.startswith('```'):
            # Extract content between ``` markers
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_json, re.DOTALL)
            if match:
                cleaned_json = match.group(1)
            else:
                # Try to find just the object
                match = re.search(r'(\{.*\})', cleaned_json, re.DOTALL)
                if match:
                    cleaned_json = match.group(1)
        
        result = json.loads(cleaned_json)
        
        # Handle both array and object formats
        if isinstance(result, list):
            sources = result
        elif isinstance(result, dict) and "sources" in result:
            sources = result["sources"]
        else:
            raise ValueError("Unexpected JSON format from GPT-4")
        
        # Add citationKey if missing (fallback)
        for source in sources:
            if "citationKey" not in source or not source["citationKey"]:
                # Generate citation key from authors and year
                authors = source.get("authors", [])
                year = source.get("year", "")
                if authors and year:
                    first_author = authors[0].split(",")[0].strip()
                    if len(authors) > 2:
                        citation_key = f"{first_author}EtAl{year}"
                    elif len(authors) == 2:
                        second_author = authors[1].split(",")[0].strip()
                        citation_key = f"{first_author}{second_author}{year}"
                    else:
                        citation_key = f"{first_author}{year}"
                    source["citationKey"] = citation_key
                else:
                    source["citationKey"] = f"Source{source.get('id', 'Unknown')}"
        
        return {"sources": sources}
        
    except Exception as e:
        print(f"Error generating sources: {str(e)}")
        print(f"Raw response: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
        raise

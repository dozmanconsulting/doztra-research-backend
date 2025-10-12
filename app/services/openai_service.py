"""
Service for interacting with OpenAI API, document processing, and LLM interactions.
"""
from openai import AsyncOpenAI
from typing import Optional, List, Dict, Any, Tuple, Union
import logging
import os
import json
import base64
import asyncio
from datetime import datetime
import tempfile
import uuid
import httpx
from pathlib import Path

from app.core.config import settings

# Configure OpenAI API client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Configure logging
logger = logging.getLogger(__name__)


def get_openai_client():
    """Returns the configured OpenAI client instance"""
    return client

# Constants
MAX_CHUNK_SIZE = 8000  # Maximum tokens per chunk for context window
OVERLAP_SIZE = 200     # Overlap between chunks to maintain context
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI embedding model
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI embeddings


async def generate_research_content(
    section_title: str,
    project_title: str,
    project_type: str,
    context: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate detailed content for a specific section of a research project.
    
    Args:
        section_title: The title of the section to generate content for
        project_title: The title of the research project
        project_type: The type of research project (e.g., case_study, dissertation)
        context: Additional context or information about the project
        metadata: Additional metadata about the project (academic level, audience, etc.)
        
    Returns:
        str: Generated content for the section
    """
    try:
        # Convert project_type to a more readable format
        project_type_readable = project_type.replace('_', ' ').title()
        
        # Extract metadata fields if available
        metadata = metadata or {}
        logger.info(f"Received metadata for content generation: {metadata}")
        
        academic_level = metadata.get('academic_level', '')
        target_audience = metadata.get('target_audience', '')
        research_methodology = metadata.get('research_methodology', '')
        country = metadata.get('country', '')
        keywords = metadata.get('keywords', [])
        discipline = metadata.get('discipline', '')
        
        # Log extracted metadata fields
        logger.info(f"Extracted metadata fields for '{section_title}' section:")
        logger.info(f"  - Academic Level: {academic_level}")
        logger.info(f"  - Target Audience: {target_audience}")
        logger.info(f"  - Research Methodology: {research_methodology}")
        logger.info(f"  - Country: {country}")
        logger.info(f"  - Keywords: {keywords}")
        
        # Get section-specific guidance
        section_specific_guidance = get_section_guidance(section_title, research_methodology)
        # Determine if this is a technical/software project
        is_software_project = any(kw in project_title.lower() for kw in [
            'software', 'system', 'application', 'app', 'platform', 'tool', 
            'ai', 'ml', 'algorithm', 'framework', 'database', 'interface', 
            'api', 'web', 'mobile', 'cloud', 'service', 'question-answering',
            'assistant', 'automation'
        ])
        
        # Log the project focus detection
        logger.info(f"Project title: '{project_title}' - Detected as software project: {is_software_project}")
        
        
        # Build the prompt with enhanced context and specificity
        # Extract project title components to better understand the topic
        title_keywords = project_title.lower().split()
        
        # Determine if this is a technical/software project
        is_software_project = any(kw in project_title.lower() for kw in ['software', 'system', 'application', 'app', 'platform', 'tool', 'ai', 'ml', 'algorithm', 'framework', 'database', 'interface', 'api', 'web', 'mobile', 'cloud', 'service'])
        
        # Log the project focus detection
        logger.info(f"Project title: '{project_title}' - Detected as software project: {is_software_project}")
        
        # Build the prompt with enhanced context and specificity
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
        
        Additional context from the user:
        {context if context else "No additional context provided."}
        
        {'If the project involves software, systems, or technical components, focus on technical specifications, architecture, implementation details, and relevant technologies.' if is_software_project else ''}
        
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
        
        CRITICAL: The content MUST be about "{project_title}" and not generic academic content. Every paragraph should directly relate to the specific project topic.
        
        Create comprehensive, detailed content that appears to be written by an expert in the specific field of the project.
        """
        
        # Avoid generic placeholders like [Research Project] or [Variable A] - instead, use specific, plausible
        # examples related to the project title and focus.
        
        # Call OpenAI API with GPT-4
        response = await client.chat.completions.create(
            model=settings.LLM_REASONING,  # Now using GPT-4
            messages=[
                {"role": "system", "content": "You are an expert academic researcher and writer specializing in creating high-quality research content at a distinction level. Your expertise spans multiple disciplines and methodologies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,  # Increased token limit for more detailed content
            top_p=1.0,
            frequency_penalty=0.3,  # Added to reduce repetition
            presence_penalty=0.1    # Added to encourage diversity
        )
        
        # Extract and return the generated content
        content = response.choices[0].message.content.strip()
        return content
        
    except Exception as e:
        logger.error(f"Error generating research content: {str(e)}")
        raise Exception(f"Failed to generate content: {str(e)}")


def get_section_guidance(section_title: str, methodology: str = None) -> str:
    """
    Get enhanced guidance for specific section types with methodology considerations.
    
    Args:
        section_title: The title of the section
        methodology: The research methodology being used (if available)
        
    Returns:
        str: Specific guidance for the section type
    """
    section_title_lower = section_title.lower()
    
    # Enhanced section guidance that incorporates methodology if available
    if section_title_lower == "introduction" or "introduction" in section_title_lower or "background" in section_title_lower:
        return """
        For the Introduction/Background section:
        - Clearly establish the research problem and its significance in the field
        - Provide comprehensive background information with historical context
        - Present a clear thesis statement or research question
        - Outline the scope and limitations of the study
        - Preview the structure of the entire document
        - Establish the theoretical framework that guides the research
        - Highlight the originality and contribution of this work
        """
    elif "literature" in section_title_lower or "review" in section_title_lower or "previous work" in section_title_lower:
        return """
        For the Literature Review section:
        - Organize the review thematically, chronologically, or methodologically
        - Critically analyze key studies rather than just summarizing them
        - Identify patterns, gaps, and contradictions in existing research
        - Establish connections between different studies and perspectives
        - Evaluate the strengths and limitations of significant works
        - Demonstrate how your research addresses identified gaps
        - Use a balanced mix of seminal works and current research
        """
    elif "method" in section_title_lower or "approach" in section_title_lower:
        # Customize methodology guidance based on the specific methodology if available
        if methodology and "qualitative" in methodology.lower():
            return """
            For the Methodology section (Qualitative):
            - Justify the chosen qualitative research design and approach
            - Detail data collection methods (interviews, focus groups, observations, etc.)
            - Explain participant selection and recruitment strategies
            - Describe data analysis techniques (thematic analysis, grounded theory, etc.)
            - Address trustworthiness, credibility, and transferability
            - Discuss ethical considerations including consent and confidentiality
            - Acknowledge researcher positionality and potential biases
            """
        elif methodology and "quantitative" in methodology.lower():
            return """
            For the Methodology section (Quantitative):
            - Justify the chosen quantitative research design and approach
            - Detail sampling methods and sample size calculations
            - Describe variables, measures, and instruments with validity/reliability
            - Explain data collection procedures and protocols
            - Detail statistical analysis techniques and software used
            - Address validity, reliability, and generalizability
            - Discuss ethical considerations and approval processes
            """
        elif methodology and "mixed" in methodology.lower():
            return """
            For the Methodology section (Mixed Methods):
            - Justify the mixed methods approach and specific design (sequential, concurrent, etc.)
            - Explain how quantitative and qualitative components complement each other
            - Detail both quantitative and qualitative data collection methods
            - Describe integration points between methodologies
            - Explain data analysis for both components and integration strategy
            - Address validity/reliability and trustworthiness considerations
            - Discuss ethical considerations for all research components
            """
        else:
            return """
            For the Methodology section:
            - Justify the chosen research design and approach
            - Detail data collection methods, tools, and procedures
            - Explain sampling strategies and participant selection criteria
            - Describe analytical techniques with appropriate rigor
            - Address validity, reliability, and generalizability
            - Discuss ethical considerations and approval processes
            - Acknowledge methodological limitations and how they were addressed
            """
    elif "result" in section_title_lower or "finding" in section_title_lower:
        return """
        For the Results/Findings section:
        - Present findings clearly without interpretation
        - Organize results logically, aligned with research questions
        - Use tables, figures, or charts where appropriate (described in text)
        - Report statistical analyses with appropriate detail
        - Present qualitative findings with supporting evidence
        - Highlight key patterns and unexpected outcomes
        - Maintain objectivity throughout the presentation
        """
    elif "discussion" in section_title_lower or "analysis" in section_title_lower or "interpretation" in section_title_lower:
        return """
        For the Discussion/Analysis section:
        - Interpret results in relation to original research questions
        - Connect findings to existing literature and theoretical frameworks
        - Discuss implications of the results for theory and practice
        - Address unexpected findings and alternative explanations
        - Acknowledge limitations and their impact on interpretations
        - Suggest directions for future research
        - Avoid introducing new data not presented in results
        """
    elif "conclusion" in section_title_lower or "summary" in section_title_lower:
        return """
        For the Conclusion section:
        - Synthesize key findings without introducing new material
        - Restate the significance of the research and its contribution
        - Connect conclusions directly to the research questions/objectives
        - Discuss theoretical and practical implications
        - Address limitations of the study with balanced perspective
        - Suggest specific directions for future research
        - End with a compelling final statement on the research's value
        """
    elif "recommendation" in section_title_lower:
        return """
        For the Recommendations section:
        - Provide specific, actionable recommendations based on findings
        - Prioritize recommendations by importance or feasibility
        - Justify each recommendation with evidence from the research
        - Consider practical implementation challenges and solutions
        - Address different stakeholder perspectives and needs
        - Discuss resource implications and potential timelines
        - Include methods for evaluating the effectiveness of recommendations
        """
    elif "abstract" in section_title_lower or "executive summary" in section_title_lower:
        return """
        For the Abstract/Executive Summary section:
        - Provide a comprehensive yet concise overview of the entire work
        - Include problem statement, methodology, key findings, and conclusions
        - Highlight the significance and originality of the research
        - Maintain the word limit typical for this document type (150-350 words)
        - Avoid citations and abbreviations unless absolutely necessary
        - Ensure it can stand alone as a summary of the work
        - Use keywords relevant to the field for searchability
        """
    else:
        # Generic guidance for other section types
        return f"""
        For the {section_title} section:
        - Ensure this section serves its specific purpose within the overall document
        - Maintain logical flow and coherence with other sections
        - Use appropriate academic language and terminology
        - Include relevant examples, evidence, or data
        - Cite appropriate sources to support key points
        - Maintain focus on the research questions/objectives
        - Ensure appropriate depth and detail for this section
        """


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    model: str = None
) -> str:
    """
    Generate a completion using OpenAI API (synchronous version for prompt generation).
    
    Args:
        system_prompt: System message to set context
        user_prompt: User message/prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        model: Model to use (defaults to LLM_REASONING)
        
    Returns:
        str: Generated completion
    """
    try:
        # Use synchronous client for this function
        import openai
        sync_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Use provided model or default to reasoning model
        model_name = model or settings.LLM_REASONING
        
        response = sync_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1.0,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating completion: {str(e)}")
        raise Exception(f"Failed to generate completion: {str(e)}")


async def generate_chat_response(messages: List[Dict[str, Any]]) -> str:
    """
    Generate a response for chat messages.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        
    Returns:
        str: Generated response
    """
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_CONVERSATION,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating chat response: {str(e)}")
        raise Exception(f"Failed to generate response: {str(e)}")


async def extract_text_from_document(file_path: str, file_type: str) -> str:
    """
    Extract text content from a document file.
    
    Args:
        file_path: Path to the document file
        file_type: MIME type of the file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Extract text based on file type
        if file_type == "application/pdf":
            # Use PyPDF for PDF extraction
            import PyPDF2
            
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from each page
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                    
                return text
                
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Use python-docx for DOCX extraction
            import docx
            
            doc = docx.Document(file_path)
            text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
            
        elif file_type == "text/plain":
            # Simple text file
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
                
        elif file_type == "text/csv":
            # Use pandas for CSV
            import pandas as pd
            
            df = pd.read_csv(file_path)
            return df.to_string()
            
        elif file_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            # Use OpenAI's vision capabilities for images
            return await extract_text_from_image(file_path)
            
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
    except Exception as e:
        logger.error(f"Error extracting text from document: {str(e)}")
        raise Exception(f"Failed to extract text: {str(e)}")


async def extract_text_from_image(image_path: str) -> str:
    """
    Extract text and content description from an image using OpenAI's vision model.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Description and extracted text from the image
    """
    try:
        # Read image file and encode as base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Call OpenAI API with vision capabilities
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please describe this image in detail and extract any visible text. Format your response with 'Description:' followed by image content details, and 'Extracted Text:' followed by any text visible in the image."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        raise Exception(f"Failed to process image: {str(e)}")


async def chunk_document(text: str, metadata: Dict[str, Any] = None, chunk_size: int = None) -> List[Dict[str, Any]]:
    """
    Split a document into manageable chunks for processing.
    
    Args:
        text: The document text to chunk
        metadata: Additional metadata to include with each chunk
        chunk_size: Optional custom chunk size (defaults to MAX_CHUNK_SIZE)
        
    Returns:
        List[Dict[str, Any]]: List of chunks with text and metadata
    """
    try:
        # Simple chunking by paragraphs and size
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        # Use custom chunk size if provided, otherwise use default
        max_size = chunk_size if chunk_size is not None else MAX_CHUNK_SIZE
        
        for i, paragraph in enumerate(paragraphs):
            # If adding this paragraph would exceed max chunk size, save current chunk and start a new one
            if len(current_chunk) + len(paragraph) > max_size:
                if current_chunk:  # Don't add empty chunks
                    chunks.append({
                        "text": current_chunk,
                        "metadata": {
                            "chunk_index": len(chunks),
                            **(metadata or {})
                        }
                    })
                current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "metadata": {
                    "chunk_index": len(chunks),
                    **(metadata or {})
                }
            })
            
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking document: {str(e)}")
        raise Exception(f"Failed to chunk document: {str(e)}")


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks using OpenAI's embedding model.
    
    Args:
        texts: List of text chunks to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    try:
        # Process in batches to avoid rate limits
        embeddings = []
        batch_size = 20  # Adjust based on API limits
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Call OpenAI API to generate embeddings
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            
            # Extract embedding data
            batch_embeddings = [data.embedding for data in response.data]
            embeddings.extend(batch_embeddings)
            
            # Respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)
                
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise Exception(f"Failed to generate embeddings: {str(e)}")


async def process_document(file_path: str, file_type: str, document_id: str, user_id: str, metadata: Dict[str, Any] = None, chunk_size: int = None) -> Dict[str, Any]:
    """
    Process a document: extract text, chunk it, generate embeddings, and store in vector database.
    
    Args:
        file_path: Path to the document file
        file_type: MIME type of the file
        document_id: Unique ID for the document
        user_id: ID of the user who uploaded the document
        metadata: Additional metadata about the document
        chunk_size: Optional custom chunk size for document processing
        
    Returns:
        Dict[str, Any]: Processing results including chunk count and status
    """
    try:
        logger.info(f"Processing document: {file_path}, type: {file_type}, id: {document_id}")
        
        # Extract text from document
        logger.info(f"Extracting text from document: {file_path}")
        text = await extract_text_from_document(file_path, file_type)
        logger.info(f"Extracted {len(text)} characters of text")
        
        # Prepare document metadata
        logger.info(f"Preparing metadata with: {metadata}")
        doc_metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "file_type": file_type,
            "processed_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        logger.info(f"Final metadata: {doc_metadata}")
        
        # Chunk the document
        logger.info(f"Chunking document with size: {chunk_size if chunk_size else 'default'}")
        chunks = await chunk_document(text, doc_metadata, chunk_size)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Extract just the text for embedding
        logger.info("Extracting text for embeddings")
        chunk_texts = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_texts.append(chunk["text"])
            except Exception as e:
                logger.error(f"Error extracting text from chunk {i}: {str(e)}")
                logger.error(f"Chunk data: {chunk}")
                raise
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
        embeddings = await generate_embeddings(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Add embeddings to chunks
        logger.info("Adding embeddings to chunks")
        for i, embedding in enumerate(embeddings):
            try:
                chunks[i]["embedding"] = embedding
            except Exception as e:
                logger.error(f"Error adding embedding to chunk {i}: {str(e)}")
                logger.error(f"Chunk data: {chunks[i] if i < len(chunks) else 'index out of range'}")
                raise
        
        # Store in vector database (implementation depends on your vector DB choice)
        # This is a placeholder - replace with actual vector DB storage code
        await store_document_chunks(chunks, document_id, user_id)
        
        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "status": "processed",
            "text_length": len(text),
            "processed_at": doc_metadata["processed_at"]
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise Exception(f"Failed to process document: {str(e)}")


async def store_document_chunks(chunks: List[Dict[str, Any]], document_id: str, user_id: str) -> bool:
    """
    Store document chunks in a vector database.
    
    Args:
        chunks: List of document chunks with embeddings
        document_id: Unique ID for the document
        user_id: ID of the user who uploaded the document
        
    Returns:
        bool: True if storage was successful
    """
    # This is a placeholder - replace with your actual vector DB implementation
    # For example, using Pinecone, Weaviate, Milvus, or PostgreSQL with pgvector
    
    try:
        logger.info(f"Storing {len(chunks)} document chunks for document {document_id}")
        
        # Example using a hypothetical vector DB client
        # For actual implementation, replace with your chosen vector DB
        
        # Prepare records for batch insertion
        records = []
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Processing chunk {i} for storage")
                
                # Ensure metadata is a dictionary
                if isinstance(chunk.get('metadata'), dict):
                    chunk_index = chunk['metadata'].get('chunk_index', i)
                    logger.info(f"Using metadata chunk_index: {chunk_index}")
                else:
                    chunk_index = i
                    logger.info(f"Using default chunk_index: {i}, metadata type: {type(chunk.get('metadata'))}")
                    if chunk.get('metadata') is not None:
                        logger.info(f"Metadata value: {chunk.get('metadata')}")
                
                # Ensure text is present
                if 'text' not in chunk:
                    logger.error(f"Missing 'text' in chunk {i}: {chunk}")
                    raise KeyError(f"Missing 'text' in chunk {i}")
                    
                # Ensure embedding is present
                if 'embedding' not in chunk:
                    logger.error(f"Missing 'embedding' in chunk {i}: {chunk}")
                    raise KeyError(f"Missing 'embedding' in chunk {i}")
                
                records.append({
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "values": chunk["embedding"],
                    "metadata": chunk.get("metadata", {}),
                    "text": chunk["text"]
                })
                
            except Exception as e:
                logger.error(f"Error processing chunk {i} for storage: {str(e)}")
                logger.error(f"Chunk data: {chunk}")
                raise
        
        # Store in vector DB (placeholder)
        # vector_db_client.upsert(index_name="documents", namespace=user_id, vectors=records)
        
        # For now, just log that we would store these chunks
        logger.info(f"Would store {len(chunks)} chunks for document {document_id} in vector DB")
        
        # Also store in a local JSON file for testing purposes
        output_dir = Path("./document_chunks")
        output_dir.mkdir(exist_ok=True)
        
        # Remove embeddings to make the JSON file smaller
        logger.info("Creating simplified chunks for JSON storage")
        simplified_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Processing chunk {i} for JSON storage")
                
                # Ensure metadata is a dictionary
                if isinstance(chunk.get('metadata'), dict):
                    chunk_index = chunk['metadata'].get('chunk_index', i)
                    metadata = chunk['metadata']
                    logger.info(f"Using metadata from chunk: {chunk_index}")
                else:
                    chunk_index = i
                    metadata = {"chunk_index": i}
                    logger.info(f"Created default metadata for chunk {i}")
                
                # Ensure text is present
                if 'text' not in chunk:
                    logger.error(f"Missing 'text' in chunk {i} for JSON storage: {chunk}")
                    # Use a placeholder instead of failing
                    text = f"[Missing text for chunk {i}]"
                else:
                    text = chunk["text"]
                    
                # Get embedding size if available
                if "embedding" in chunk:
                    try:
                        embedding_size = len(chunk["embedding"])
                    except Exception as e:
                        logger.error(f"Error getting embedding size: {str(e)}")
                        embedding_size = 0
                else:
                    embedding_size = 0
                
                simplified_chunk = {
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "metadata": metadata,
                    "text": text,
                    "embedding_size": embedding_size
                }
                simplified_chunks.append(simplified_chunk)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i} for JSON storage: {str(e)}")
                logger.error(f"Chunk data: {chunk}")
                # Continue with other chunks instead of failing completely
                continue
        
        with open(output_dir / f"{document_id}_chunks.json", "w") as f:
            json.dump(simplified_chunks, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error storing document chunks: {str(e)}")
        raise Exception(f"Failed to store document chunks: {str(e)}")


async def search_document_chunks(query: str, user_id: str, document_ids: List[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant document chunks based on a query.
    
    Args:
        query: The search query
        user_id: ID of the user performing the search
        document_ids: Optional list of document IDs to restrict the search to
        top_k: Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of relevant chunks with similarity scores
    """
    try:
        # Generate embedding for the query
        query_embedding = await generate_embeddings([query])
        if not query_embedding or len(query_embedding) == 0:
            raise ValueError("Failed to generate query embedding")
            
        # This is a placeholder - replace with your actual vector DB search implementation
        # For example, using Pinecone, Weaviate, Milvus, or PostgreSQL with pgvector
        
        # For testing purposes, we'll simulate a search using local files
        results = []
        
        # Get all chunk files for the user
        output_dir = Path("./document_chunks")
        if not output_dir.exists():
            return []
            
        # Filter by document IDs if provided
        if document_ids:
            chunk_files = [output_dir / f"{doc_id}_chunks.json" for doc_id in document_ids if (output_dir / f"{doc_id}_chunks.json").exists()]
        else:
            chunk_files = list(output_dir.glob("*_chunks.json"))
            
        # Load chunks from files and simulate vector search
        all_chunks = []
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r") as f:
                    chunks = json.load(f)
                    all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Error loading chunks from {chunk_file}: {str(e)}")
                
        # For a real implementation, you would search the vector DB here
        # For this simulation, we'll just return some chunks with simulated scores
        for i, chunk in enumerate(all_chunks[:top_k]):
            # Simulate a relevance score (in a real implementation, this would be cosine similarity)
            score = 0.95 - (i * 0.05)  # Decreasing scores for demonstration
            
            results.append({
                "chunk_id": chunk["id"],
                "document_id": chunk["metadata"]["document_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": score
            })
            
        return results
        
    except Exception as e:
        logger.error(f"Error searching document chunks: {str(e)}")
        raise Exception(f"Failed to search documents: {str(e)}")


async def query_with_documents(query: str, user_id: str, document_ids: List[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Query the LLM with document context.
    
    Args:
        query: The user's query
        user_id: ID of the user making the query
        document_ids: Optional list of document IDs to use as context
        options: Additional options for the query (model, temperature, etc.)
        
    Returns:
        Dict[str, Any]: LLM response with citations and metadata
    """
    try:
        # Default options
        default_options = {
            "model": settings.LLM_REASONING,
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_k": 5  # Number of document chunks to retrieve
        }
        
        # Merge with user options
        query_options = {**default_options, **(options or {})}
        
        # Check if documents exist and are processed
        chunks_dir = Path("./document_chunks")
        for doc_id in document_ids or []:
            # First check if the document exists in the user's uploads
            user_dir = Path("./uploads") / user_id
            doc_dir = user_dir / doc_id
            
            if not doc_dir.exists():
                # Document doesn't exist
                return {
                    "answer": f"The document with ID {doc_id} was not found. Please check the document ID and try again.",
                    "sources": [],
                    "query": query,
                    "model": query_options["model"],
                    "error": "document_not_found"
                }
                
            # Now check if document is processed
            chunks_file = chunks_dir / f"{doc_id}_chunks.json"
            if not chunks_file.exists():
                # Document exists but is not processed yet
                return {
                    "answer": f"The document with ID {doc_id} is still being processed. Please try again in a few moments.",
                    "sources": [],
                    "query": query,
                    "model": query_options["model"],
                    "processing_status": "pending"
                }
        
        # Search for relevant document chunks
        relevant_chunks = await search_document_chunks(
            query=query,
            user_id=user_id,
            document_ids=document_ids,
            top_k=query_options["top_k"]
        )
        
        if not relevant_chunks:
            # No relevant documents found, fall back to standard chat
            return await generate_standard_response(query, query_options)
            
        # Prepare context from chunks
        context = ""
        for i, chunk in enumerate(relevant_chunks):
            context += f"\n\nDocument {i+1} (ID: {chunk['document_id']}):\n{chunk['text']}"
            
        # Build prompt with document context
        system_message = """
        You are a helpful AI assistant with access to document context. 
        Answer the user's question based on the provided document context. 
        If the context doesn't contain relevant information, say so clearly.
        
        When referencing information from the documents, cite the source using [Document X] format.
        Be precise, accurate, and helpful.
        """
        
        user_message = f"""Question: {query}
        
        Document Context:
        {context}
        
        Please provide a comprehensive answer based on the document context. Include citations to specific documents."""
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=query_options["model"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=query_options["temperature"],
            max_tokens=query_options["max_tokens"]
        )
        
        # Extract response
        answer = response.choices[0].message.content.strip()
        
        # Return response with metadata
        return {
            "answer": answer,
            "sources": [
                {
                    "document_id": chunk["document_id"],
                    "chunk_id": chunk["chunk_id"],
                    "score": chunk["score"],
                    "metadata": chunk["metadata"]
                } for chunk in relevant_chunks
            ],
            "query": query,
            "model": query_options["model"]
        }
        
    except Exception as e:
        logger.error(f"Error querying with documents: {str(e)}")
        raise Exception(f"Failed to query with documents: {str(e)}")


async def generate_standard_response(query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate a standard response without document context.
    
    Args:
        query: The user's query
        options: Additional options for the query (model, temperature, etc.)
        
    Returns:
        Dict[str, Any]: LLM response
    """
    try:
        # Default options
        default_options = {
            "model": settings.LLM_CONVERSATION,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Merge with user options
        query_options = {**default_options, **(options or {})}
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=query_options["model"],
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": query}
            ],
            temperature=query_options["temperature"],
            max_tokens=query_options["max_tokens"]
        )
        
        # Extract response
        answer = response.choices[0].message.content.strip()
        
        # Return response with metadata
        return {
            "answer": answer,
            "sources": [],  # No document sources
            "query": query,
            "model": query_options["model"]
        }
        
    except Exception as e:
        logger.error(f"Error generating standard response: {str(e)}")
        raise Exception(f"Failed to generate response: {str(e)}")


async def analyze_document(document_id: str, user_id: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Generate analysis for a document (summary, key points, etc.).
    
    Args:
        document_id: ID of the document to analyze
        user_id: ID of the user requesting analysis
        analysis_type: Type of analysis to perform (summary, key_points, topics, etc.)
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    try:
        # Check if document is processed
        chunks_dir = Path("./document_chunks")
        chunks_file = chunks_dir / f"{document_id}_chunks.json"
        
        if not chunks_file.exists():
            # Document is not processed yet
            return {
                "document_id": document_id,
                "analysis_type": analysis_type,
                "analysis": "This document is still being processed. Please try again in a few moments.",
                "processing_status": "pending",
                "timestamp": datetime.now().isoformat()
            }
            
        # Get document chunks
        chunks = await get_document_chunks(document_id, user_id)
        if not chunks:
            raise ValueError(f"No chunks found for document {document_id}")
            
        # Combine chunks into a single text (for smaller documents)
        # For larger documents, we would need to process in batches
        full_text = "\n\n".join([chunk["text"] for chunk in chunks])
        
        # Determine analysis prompt based on type
        if analysis_type == "summary":
            prompt = f"Please provide a comprehensive summary of the following document:\n\n{full_text}"
        elif analysis_type == "key_points":
            prompt = f"Extract and list the key points from the following document:\n\n{full_text}"
        elif analysis_type == "topics":
            prompt = f"Identify and categorize the main topics discussed in the following document:\n\n{full_text}"
        else:
            prompt = f"Analyze the following document and provide insights:\n\n{full_text}"
            
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=settings.LLM_REASONING,
            messages=[
                {"role": "system", "content": "You are an expert at document analysis and summarization."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Lower temperature for more factual responses
            max_tokens=1500
        )
        
        # Extract analysis
        analysis = response.choices[0].message.content.strip()
        
        # Return analysis with metadata
        return {
            "document_id": document_id,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "chunk_count": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise Exception(f"Failed to analyze document: {str(e)}")


async def get_document_chunks(document_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a specific document.
    
    Args:
        document_id: ID of the document
        user_id: ID of the user who owns the document
        
    Returns:
        List[Dict[str, Any]]: List of document chunks
    """
    try:
        # This is a placeholder - replace with your actual vector DB implementation
        # For testing purposes, we'll load from the local JSON file
        output_dir = Path("./document_chunks")
        chunk_file = output_dir / f"{document_id}_chunks.json"
        
        if not chunk_file.exists():
            return []
            
        with open(chunk_file, "r") as f:
            chunks = json.load(f)
            
        return chunks
        
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        return []

from typing import List, Dict, Any, Optional
import logging
import uuid
import re
import json
import random
from datetime import datetime

# Import OpenAI service
from app.services.openai_service import get_openai_client

# Import utility modules
from app.utils.nlp import extract_entities_spacy, extract_keywords, extract_sentences
from app.utils.visualization import extract_chart_data, extract_table_data, create_chart
from app.utils.citation import extract_citation_contexts, extract_keywords_from_text, generate_mock_reference, generate_citation

# Import schemas
from app.schemas.research import (
    AnalysisType, CitationStyle, ChartType, DataType,
    Analysis, SentimentAnalysis, Entity, Topic,
    InlineCitation, Reference, ChartData, TableData
)

# Setup logging
logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH = 10000  # Maximum text length to process
DEFAULT_MODEL = "gpt-4o"  # Default model for analysis

async def analyze_text(text: str, analysis_type: AnalysisType = AnalysisType.full) -> Analysis:
    """
    Analyze text content to extract insights, summaries, or key points
    """
    # Truncate text if it's too long
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
        logger.warning(f"Text was truncated to {MAX_TEXT_LENGTH} characters")
    
    analysis = Analysis()
    
    try:
        # Try to use our utility functions first
        if analysis_type == AnalysisType.summary or analysis_type == AnalysisType.full:
            # Extract sentences and use the first few as a summary
            sentences = extract_sentences(text)
            if sentences:
                # Take first sentence, a middle sentence, and last sentence
                summary_sentences = [sentences[0]]
                if len(sentences) > 2:
                    summary_sentences.append(sentences[len(sentences) // 2])
                if len(sentences) > 1:
                    summary_sentences.append(sentences[-1])
                analysis.summary = ' '.join(summary_sentences)
        
        if analysis_type == AnalysisType.key_points or analysis_type == AnalysisType.full:
            # Extract keywords and convert to key points
            keywords = extract_keywords(text)
            if keywords:
                # Convert keywords to sentences
                key_points = [f"The text discusses {keyword}." for keyword in keywords[:5]]
                analysis.key_points = key_points
        
        if analysis_type == AnalysisType.full:
            # Extract entities using spaCy
            entities = extract_entities_spacy(text)
            if entities:
                analysis.entities = [Entity(**entity) for entity in entities]
        
        # For sentiment analysis and topics, we still need OpenAI
        client = get_openai_client()
        
        # Check if we need to fill in missing analysis components
        if (analysis_type == AnalysisType.summary or analysis_type == AnalysisType.full) and not analysis.summary:
            summary = await generate_summary(client, text)
            analysis.summary = summary
        
        if analysis_type == AnalysisType.sentiment or analysis_type == AnalysisType.full:
            sentiment = await analyze_sentiment(client, text)
            analysis.sentiment = sentiment
        
        if (analysis_type == AnalysisType.key_points or analysis_type == AnalysisType.full) and not analysis.key_points:
            key_points = await extract_key_points(client, text)
            analysis.key_points = key_points
        
        if analysis_type == AnalysisType.full:
            if not analysis.entities:
                entities = await extract_entities(client, text)
                analysis.entities = entities
            
            topics = await identify_topics(client, text)
            analysis.topics = topics
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        # Fall back to OpenAI for all analysis
        try:
            client = get_openai_client()
            analysis = Analysis()
            
            # Generate analysis based on the requested type
            if analysis_type == AnalysisType.summary or analysis_type == AnalysisType.full:
                summary = await generate_summary(client, text)
                analysis.summary = summary
            
            if analysis_type == AnalysisType.sentiment or analysis_type == AnalysisType.full:
                sentiment = await analyze_sentiment(client, text)
                analysis.sentiment = sentiment
            
            if analysis_type == AnalysisType.key_points or analysis_type == AnalysisType.full:
                key_points = await extract_key_points(client, text)
                analysis.key_points = key_points
            
            if analysis_type == AnalysisType.full:
                entities = await extract_entities(client, text)
                topics = await identify_topics(client, text)
                analysis.entities = entities
                analysis.topics = topics
            
            return analysis
        except Exception as e2:
            logger.error(f"Error in fallback text analysis: {str(e2)}")
            raise e

async def generate_summary(client: Any, text: str) -> str:
    """Generate a summary of the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a text summarization expert. Provide a concise summary of the text."},
                {"role": "user", "content": f"Summarize the following text in a concise paragraph:\n\n{text}"}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return "Error generating summary."

async def analyze_sentiment(client: Any, text: str) -> SentimentAnalysis:
    """Analyze sentiment of the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a sentiment analysis expert. Analyze the sentiment of the text and provide a score between -1 (very negative) and 1 (very positive), and a label."},
                {"role": "user", "content": f"Analyze the sentiment of the following text and respond with a JSON object containing a 'score' (between -1 and 1) and a 'label' (e.g., 'Positive', 'Negative', 'Neutral'):\n\n{text}"}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return SentimentAnalysis(score=float(result["score"]), label=result["label"])
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return SentimentAnalysis(score=0.0, label="Neutral")

async def extract_key_points(client: Any, text: str) -> List[str]:
    """Extract key points from the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a text analysis expert. Extract the key points from the text."},
                {"role": "user", "content": f"Extract 3-5 key points from the following text and respond with a JSON array of strings:\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("key_points", [])
    except Exception as e:
        logger.error(f"Error extracting key points: {str(e)}")
        return ["Error extracting key points."]

async def extract_entities(client: Any, text: str) -> List[Entity]:
    """Extract entities from the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a named entity recognition expert. Extract entities from the text."},
                {"role": "user", "content": f"Extract the main entities from the following text and respond with a JSON array of objects, each with 'name', 'type', and 'relevance' (0-1) properties:\n\n{text}"}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        entities = result.get("entities", [])
        return [Entity(**entity) for entity in entities]
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return []

async def identify_topics(client: Any, text: str) -> List[Topic]:
    """Identify topics in the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a topic modeling expert. Identify the main topics in the text."},
                {"role": "user", "content": f"Identify 3-5 main topics in the following text and respond with a JSON array of objects, each with 'name' and 'score' (0-1) properties:\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        topics = result.get("topics", [])
        return [Topic(**topic) for topic in topics]
    except Exception as e:
        logger.error(f"Error identifying topics: {str(e)}")
        return []

async def generate_citations(text: str, style: CitationStyle = CitationStyle.apa) -> Dict[str, Any]:
    """
    Generate in-line citations and references for a given text
    """
    # Truncate text if it's too long
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
        logger.warning(f"Text was truncated to {MAX_TEXT_LENGTH} characters")
    
    try:
        # Extract keywords from the text
        keywords = extract_keywords_from_text(text)
        
        # Extract citation contexts based on keywords
        citation_contexts = extract_citation_contexts(text, keywords)
        
        # Generate references based on keywords
        num_references = min(5, max(3, len(citation_contexts)))
        references_list = []
        
        for _ in range(num_references):
            ref = generate_mock_reference(keywords, style.value)
            references_list.append(Reference(**ref))
        
        # Generate inline citations
        inline_citations_list = []
        for context in citation_contexts:
            # Select a random reference
            ref = random.choice(references_list)
            authors = ref.authors if hasattr(ref, 'authors') and ref.authors else ["Author"]
            year = ref.year if hasattr(ref, 'year') and ref.year else "2023"
            
            # Generate citation text
            citation_text = generate_citation(authors, year, style.value)
            
            inline_citations_list.append(InlineCitation(
                text=context["text"],
                citation=citation_text,
                confidence=context["confidence"]
            ))
        
        # If no citations were found using our utility, fall back to OpenAI
        if not inline_citations_list or not references_list:
            client = get_openai_client()
            # Generate inline citations
            inline_citations_list = await generate_inline_citations(client, text, style)
            
            # Generate references
            references_list = await generate_references(client, text, style)
        
        return {
            "inline_citations": inline_citations_list,
            "references": references_list
        }
    
    except Exception as e:
        logger.error(f"Error generating citations: {str(e)}")
        # Fall back to OpenAI
        try:
            client = get_openai_client()
            # Generate inline citations
            inline_citations = await generate_inline_citations(client, text, style)
            
            # Generate references
            references = await generate_references(client, text, style)
            
            return {
                "inline_citations": inline_citations,
                "references": references
            }
        except Exception as e2:
            logger.error(f"Error in fallback citation generation: {str(e2)}")
            raise e

async def generate_inline_citations(client: Any, text: str, style: CitationStyle) -> List[InlineCitation]:
    """Generate inline citations for the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": f"You are a citation expert. Generate inline citations in {style.value.upper()} style for the text."},
                {"role": "user", "content": f"Identify statements in the following text that should be cited and generate inline citations in {style.value.upper()} style. Respond with a JSON array of objects, each with 'text' (the original text segment), 'citation' (the citation text), and 'confidence' (0-1) properties:\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        citations = result.get("citations", [])
        return [InlineCitation(**citation) for citation in citations]
    except Exception as e:
        logger.error(f"Error generating inline citations: {str(e)}")
        return []

async def generate_references(client: Any, text: str, style: CitationStyle, count: int = 5) -> List[Reference]:
    """Generate references for the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": f"You are a reference generation expert. Generate {count} references in {style.value.upper()} style based on the content of the text."},
                {"role": "user", "content": f"Generate {count} references in {style.value.upper()} style based on the content of the following text. Respond with a JSON array of objects, each with 'id', 'reference', 'url' (optional), 'doi' (optional), 'year', 'authors' (array), 'title', 'journal' (optional), and 'publisher' (optional) properties:\n\n{text}"}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        refs = result.get("references", [])
        
        # Ensure each reference has an ID
        for ref in refs:
            if "id" not in ref or not ref["id"]:
                ref["id"] = str(uuid.uuid4())
        
        return [Reference(**ref) for ref in refs]
    except Exception as e:
        logger.error(f"Error generating references: {str(e)}")
        return []

async def generate_visualizations(
    text: str, 
    data_type: DataType = DataType.chart,
    chart_type: ChartType = ChartType.bar
) -> Dict[str, Any]:
    """
    Generate visualizations (charts or tables) from text data
    """
    # Truncate text if it's too long
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
        logger.warning(f"Text was truncated to {MAX_TEXT_LENGTH} characters")
    
    try:
        # First try to extract data using our utility functions
        if data_type == DataType.table:
            table_data = extract_table_data(text)
            if table_data["headers"] and table_data["rows"]:
                return {
                    "visualization_type": "table",
                    "title": "Data Table",
                    "description": "Extracted from the provided text",
                    "table_data": table_data
                }
            else:
                # Fall back to OpenAI if no data was extracted
                client = get_openai_client()
                return await generate_table_visualization(client, text)
        else:
            chart_data = extract_chart_data(text)
            if chart_data["labels"] and chart_data["datasets"][0]["data"]:
                # Generate chart image
                image_url = create_chart(chart_data, chart_type.value, f"{chart_type.value.capitalize()} Chart")
                
                return {
                    "visualization_type": "chart",
                    "title": f"{chart_type.value.capitalize()} Chart",
                    "description": "Extracted from the provided text",
                    "chart_type": chart_type.value,
                    "chart_data": chart_data,
                    "image_url": image_url
                }
            else:
                # Fall back to OpenAI if no data was extracted
                client = get_openai_client()
                return await generate_chart_visualization(client, text, chart_type)
    
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        # Fall back to OpenAI
        try:
            client = get_openai_client()
            if data_type == DataType.table:
                return await generate_table_visualization(client, text)
            else:
                return await generate_chart_visualization(client, text, chart_type)
        except Exception as e2:
            logger.error(f"Error in fallback visualization generation: {str(e2)}")
            raise e

async def generate_table_visualization(client: Any, text: str) -> Dict[str, Any]:
    """Generate a table visualization from the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a data visualization expert. Extract tabular data from the text and format it as a table."},
                {"role": "user", "content": f"Extract tabular data from the following text and format it as a table. Respond with a JSON object containing 'title', 'description', 'headers' (array of column names), and 'rows' (array of arrays, each representing a row of data):\n\n{text}"}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "visualization_type": "table",
            "title": result.get("title", "Data Table"),
            "description": result.get("description", ""),
            "table_data": {
                "headers": result.get("headers", []),
                "rows": result.get("rows", [])
            }
        }
    except Exception as e:
        logger.error(f"Error generating table visualization: {str(e)}")
        return {
            "visualization_type": "table",
            "title": "Error",
            "description": "Error generating table visualization.",
            "table_data": {
                "headers": ["Error"],
                "rows": [["Failed to generate table visualization."]]
            }
        }

async def generate_chart_visualization(client: Any, text: str, chart_type: ChartType) -> Dict[str, Any]:
    """Generate a chart visualization from the text"""
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": f"You are a data visualization expert. Extract data from the text and format it for a {chart_type.value} chart."},
                {"role": "user", "content": f"Extract data from the following text that would be suitable for a {chart_type.value} chart. Respond with a JSON object containing 'title', 'description', 'labels' (array of x-axis labels or categories), and 'datasets' (array of objects, each with 'label', 'data' (array of numeric values), 'backgroundColor' (array of colors, optional), and 'borderColor' (array of colors, optional)):\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Generate a placeholder image URL (in a real implementation, this would be a call to a chart generation service)
        image_url = f"https://example.com/charts/{chart_type.value}?title={result.get('title', 'Chart')}&t={datetime.now().timestamp()}"
        
        return {
            "visualization_type": "chart",
            "title": result.get("title", f"{chart_type.value.capitalize()} Chart"),
            "description": result.get("description", ""),
            "chart_type": chart_type.value,
            "chart_data": {
                "labels": result.get("labels", []),
                "datasets": result.get("datasets", [])
            },
            "image_url": image_url
        }
    except Exception as e:
        logger.error(f"Error generating chart visualization: {str(e)}")
        return {
            "visualization_type": "chart",
            "title": "Error",
            "description": "Error generating chart visualization.",
            "chart_type": chart_type.value,
            "chart_data": {
                "labels": ["Error"],
                "datasets": [{
                    "label": "Error",
                    "data": [0],
                    "backgroundColor": ["#ff0000"]
                }]
            }
        }

async def generate_references_only(
    text: str, 
    style: CitationStyle,
    count: int = 5
) -> Dict[str, Any]:
    """
    Generate references in a specific style
    """
    # Truncate text if it's too long
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."
        logger.warning(f"Text was truncated to {MAX_TEXT_LENGTH} characters")
    
    try:
        # Extract keywords from the text
        keywords = extract_keywords_from_text(text)
        
        # Generate references based on keywords
        references_list = []
        for _ in range(count):
            ref = generate_mock_reference(keywords, style.value)
            references_list.append(Reference(**ref))
        
        return {
            "references": references_list
        }
    
    except Exception as e:
        logger.error(f"Error generating references: {str(e)}")
        # Fall back to OpenAI
        try:
            client = get_openai_client()
            references = await generate_references(client, text, style, count)
            
            return {
                "references": references
            }
        except Exception as e2:
            logger.error(f"Error in fallback reference generation: {str(e2)}")
            raise e

"""
Natural Language Processing utilities for research tools.
"""
import re
import logging
from typing import List, Dict, Any, Optional
import spacy
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

# Initialize logging
logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK resources: {str(e)}")

# Initialize spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f"Failed to load spaCy model: {str(e)}")
    nlp = None

# Initialize NLTK components
try:
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
except Exception as e:
    logger.warning(f"Failed to initialize NLTK components: {str(e)}")
    stop_words = set()
    lemmatizer = None


def preprocess_text(text: str) -> str:
    """
    Preprocess text by removing special characters, extra whitespace, etc.
    
    Args:
        text: The input text to preprocess
        
    Returns:
        Preprocessed text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.
    
    Args:
        text: The input text
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    try:
        return sent_tokenize(text)
    except Exception as e:
        logger.error(f"Error extracting sentences: {str(e)}")
        # Fallback to simple period-based splitting
        return [s.strip() + '.' for s in text.split('.') if s.strip()]


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: The input text
        top_n: Number of top keywords to return
        
    Returns:
        List of keywords
    """
    if not text or not nlp:
        return []
    
    try:
        # Process the text with spaCy
        doc = nlp(text)
        
        # Extract nouns and adjectives
        keywords = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop:
                keywords.append(token.lemma_)
        
        # Count frequencies
        keyword_freq = {}
        for word in keywords:
            if word in keyword_freq:
                keyword_freq[word] += 1
            else:
                keyword_freq[word] = 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N keywords
        return [word for word, freq in sorted_keywords[:top_n]]
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return []


def extract_entities_spacy(text: str) -> List[Dict[str, Any]]:
    """
    Extract named entities using spaCy.
    
    Args:
        text: The input text
        
    Returns:
        List of entities with their types
    """
    if not text or not nlp:
        return []
    
    try:
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "name": ent.text,
                "type": ent.label_,
                "relevance": 1.0  # Default relevance score
            })
        
        return entities
    
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return []


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using spaCy.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2 or not nlp:
        return 0.0
    
    try:
        doc1 = nlp(text1)
        doc2 = nlp(text2)
        
        return doc1.similarity(doc2)
    
    except Exception as e:
        logger.error(f"Error calculating text similarity: {str(e)}")
        return 0.0


def extract_numeric_data(text: str) -> Dict[str, List[float]]:
    """
    Extract numeric data from text for visualization.
    
    Args:
        text: The input text
        
    Returns:
        Dictionary with labels and values
    """
    if not text:
        return {"labels": [], "values": []}
    
    try:
        # Look for patterns like "X: 10.5" or "X - 10.5"
        pattern = r'([A-Za-z\s]+)[\:\-]\s*(\d+\.?\d*)'
        matches = re.findall(pattern, text)
        
        labels = []
        values = []
        
        for match in matches:
            label = match[0].strip()
            value = float(match[1])
            
            labels.append(label)
            values.append(value)
        
        return {"labels": labels, "values": values}
    
    except Exception as e:
        logger.error(f"Error extracting numeric data: {str(e)}")
        return {"labels": [], "values": []}


def extract_tabular_data(text: str) -> Dict[str, Any]:
    """
    Extract tabular data from text.
    
    Args:
        text: The input text
        
    Returns:
        Dictionary with headers and rows
    """
    if not text:
        return {"headers": [], "rows": []}
    
    try:
        # This is a simplified approach - in a real implementation,
        # you would need more sophisticated parsing
        lines = text.strip().split('\n')
        
        # Try to find table-like structures
        potential_tables = []
        current_table = []
        
        for line in lines:
            # If line contains multiple tab or multiple spaces (3+)
            if '\t' in line or '  ' in line:
                current_table.append(line)
            elif current_table:
                potential_tables.append(current_table)
                current_table = []
        
        if current_table:
            potential_tables.append(current_table)
        
        # Process the first potential table found
        if potential_tables:
            table = potential_tables[0]
            
            # Split by tabs or multiple spaces
            if '\t' in table[0]:
                rows = [line.split('\t') for line in table]
            else:
                rows = [re.split(r'\s{2,}', line) for line in table]
            
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            return {"headers": headers, "rows": data_rows}
        
        return {"headers": [], "rows": []}
    
    except Exception as e:
        logger.error(f"Error extracting tabular data: {str(e)}")
        return {"headers": [], "rows": []}


def format_citation(
    authors: List[str], 
    year: str, 
    title: str, 
    source: str, 
    style: str = "apa"
) -> str:
    """
    Format a citation according to the specified style.
    
    Args:
        authors: List of author names
        year: Publication year
        title: Title of the work
        source: Source (journal, book, etc.)
        style: Citation style (apa, mla, chicago, harvard, ieee)
        
    Returns:
        Formatted citation string
    """
    if not authors or not title:
        return ""
    
    try:
        style = style.lower()
        
        if style == "apa":
            # APA style
            author_text = ", ".join(authors[:-1])
            if author_text:
                author_text += f", & {authors[-1]}"
            else:
                author_text = authors[-1]
            
            return f"{author_text} ({year}). {title}. {source}."
        
        elif style == "mla":
            # MLA style
            author_text = ", ".join(authors[:-1])
            if author_text:
                author_text += f", and {authors[-1]}"
            else:
                author_text = authors[-1]
            
            return f"{author_text}. \"{title}.\" {source}, {year}."
        
        elif style == "chicago":
            # Chicago style
            author_text = ", ".join(authors[:-1])
            if author_text:
                author_text += f", and {authors[-1]}"
            else:
                author_text = authors[-1]
            
            return f"{author_text}. \"{title}.\" {source} ({year})."
        
        elif style == "harvard":
            # Harvard style
            author_text = ", ".join(authors[:-1])
            if author_text:
                author_text += f" and {authors[-1]}"
            else:
                author_text = authors[-1]
            
            return f"{author_text} ({year}). {title}. {source}."
        
        elif style == "ieee":
            # IEEE style
            if len(authors) > 3:
                author_text = f"{authors[0]} et al."
            else:
                author_text = ", ".join(authors)
            
            return f"{author_text}, \"{title},\" {source}, {year}."
        
        else:
            # Default to APA
            author_text = ", ".join(authors[:-1])
            if author_text:
                author_text += f", & {authors[-1]}"
            else:
                author_text = authors[-1]
            
            return f"{author_text} ({year}). {title}. {source}."
    
    except Exception as e:
        logger.error(f"Error formatting citation: {str(e)}")
        return f"{', '.join(authors)} ({year}). {title}. {source}."

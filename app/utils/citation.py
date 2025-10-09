"""
Citation and reference management utilities for research tools.
"""
import logging
import re
import uuid
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta

# Import NLP utilities
from app.utils.nlp import format_citation

# Initialize logging
logger = logging.getLogger(__name__)

# Sample data for generating mock citations and references
SAMPLE_AUTHORS = [
    ["Smith, J.", "Johnson, P."],
    ["Garcia, M.", "Rodriguez, A.", "Lee, S."],
    ["Williams, B.", "Brown, T."],
    ["Davis, R.", "Miller, C."],
    ["Wilson, E.", "Moore, D."],
    ["Taylor, L.", "Anderson, J."],
    ["Thomas, K.", "Jackson, M."],
    ["White, N.", "Harris, P."],
    ["Martin, S.", "Thompson, R."],
    ["Clark, D.", "Lewis, G."],
]

SAMPLE_JOURNALS = [
    "Journal of Computer Science",
    "International Journal of Artificial Intelligence",
    "Data Science Review",
    "Computational Linguistics Quarterly",
    "Machine Learning Research",
    "Neural Networks Today",
    "Information Processing Letters",
    "Journal of Natural Language Processing",
    "Advances in Computing",
    "Digital Humanities Journal",
]

SAMPLE_PUBLISHERS = [
    "Academic Press",
    "Springer",
    "MIT Press",
    "Oxford University Press",
    "Cambridge University Press",
    "Elsevier",
    "Wiley",
    "IEEE",
    "ACM",
    "Taylor & Francis",
]

SAMPLE_DOMAINS = [
    "example.com",
    "academia.edu",
    "research.org",
    "university.edu",
    "science.org",
    "journal.com",
    "publisher.net",
    "institute.org",
    "conference.info",
    "repository.io",
]


def extract_citation_contexts(text: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Extract contexts from text that might need citations based on keywords.
    
    Args:
        text: The input text
        keywords: List of keywords to look for
        
    Returns:
        List of dictionaries with text segments and confidence scores
    """
    if not text or not keywords:
        return []
    
    contexts = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        # Check if sentence contains any of the keywords
        if any(keyword.lower() in sentence.lower() for keyword in keywords):
            # Check if sentence contains statements that might need citation
            if re.search(r'(show|found|suggest|indicate|report|according|study|research|evidence|data)', 
                         sentence, re.IGNORECASE):
                contexts.append({
                    "text": sentence,
                    "confidence": 0.8
                })
            else:
                contexts.append({
                    "text": sentence,
                    "confidence": 0.5
                })
    
    return contexts


def generate_citation(authors: List[str], year: str, style: str = "apa") -> str:
    """
    Generate a citation string based on the authors and year.
    
    Args:
        authors: List of author names
        year: Publication year
        style: Citation style
        
    Returns:
        Citation string
    """
    style = style.lower()
    
    if style == "apa":
        if len(authors) == 1:
            return f"{authors[0]} ({year})"
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]} ({year})"
        else:
            return f"{authors[0]} et al. ({year})"
    
    elif style == "mla":
        if len(authors) == 1:
            return f"{authors[0]}"
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            return f"{authors[0]} et al."
    
    elif style == "chicago":
        if len(authors) == 1:
            return f"{authors[0]} ({year})"
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]} ({year})"
        else:
            return f"{authors[0]} et al. ({year})"
    
    elif style == "harvard":
        if len(authors) == 1:
            return f"{authors[0]}, {year}"
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}, {year}"
        else:
            return f"{authors[0]} et al., {year}"
    
    elif style == "ieee":
        return f"[{random.randint(1, 30)}]"
    
    else:
        # Default to APA
        if len(authors) == 1:
            return f"{authors[0]} ({year})"
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]} ({year})"
        else:
            return f"{authors[0]} et al. ({year})"


def generate_reference_id() -> str:
    """
    Generate a unique reference ID.
    
    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())


def generate_mock_reference(
    topic_keywords: List[str], 
    style: str = "apa",
    year_range: tuple = (2018, 2024)
) -> Dict[str, Any]:
    """
    Generate a mock reference based on topic keywords.
    
    Args:
        topic_keywords: List of keywords related to the topic
        style: Citation style
        year_range: Range of years for publication dates
        
    Returns:
        Dictionary with reference information
    """
    # Select random elements
    authors = random.choice(SAMPLE_AUTHORS)
    year = str(random.randint(year_range[0], year_range[1]))
    
    # Generate a title using the keywords
    if topic_keywords and len(topic_keywords) > 0:
        # Use 1-3 random keywords in the title
        num_keywords = min(3, len(topic_keywords))
        selected_keywords = random.sample(topic_keywords, num_keywords)
        
        title_templates = [
            "Advances in {0} Research: A Comprehensive Study",
            "Understanding {0}: Analysis and Implications",
            "The Role of {0} in Modern Applications",
            "A Novel Approach to {0} Using Advanced Techniques",
            "{0}: Challenges and Opportunities"
        ]
        
        title_template = random.choice(title_templates)
        title = title_template.format(" and ".join(selected_keywords))
    else:
        title = "Comprehensive Research Study"
    
    # Select journal or publisher
    is_journal = random.choice([True, False])
    if is_journal:
        source = random.choice(SAMPLE_JOURNALS)
        journal = source
        publisher = None
    else:
        source = random.choice(SAMPLE_PUBLISHERS)
        journal = None
        publisher = source
    
    # Generate URL and DOI
    domain = random.choice(SAMPLE_DOMAINS)
    url = f"https://www.{domain}/article/{uuid.uuid4().hex[:8]}"
    doi = f"10.{random.randint(1000, 9999)}/{uuid.uuid4().hex[:8]}"
    
    # Format the reference string
    reference_str = format_citation(authors, year, title, source, style)
    
    return {
        "id": generate_reference_id(),
        "reference": reference_str,
        "url": url,
        "doi": doi,
        "year": year,
        "authors": authors,
        "title": title,
        "journal": journal,
        "publisher": publisher
    }


def extract_keywords_from_text(text: str) -> List[str]:
    """
    Extract potential keywords from text for citation matching.
    
    Args:
        text: The input text
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # This is a simplified approach - in a real implementation,
    # you would use more sophisticated NLP techniques
    
    # Remove common words and punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    common_words = {
        'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with',
        'by', 'about', 'as', 'of', 'from', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'can', 'may', 'might', 'must', 'this',
        'that', 'these', 'those', 'it', 'they', 'them', 'their', 'we', 'us',
        'our', 'i', 'me', 'my', 'you', 'your'
    }
    
    words = text.split()
    keywords = [word for word in words if word not in common_words and len(word) > 3]
    
    # Get unique keywords
    unique_keywords = list(set(keywords))
    
    # Sort by frequency in the original text
    keyword_freq = {keyword: text.lower().count(keyword) for keyword in unique_keywords}
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return top 10 keywords
    return [keyword for keyword, _ in sorted_keywords[:10]]

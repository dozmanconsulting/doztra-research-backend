import pytest
from unittest.mock import patch, MagicMock
import spacy
import nltk

from app.utils.nlp import (
    preprocess_text,
    extract_sentences,
    extract_keywords,
    extract_entities_spacy,
    calculate_text_similarity,
    extract_numeric_data,
    extract_tabular_data,
    format_citation
)


class TestNLPUtils:
    """Test suite for NLP utility functions"""

    def test_preprocess_text(self):
        """Test text preprocessing function"""
        # Test with normal text
        text = "Hello, world! This is a test. http://example.com user@example.com 123"
        processed = preprocess_text(text)
        assert "hello world this is a test" in processed
        assert "http" not in processed
        assert "@" not in processed
        assert "123" not in processed

        # Test with empty text
        assert preprocess_text("") == ""
        assert preprocess_text(None) == ""

    def test_extract_sentences(self):
        """Test sentence extraction function"""
        # Test with normal text
        text = "This is the first sentence. This is the second sentence! Is this the third sentence?"
        sentences = extract_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "This is the first sentence."
        assert sentences[1] == "This is the second sentence!"
        assert sentences[2] == "Is this the third sentence?"

        # Test with empty text
        assert extract_sentences("") == []
        assert extract_sentences(None) == []

    @patch("app.utils.nlp.nlp")
    def test_extract_keywords(self, mock_nlp):
        """Test keyword extraction function"""
        # Mock spaCy's behavior
        mock_doc = MagicMock()
        mock_tokens = []
        for word, pos in [("test", "NOUN"), ("important", "ADJ"), ("the", "DET"), ("is", "VERB")]:
            token = MagicMock()
            token.text = word
            token.pos_ = pos
            token.is_stop = word in ["the", "is"]
            token.lemma_ = word
            mock_tokens.append(token)
        
        mock_doc.__iter__.return_value = mock_tokens
        mock_nlp.return_value = mock_doc

        # Test with normal text
        keywords = extract_keywords("This is a test text with important keywords", top_n=2)
        assert len(keywords) <= 2
        
        # Test with empty text
        assert extract_keywords("") == []
        assert extract_keywords(None) == []

    @patch("app.utils.nlp.nlp")
    def test_extract_entities_spacy(self, mock_nlp):
        """Test entity extraction function"""
        # Mock spaCy's behavior
        mock_doc = MagicMock()
        mock_ent1 = MagicMock()
        mock_ent1.text = "Google"
        mock_ent1.label_ = "ORG"
        
        mock_ent2 = MagicMock()
        mock_ent2.text = "John Smith"
        mock_ent2.label_ = "PERSON"
        
        mock_doc.ents = [mock_ent1, mock_ent2]
        mock_nlp.return_value = mock_doc

        # Test with normal text
        entities = extract_entities_spacy("Google was founded by Larry Page and Sergey Brin. John Smith works there.")
        assert len(entities) == 2
        assert entities[0]["name"] == "Google"
        assert entities[0]["type"] == "ORG"
        assert entities[1]["name"] == "John Smith"
        assert entities[1]["type"] == "PERSON"
        
        # Test with empty text
        assert extract_entities_spacy("") == []
        assert extract_entities_spacy(None) == []

    @patch("app.utils.nlp.nlp")
    def test_calculate_text_similarity(self, mock_nlp):
        """Test text similarity calculation function"""
        # Mock spaCy's behavior
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        mock_doc1.similarity.return_value = 0.85
        mock_nlp.side_effect = [mock_doc1, mock_doc2]

        # Test with normal text
        similarity = calculate_text_similarity(
            "This is the first text about AI.",
            "This is the second text about artificial intelligence."
        )
        assert similarity == 0.85
        
        # Test with empty text
        assert calculate_text_similarity("", "") == 0.0
        assert calculate_text_similarity(None, "text") == 0.0
        assert calculate_text_similarity("text", None) == 0.0

    def test_extract_numeric_data(self):
        """Test numeric data extraction function"""
        # Test with normal text containing numeric data
        text = "Category A: 10.5\nCategory B: 20\nCategory C - 30.75"
        data = extract_numeric_data(text)
        assert "labels" in data
        assert "values" in data
        assert len(data["labels"]) == 3
        assert len(data["values"]) == 3
        assert "Category A" in data["labels"]
        assert 10.5 in data["values"]
        assert "Category B" in data["labels"]
        assert 20.0 in data["values"]
        assert "Category C" in data["labels"]
        assert 30.75 in data["values"]
        
        # Test with text without numeric data
        text = "This text does not contain any numeric data in the expected format."
        data = extract_numeric_data(text)
        assert len(data["labels"]) == 0
        assert len(data["values"]) == 0
        
        # Test with empty text
        assert extract_numeric_data("") == {"labels": [], "values": []}
        assert extract_numeric_data(None) == {"labels": [], "values": []}

    def test_extract_tabular_data(self):
        """Test tabular data extraction function"""
        # Test with tab-separated data
        text = "Column 1\tColumn 2\tColumn 3\nA\t10\t20\nB\t30\t40\nC\t50\t60"
        data = extract_tabular_data(text)
        assert "headers" in data
        assert "rows" in data
        assert len(data["headers"]) == 3
        assert len(data["rows"]) == 3
        assert data["headers"][0] == "Column 1"
        assert data["rows"][0][0] == "A"
        
        # Test with space-separated data
        text = "Column 1  Column 2  Column 3\nA  10  20\nB  30  40\nC  50  60"
        data = extract_tabular_data(text)
        assert len(data["headers"]) == 3
        assert len(data["rows"]) == 3
        
        # Test with text without tabular data
        text = "This text does not contain any tabular data."
        data = extract_tabular_data(text)
        assert len(data["headers"]) == 0
        assert len(data["rows"]) == 0
        
        # Test with empty text
        assert extract_tabular_data("") == {"headers": [], "rows": []}
        assert extract_tabular_data(None) == {"headers": [], "rows": []}

    def test_format_citation(self):
        """Test citation formatting function"""
        authors = ["Smith, J.", "Johnson, P."]
        year = "2023"
        title = "Test Title"
        source = "Journal of Testing"
        
        # Test APA style
        apa = format_citation(authors, year, title, source, "apa")
        assert "Smith, J., & Johnson, P. (2023)" in apa
        assert "Test Title" in apa
        assert "Journal of Testing" in apa
        
        # Test MLA style
        mla = format_citation(authors, year, title, source, "mla")
        assert "Smith, J., and Johnson, P." in mla
        assert "\"Test Title.\"" in mla
        assert "Journal of Testing" in mla
        assert "2023" in mla
        
        # Test Chicago style
        chicago = format_citation(authors, year, title, source, "chicago")
        assert "Smith, J., and Johnson, P." in chicago
        assert "\"Test Title.\"" in chicago
        assert "Journal of Testing" in chicago
        assert "(2023)" in chicago
        
        # Test Harvard style
        harvard = format_citation(authors, year, title, source, "harvard")
        assert "Smith, J. and Johnson, P. (2023)" in harvard
        assert "Test Title" in harvard
        assert "Journal of Testing" in harvard
        
        # Test IEEE style
        ieee = format_citation(authors, year, title, source, "ieee")
        assert "Smith, J., Johnson, P." in ieee
        assert "\"Test Title,\"" in ieee
        assert "Journal of Testing" in ieee
        assert "2023" in ieee
        
        # Test with single author
        single_author = format_citation(["Smith, J."], year, title, source, "apa")
        assert "Smith, J. (2023)" in single_author
        
        # Test with empty authors
        assert format_citation([], year, title, source, "apa") == ""
        
        # Test with empty title
        assert format_citation(authors, year, "", source, "apa") == ""

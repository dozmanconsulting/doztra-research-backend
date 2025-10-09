import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
import json

from app.main import app
from app.schemas.research import (
    AnalysisType, CitationStyle, ChartType, DataType,
    Analysis, SentimentAnalysis, Entity, Topic,
    InlineCitation, Reference
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    return MagicMock(id="test_user_id", email="test@example.com", is_active=True)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}


@patch("app.api.deps.get_current_active_user")
def test_analyze_text(mock_get_user, client, mock_current_user, auth_headers):
    mock_get_user.return_value = mock_current_user
    
    # Mock the analyze_text service function
    with patch("app.services.research.analyze_text") as mock_analyze:
        # Test case 1: Full analysis
        mock_analyze.return_value = Analysis(
            summary="This is a test summary.",
            sentiment=SentimentAnalysis(score=0.8, label="Positive"),
            key_points=["Point 1", "Point 2"],
            entities=[
                Entity(name="Test Entity", type="ORG", relevance=0.9)
            ],
            topics=[
                Topic(name="Test Topic", score=0.8)
            ]
        )
        
        response = client.post(
            "/api/research/analyze",
            json={"text": "This is a test text.", "analysis_type": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert data["analysis"]["summary"] == "This is a test summary."
        assert data["analysis"]["sentiment"]["score"] == 0.8
        assert data["analysis"]["sentiment"]["label"] == "Positive"
        assert len(data["analysis"]["key_points"]) == 2
        assert len(data["analysis"]["entities"]) == 1
        assert len(data["analysis"]["topics"]) == 1
        
        # Verify the service was called with the right parameters
        mock_analyze.assert_called_once_with(text="This is a test text.", analysis_type=AnalysisType.full)
        mock_analyze.reset_mock()
        
        # Test case 2: Summary analysis only
        mock_analyze.return_value = Analysis(
            summary="This is just a summary."
        )
        
        response = client.post(
            "/api/research/analyze",
            json={"text": "Another test text.", "analysis_type": "summary"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert data["analysis"]["summary"] == "This is just a summary."
        assert "sentiment" not in data["analysis"]
        assert "key_points" not in data["analysis"]
        assert "entities" not in data["analysis"]
        assert "topics" not in data["analysis"]
        
        mock_analyze.assert_called_once_with(text="Another test text.", analysis_type=AnalysisType.summary)
        mock_analyze.reset_mock()
        
        # Test case 3: Sentiment analysis only
        mock_analyze.return_value = Analysis(
            sentiment=SentimentAnalysis(score=-0.6, label="Negative")
        )
        
        response = client.post(
            "/api/research/analyze",
            json={"text": "Negative text.", "analysis_type": "sentiment"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "summary" not in data["analysis"]
        assert data["analysis"]["sentiment"]["score"] == -0.6
        assert data["analysis"]["sentiment"]["label"] == "Negative"
        
        mock_analyze.assert_called_once_with(text="Negative text.", analysis_type=AnalysisType.sentiment)
        mock_analyze.reset_mock()
        
        # Test case 4: Key points analysis only
        mock_analyze.return_value = Analysis(
            key_points=["Main point 1", "Main point 2", "Main point 3"]
        )
        
        response = client.post(
            "/api/research/analyze",
            json={"text": "Text with key points.", "analysis_type": "key_points"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "summary" not in data["analysis"]
        assert "sentiment" not in data["analysis"]
        assert len(data["analysis"]["key_points"]) == 3
        assert "Main point 1" in data["analysis"]["key_points"]
        
        mock_analyze.assert_called_once_with(text="Text with key points.", analysis_type=AnalysisType.key_points)
        
        # Test case 5: Error handling
        mock_analyze.side_effect = Exception("Test error")
        
        response = client.post(
            "/api/research/analyze",
            json={"text": "Error text.", "analysis_type": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error analyzing text" in data["detail"]


@patch("app.api.deps.get_current_active_user")
def test_generate_citations(mock_get_user, client, mock_current_user, auth_headers):
    mock_get_user.return_value = mock_current_user
    
    # Mock the generate_citations service function
    with patch("app.services.research.generate_citations") as mock_citations:
        # Test case 1: APA style citations
        mock_citations.return_value = {
            "inline_citations": [
                {
                    "text": "This is a statement that needs citation.",
                    "citation": "Smith & Johnson (2023)",
                    "confidence": 0.9
                }
            ],
            "references": [
                {
                    "id": "ref1",
                    "reference": "Smith, J., & Johnson, P. (2023). Test Reference. Journal of Testing.",
                    "url": "https://example.com",
                    "doi": "10.1234/test",
                    "year": "2023",
                    "authors": ["Smith, J.", "Johnson, P."],
                    "title": "Test Reference",
                    "journal": "Journal of Testing"
                }
            ]
        }
        
        response = client.post(
            "/api/research/citations",
            json={"text": "This is a test text.", "style": "apa"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "inline_citations" in data
        assert "references" in data
        assert len(data["inline_citations"]) == 1
        assert len(data["references"]) == 1
        assert data["references"][0]["id"] == "ref1"
        assert data["inline_citations"][0]["citation"] == "Smith & Johnson (2023)"
        
        # Verify the service was called with the right parameters
        mock_citations.assert_called_once_with(text="This is a test text.", style=CitationStyle.apa)
        mock_citations.reset_mock()
        
        # Test case 2: MLA style citations
        mock_citations.return_value = {
            "inline_citations": [
                {
                    "text": "This is a statement that needs citation.",
                    "citation": "Smith and Johnson",
                    "confidence": 0.85
                },
                {
                    "text": "Another statement requiring citation.",
                    "citation": "Brown",
                    "confidence": 0.9
                }
            ],
            "references": [
                {
                    "id": "ref1",
                    "reference": "Smith, John, and Peter Johnson. \"Test Reference.\" Journal of Testing, 2023.",
                    "url": "https://example.com",
                    "year": "2023",
                    "authors": ["Smith, John", "Johnson, Peter"],
                    "title": "Test Reference",
                    "journal": "Journal of Testing"
                },
                {
                    "id": "ref2",
                    "reference": "Brown, Thomas. \"Another Reference.\" Academic Journal, 2022.",
                    "url": "https://example.org",
                    "year": "2022",
                    "authors": ["Brown, Thomas"],
                    "title": "Another Reference",
                    "journal": "Academic Journal"
                }
            ]
        }
        
        response = client.post(
            "/api/research/citations",
            json={"text": "This is a test text with multiple citations.", "style": "mla"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["inline_citations"]) == 2
        assert len(data["references"]) == 2
        assert data["inline_citations"][0]["citation"] == "Smith and Johnson"
        assert "MLA" in data["references"][0]["reference"] or "mla" in data["references"][0]["reference"]
        
        mock_citations.assert_called_once_with(
            text="This is a test text with multiple citations.", 
            style=CitationStyle.mla
        )
        mock_citations.reset_mock()
        
        # Test case 3: Default style (should be APA)
        mock_citations.return_value = {
            "inline_citations": [
                {
                    "text": "Default style citation.",
                    "citation": "Wilson (2022)",
                    "confidence": 0.8
                }
            ],
            "references": [
                {
                    "id": "ref1",
                    "reference": "Wilson, E. (2022). Default Reference. Journal of Defaults.",
                    "year": "2022",
                    "authors": ["Wilson, E."],
                    "title": "Default Reference",
                    "journal": "Journal of Defaults"
                }
            ]
        }
        
        response = client.post(
            "/api/research/citations",
            json={"text": "This is a test with default style."},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["inline_citations"]) == 1
        assert len(data["references"]) == 1
        
        # Default style should be APA
        mock_citations.assert_called_once_with(
            text="This is a test with default style.", 
            style=CitationStyle.apa
        )
        mock_citations.reset_mock()
        
        # Test case 4: Error handling
        mock_citations.side_effect = Exception("Test error")
        
        response = client.post(
            "/api/research/citations",
            json={"text": "Error text.", "style": "chicago"},
            headers=auth_headers
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error generating citations" in data["detail"]


@patch("app.api.deps.get_current_active_user")
def test_generate_visualization(mock_get_user, client, mock_current_user, auth_headers):
    mock_get_user.return_value = mock_current_user
    
    # Mock the generate_visualizations service function
    with patch("app.services.research.generate_visualizations") as mock_visualize:
        # Test case 1: Bar chart visualization
        mock_visualize.return_value = {
            "visualization_type": "chart",
            "title": "Test Bar Chart",
            "description": "A test bar chart",
            "chart_type": "bar",
            "chart_data": {
                "labels": ["A", "B", "C"],
                "datasets": [
                    {
                        "label": "Test Data",
                        "data": [10, 20, 30],
                        "backgroundColor": ["#ff0000", "#00ff00", "#0000ff"]
                    }
                ]
            },
            "image_url": "data:image/png;base64,test"
        }
        
        response = client.post(
            "/api/research/visualize",
            json={"text": "A: 10, B: 20, C: 30", "data_type": "chart", "chart_type": "bar"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["visualization_type"] == "chart"
        assert data["chart_type"] == "bar"
        assert data["title"] == "Test Bar Chart"
        assert "chart_data" in data
        assert "image_url" in data
        assert len(data["chart_data"]["labels"]) == 3
        assert len(data["chart_data"]["datasets"]) == 1
        assert len(data["chart_data"]["datasets"][0]["data"]) == 3
        
        # Verify the service was called with the right parameters
        mock_visualize.assert_called_once_with(
            text="A: 10, B: 20, C: 30", 
            data_type=DataType.chart,
            chart_type=ChartType.bar
        )
        mock_visualize.reset_mock()
        
        # Test case 2: Line chart visualization
        mock_visualize.return_value = {
            "visualization_type": "chart",
            "title": "Test Line Chart",
            "description": "A test line chart",
            "chart_type": "line",
            "chart_data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "datasets": [
                    {
                        "label": "Sales 2023",
                        "data": [65, 59, 80, 81, 56],
                        "borderColor": "#36a2eb"
                    }
                ]
            },
            "image_url": "data:image/png;base64,test_line"
        }
        
        response = client.post(
            "/api/research/visualize",
            json={"text": "Sales data: Jan: 65, Feb: 59, Mar: 80, Apr: 81, May: 56", 
                  "data_type": "chart", 
                  "chart_type": "line"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["visualization_type"] == "chart"
        assert data["chart_type"] == "line"
        assert "Line" in data["title"]
        assert len(data["chart_data"]["labels"]) == 5
        
        mock_visualize.assert_called_once_with(
            text="Sales data: Jan: 65, Feb: 59, Mar: 80, Apr: 81, May: 56", 
            data_type=DataType.chart,
            chart_type=ChartType.line
        )
        mock_visualize.reset_mock()
        
        # Test case 3: Table visualization
        mock_visualize.return_value = {
            "visualization_type": "table",
            "title": "Test Table",
            "description": "A test table",
            "table_data": {
                "headers": ["Column 1", "Column 2"],
                "rows": [
                    ["A", "10"],
                    ["B", "20"],
                    ["C", "30"]
                ]
            }
        }
        
        response = client.post(
            "/api/research/visualize",
            json={"text": "Column 1, Column 2\nA, 10\nB, 20\nC, 30", "data_type": "table"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["visualization_type"] == "table"
        assert "table_data" in data
        assert len(data["table_data"]["headers"]) == 2
        assert len(data["table_data"]["rows"]) == 3
        assert data["table_data"]["rows"][0][0] == "A"
        assert data["table_data"]["rows"][0][1] == "10"
        
        mock_visualize.assert_called_once_with(
            text="Column 1, Column 2\nA, 10\nB, 20\nC, 30", 
            data_type=DataType.table,
            chart_type=ANY
        )
        mock_visualize.reset_mock()
        
        # Test case 4: Default parameters
        mock_visualize.return_value = {
            "visualization_type": "chart",
            "title": "Default Chart",
            "chart_type": "bar",
            "chart_data": {
                "labels": ["X", "Y", "Z"],
                "datasets": [
                    {
                        "label": "Default Data",
                        "data": [5, 10, 15]
                    }
                ]
            },
            "image_url": "data:image/png;base64,default"
        }
        
        response = client.post(
            "/api/research/visualize",
            json={"text": "X: 5, Y: 10, Z: 15"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["visualization_type"] == "chart"
        assert data["chart_type"] == "bar"  # Default chart type should be bar
        
        # Default data_type should be chart and default chart_type should be bar
        mock_visualize.assert_called_once_with(
            text="X: 5, Y: 10, Z: 15", 
            data_type=DataType.chart,
            chart_type=ChartType.bar
        )
        mock_visualize.reset_mock()
        
        # Test case 5: Error handling
        mock_visualize.side_effect = Exception("Test error")
        
        response = client.post(
            "/api/research/visualize",
            json={"text": "Error data", "data_type": "chart", "chart_type": "pie"},
            headers=auth_headers
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error generating visualization" in data["detail"]


@patch("app.api.deps.get_current_active_user")
def test_generate_references(mock_get_user, client, mock_current_user, auth_headers):
    mock_get_user.return_value = mock_current_user
    
    # Mock the generate_references_only service function
    with patch("app.services.research.generate_references_only") as mock_refs:
        # Set up the mock return value
        mock_refs.return_value = {
            "references": [
                {
                    "id": "ref1",
                    "reference": "Smith, J., & Johnson, P. (2023). Test Reference. Journal of Testing.",
                    "url": "https://example.com",
                    "doi": "10.1234/test",
                    "year": "2023",
                    "authors": ["Smith, J.", "Johnson, P."],
                    "title": "Test Reference",
                    "journal": "Journal of Testing"
                },
                {
                    "id": "ref2",
                    "reference": "Brown, T. (2022). Another Test Reference. Journal of Testing.",
                    "url": "https://example.com/2",
                    "doi": "10.1234/test2",
                    "year": "2022",
                    "authors": ["Brown, T."],
                    "title": "Another Test Reference",
                    "journal": "Journal of Testing"
                }
            ]
        }
        
        # Make the request
        response = client.post(
            "/api/research/references",
            json={"text": "This is a test text.", "style": "apa", "count": 2},
            headers=auth_headers
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "references" in data
        assert len(data["references"]) == 2
        assert data["references"][0]["id"] == "ref1"
        assert data["references"][1]["id"] == "ref2"

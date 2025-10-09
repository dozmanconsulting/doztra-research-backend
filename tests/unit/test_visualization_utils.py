import pytest
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt
import io
import base64
import re

from app.utils.visualization import (
    extract_chart_data,
    extract_table_data,
    generate_colors,
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_scatter_chart,
    create_chart,
    create_table_html
)


class TestVisualizationUtils:
    """Test suite for visualization utility functions"""

    @patch("app.utils.visualization.extract_numeric_data")
    def test_extract_chart_data(self, mock_extract_numeric):
        """Test chart data extraction function"""
        # Mock the extract_numeric_data function
        mock_extract_numeric.return_value = {
            "labels": ["A", "B", "C"],
            "values": [10, 20, 30]
        }

        # Test with normal text
        data = extract_chart_data("A: 10, B: 20, C: 30")
        assert "labels" in data
        assert "datasets" in data
        assert len(data["labels"]) == 3
        assert len(data["datasets"]) == 1
        assert data["labels"] == ["A", "B", "C"]
        assert data["datasets"][0]["data"] == [10, 20, 30]
        assert "backgroundColor" in data["datasets"][0]
        assert "borderColor" in data["datasets"][0]
        
        # Test with empty data
        mock_extract_numeric.return_value = {"labels": [], "values": []}
        data = extract_chart_data("")
        assert len(data["labels"]) == 0
        assert len(data["datasets"]) == 1
        assert len(data["datasets"][0]["data"]) == 0

    @patch("app.utils.visualization.extract_tabular_data")
    def test_extract_table_data(self, mock_extract_tabular):
        """Test table data extraction function"""
        # Mock the extract_tabular_data function
        mock_extract_tabular.return_value = {
            "headers": ["Column 1", "Column 2", "Column 3"],
            "rows": [
                ["A", "10", "20"],
                ["B", "30", "40"],
                ["C", "50", "60"]
            ]
        }

        # Test with normal text
        data = extract_table_data("Column 1\tColumn 2\tColumn 3\nA\t10\t20\nB\t30\t40\nC\t50\t60")
        assert "headers" in data
        assert "rows" in data
        assert len(data["headers"]) == 3
        assert len(data["rows"]) == 3
        assert data["headers"][0] == "Column 1"
        assert data["rows"][0][0] == "A"
        
        # Test with empty data
        mock_extract_tabular.return_value = {"headers": [], "rows": []}
        data = extract_table_data("")
        assert len(data["headers"]) == 0
        assert len(data["rows"]) == 0

    def test_generate_colors(self):
        """Test color generation function"""
        # Test with different counts
        colors1 = generate_colors(3)
        assert len(colors1) == 3
        for color in colors1:
            assert color.startswith("rgba(")
            assert color.endswith("0.6)")
        
        colors2 = generate_colors(5, 0.8)
        assert len(colors2) == 5
        for color in colors2:
            assert color.startswith("rgba(")
            assert color.endswith("0.8)")
        
        # Test with count > 10 (should cycle through colors)
        colors3 = generate_colors(15)
        assert len(colors3) == 15
        # First 10 colors should be unique, then they should repeat
        assert colors3[0] == colors3[10]
        assert colors3[1] == colors3[11]

    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.bar")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.xticks")
    @patch("matplotlib.pyplot.tight_layout")
    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_create_bar_chart(self, mock_close, mock_savefig, mock_tight_layout, 
                             mock_xticks, mock_title, mock_bar, mock_figure):
        """Test bar chart creation function"""
        # Mock the BytesIO and base64 encode
        mock_buf = MagicMock(spec=io.BytesIO)
        mock_buf.read.return_value = b"test_image_data"
        
        with patch("io.BytesIO", return_value=mock_buf):
            with patch("base64.b64encode", return_value=b"encoded_test_image_data"):
                # Test with normal data
                data = {
                    "labels": ["A", "B", "C"],
                    "datasets": [{
                        "label": "Test Data",
                        "data": [10, 20, 30],
                        "backgroundColor": ["#ff0000", "#00ff00", "#0000ff"]
                    }]
                }
                
                chart = create_bar_chart(data, "Test Bar Chart")
                assert chart.startswith("data:image/png;base64,")
                assert "encoded_test_image_data" in chart
                
                # Verify matplotlib calls
                mock_figure.assert_called_once()
                mock_bar.assert_called_once()
                mock_title.assert_called_once_with("Test Bar Chart")
                mock_xticks.assert_called_once()
                mock_tight_layout.assert_called_once()
                mock_savefig.assert_called_once()
                mock_close.assert_called_once()
                
                # Test with empty data
                mock_figure.reset_mock()
                mock_bar.reset_mock()
                
                empty_data = {
                    "labels": [],
                    "datasets": [{
                        "label": "Empty Data",
                        "data": []
                    }]
                }
                
                empty_chart = create_bar_chart(empty_data)
                assert empty_chart == ""
                mock_figure.assert_not_called()

    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.plot")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.xticks")
    @patch("matplotlib.pyplot.tight_layout")
    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_create_line_chart(self, mock_close, mock_savefig, mock_tight_layout, 
                              mock_xticks, mock_title, mock_plot, mock_figure):
        """Test line chart creation function"""
        # Mock the BytesIO and base64 encode
        mock_buf = MagicMock(spec=io.BytesIO)
        mock_buf.read.return_value = b"test_image_data"
        
        with patch("io.BytesIO", return_value=mock_buf):
            with patch("base64.b64encode", return_value=b"encoded_test_image_data"):
                # Test with normal data
                data = {
                    "labels": ["A", "B", "C"],
                    "datasets": [{
                        "label": "Test Data",
                        "data": [10, 20, 30],
                        "borderColor": "#0000ff"
                    }]
                }
                
                chart = create_line_chart(data, "Test Line Chart")
                assert chart.startswith("data:image/png;base64,")
                assert "encoded_test_image_data" in chart
                
                # Verify matplotlib calls
                mock_figure.assert_called_once()
                mock_plot.assert_called_once()
                mock_title.assert_called_once_with("Test Line Chart")
                mock_xticks.assert_called_once()
                mock_tight_layout.assert_called_once()
                mock_savefig.assert_called_once()
                mock_close.assert_called_once()

    @patch("matplotlib.pyplot.figure")
    @patch("matplotlib.pyplot.pie")
    @patch("matplotlib.pyplot.title")
    @patch("matplotlib.pyplot.axis")
    @patch("matplotlib.pyplot.savefig")
    @patch("matplotlib.pyplot.close")
    def test_create_pie_chart(self, mock_close, mock_savefig, mock_axis, 
                             mock_title, mock_pie, mock_figure):
        """Test pie chart creation function"""
        # Mock the BytesIO and base64 encode
        mock_buf = MagicMock(spec=io.BytesIO)
        mock_buf.read.return_value = b"test_image_data"
        
        with patch("io.BytesIO", return_value=mock_buf):
            with patch("base64.b64encode", return_value=b"encoded_test_image_data"):
                # Test with normal data
                data = {
                    "labels": ["A", "B", "C"],
                    "datasets": [{
                        "label": "Test Data",
                        "data": [10, 20, 30],
                        "backgroundColor": ["#ff0000", "#00ff00", "#0000ff"]
                    }]
                }
                
                chart = create_pie_chart(data, "Test Pie Chart")
                assert chart.startswith("data:image/png;base64,")
                assert "encoded_test_image_data" in chart
                
                # Verify matplotlib calls
                mock_figure.assert_called_once()
                mock_pie.assert_called_once()
                mock_title.assert_called_once_with("Test Pie Chart")
                mock_axis.assert_called_once_with('equal')
                mock_savefig.assert_called_once()
                mock_close.assert_called_once()

    @patch("app.utils.visualization.create_bar_chart")
    @patch("app.utils.visualization.create_line_chart")
    @patch("app.utils.visualization.create_pie_chart")
    @patch("app.utils.visualization.create_scatter_chart")
    def test_create_chart(self, mock_scatter, mock_pie, mock_line, mock_bar):
        """Test chart creation function"""
        # Set up mock returns
        mock_bar.return_value = "bar_chart_image"
        mock_line.return_value = "line_chart_image"
        mock_pie.return_value = "pie_chart_image"
        mock_scatter.return_value = "scatter_chart_image"
        
        # Test data
        data = {
            "labels": ["A", "B", "C"],
            "datasets": [{
                "label": "Test Data",
                "data": [10, 20, 30]
            }]
        }
        
        # Test different chart types
        assert create_chart(data, "bar", "Test Chart") == "bar_chart_image"
        assert create_chart(data, "line", "Test Chart") == "line_chart_image"
        assert create_chart(data, "pie", "Test Chart") == "pie_chart_image"
        assert create_chart(data, "scatter", "Test Chart") == "scatter_chart_image"
        
        # Test default (should be bar)
        assert create_chart(data, "unknown", "Test Chart") == "bar_chart_image"
        
        # Verify calls
        mock_bar.assert_called_with(data, "Test Chart")
        mock_line.assert_called_with(data, "Test Chart")
        mock_pie.assert_called_with(data, "Test Chart")
        mock_scatter.assert_called_with(data, "Test Chart")

    def test_create_table_html(self):
        """Test HTML table creation function"""
        # Test with normal data
        headers = ["Column 1", "Column 2", "Column 3"]
        rows = [
            ["A", "10", "20"],
            ["B", "30", "40"],
            ["C", "50", "60"]
        ]
        
        html = create_table_html(headers, rows)
        assert "<table" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "<th>Column 1</th>" in html
        assert "<td>A</td>" in html
        
        # Test with empty data
        empty_html = create_table_html([], [])
        assert "No data available" in empty_html

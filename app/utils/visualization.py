"""
Visualization utilities for research tools.
"""
import logging
import io
import base64
import re
from typing import List, Dict, Any, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from app.utils.nlp import extract_numeric_data, extract_tabular_data

# Initialize logging
logger = logging.getLogger(__name__)

# Set default style
plt.style.use('ggplot')


def extract_chart_data(text: str) -> Dict[str, Any]:
    """
    Extract data from text for chart visualization.
    
    Args:
        text: The input text
        
    Returns:
        Dictionary with labels and datasets
    """
    # Extract numeric data using NLP utility
    data = extract_numeric_data(text)
    
    if not data["labels"] or not data["values"]:
        # If no data was found, return empty structure
        return {
            "labels": [],
            "datasets": [{
                "label": "No Data Found",
                "data": []
            }]
        }
    
    return {
        "labels": data["labels"],
        "datasets": [{
            "label": "Data",
            "data": data["values"],
            "backgroundColor": generate_colors(len(data["values"])),
            "borderColor": generate_colors(len(data["values"]), 0.8)
        }]
    }


def extract_table_data(text: str) -> Dict[str, Any]:
    """
    Extract data from text for table visualization.
    
    Args:
        text: The input text
        
    Returns:
        Dictionary with headers and rows
    """
    # Extract tabular data using NLP utility
    return extract_tabular_data(text)


def generate_colors(n: int, alpha: float = 0.6) -> List[str]:
    """
    Generate a list of n colors with the specified alpha.
    
    Args:
        n: Number of colors to generate
        alpha: Alpha value for colors
        
    Returns:
        List of color strings in rgba format
    """
    # Use a colormap from matplotlib
    cmap = plt.cm.get_cmap('tab10')
    
    colors = []
    for i in range(n):
        rgba = cmap(i % 10)
        colors.append(f'rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {alpha})')
    
    return colors


def create_bar_chart(data: Dict[str, Any], title: str = "Bar Chart") -> str:
    """
    Create a bar chart from the provided data.
    
    Args:
        data: Dictionary with labels and datasets
        title: Chart title
        
    Returns:
        Base64-encoded image
    """
    try:
        labels = data["labels"]
        dataset = data["datasets"][0]
        values = dataset["data"]
        
        if not labels or not values:
            return ""
        
        plt.figure(figsize=(10, 6))
        plt.bar(labels, values, color=dataset.get("backgroundColor", "blue"))
        plt.title(title)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        logger.error(f"Error creating bar chart: {str(e)}")
        return ""


def create_line_chart(data: Dict[str, Any], title: str = "Line Chart") -> str:
    """
    Create a line chart from the provided data.
    
    Args:
        data: Dictionary with labels and datasets
        title: Chart title
        
    Returns:
        Base64-encoded image
    """
    try:
        labels = data["labels"]
        dataset = data["datasets"][0]
        values = dataset["data"]
        
        if not labels or not values:
            return ""
        
        plt.figure(figsize=(10, 6))
        plt.plot(labels, values, marker='o', color=dataset.get("borderColor", "blue"))
        plt.title(title)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        logger.error(f"Error creating line chart: {str(e)}")
        return ""


def create_pie_chart(data: Dict[str, Any], title: str = "Pie Chart") -> str:
    """
    Create a pie chart from the provided data.
    
    Args:
        data: Dictionary with labels and datasets
        title: Chart title
        
    Returns:
        Base64-encoded image
    """
    try:
        labels = data["labels"]
        dataset = data["datasets"][0]
        values = dataset["data"]
        
        if not labels or not values:
            return ""
        
        plt.figure(figsize=(10, 6))
        plt.pie(values, labels=labels, autopct='%1.1f%%', 
                colors=dataset.get("backgroundColor", None))
        plt.title(title)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        logger.error(f"Error creating pie chart: {str(e)}")
        return ""


def create_scatter_chart(data: Dict[str, Any], title: str = "Scatter Plot") -> str:
    """
    Create a scatter plot from the provided data.
    
    Args:
        data: Dictionary with labels and datasets
        title: Chart title
        
    Returns:
        Base64-encoded image
    """
    try:
        labels = data["labels"]
        dataset = data["datasets"][0]
        values = dataset["data"]
        
        if not labels or not values:
            return ""
        
        # For scatter plot, we need x and y values
        # If only one dataset is provided, use indices as x-values
        x = range(len(values))
        y = values
        
        plt.figure(figsize=(10, 6))
        plt.scatter(x, y, color=dataset.get("backgroundColor", "blue"))
        plt.title(title)
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.tight_layout()
        
        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        
        # Encode as base64
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        logger.error(f"Error creating scatter chart: {str(e)}")
        return ""


def create_chart(
    data: Dict[str, Any], 
    chart_type: str = "bar", 
    title: str = "Chart"
) -> str:
    """
    Create a chart of the specified type from the provided data.
    
    Args:
        data: Dictionary with labels and datasets
        chart_type: Type of chart (bar, line, pie, scatter)
        title: Chart title
        
    Returns:
        Base64-encoded image
    """
    chart_type = chart_type.lower()
    
    if chart_type == "bar":
        return create_bar_chart(data, title)
    elif chart_type == "line":
        return create_line_chart(data, title)
    elif chart_type == "pie":
        return create_pie_chart(data, title)
    elif chart_type == "scatter":
        return create_scatter_chart(data, title)
    else:
        logger.warning(f"Unsupported chart type: {chart_type}, defaulting to bar chart")
        return create_bar_chart(data, title)


def create_table_html(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Create an HTML table from the provided headers and rows.
    
    Args:
        headers: List of column headers
        rows: List of rows, each containing a list of cell values
        
    Returns:
        HTML table as a string
    """
    if not headers or not rows:
        return "<table><tr><td>No data available</td></tr></table>"
    
    html = "<table border='1' cellpadding='5' cellspacing='0'>"
    
    # Add header row
    html += "<thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead>"
    
    # Add data rows
    html += "<tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</tbody>"
    
    html += "</table>"
    
    return html

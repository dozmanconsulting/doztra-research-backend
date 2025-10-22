# Research Tools API

This module provides a set of APIs for research-related tasks such as text analysis, citation generation, data visualization, and reference management.

## Endpoints

### 1. Text Analysis API

**Endpoint:** `/api/research/analyze`
**Method:** POST
**Description:** Analyzes text content to extract insights, summaries, or key points

#### Request Body:
```json
{
  "text": "String containing the text to analyze",
  "analysis_type": "summary | sentiment | key_points | full"
}
```

#### Response:
```json
{
  "analysis": {
    "summary": "Condensed version of the text highlighting key information",
    "sentiment": {
      "score": 0.75,
      "label": "Positive"
    },
    "key_points": [
      "First key point extracted from the text",
      "Second key point extracted from the text",
      "..."
    ],
    "entities": [
      {
        "name": "Entity name",
        "type": "person | organization | location | etc.",
        "relevance": 0.85
      }
    ],
    "topics": [
      {
        "name": "Topic name",
        "score": 0.92
      }
    ]
  }
}
```

### 2. Citation Generation API

**Endpoint:** `/api/research/citations`
**Method:** POST
**Description:** Generates in-line citations and references for a given text

#### Request Body:
```json
{
  "text": "String containing the text to generate citations for",
  "style": "apa | mla | chicago | harvard | ieee"
}
```

#### Response:
```json
{
  "inline_citations": [
    {
      "text": "Original text segment",
      "citation": "Author, Year",
      "confidence": 0.85
    }
  ],
  "references": [
    {
      "id": "unique-reference-id",
      "reference": "Formatted reference string according to the specified style",
      "url": "Optional URL to the source",
      "doi": "Optional DOI if available",
      "year": "Publication year",
      "authors": ["Author 1", "Author 2", "..."],
      "title": "Title of the work",
      "journal": "Journal name if applicable",
      "publisher": "Publisher name if applicable"
    }
  ]
}
```

### 3. Visualization API

**Endpoint:** `/api/research/visualize`
**Method:** POST
**Description:** Generates visualizations (charts or tables) from text data

#### Request Body:
```json
{
  "text": "String containing the text with data to visualize",
  "data_type": "table | chart",
  "chart_type": "bar | line | pie | scatter"
}
```

#### Response:
```json
{
  "visualization_type": "table | chart",
  "title": "Generated title for the visualization",
  "description": "Description of what the visualization shows",
  "chart_type": "bar | line | pie | scatter",
  "chart_data": {
    "labels": ["Label 1", "Label 2", "..."],
    "datasets": [
      {
        "label": "Dataset label",
        "data": [10, 20, 30, 40],
        "backgroundColor": ["#ff6384", "#36a2eb", "..."],
        "borderColor": ["#ff6384", "#36a2eb", "..."]
      }
    ]
  },
  "table_data": {
    "headers": ["Column 1", "Column 2", "..."],
    "rows": [
      ["Row 1, Col 1", "Row 1, Col 2", "..."],
      ["Row 2, Col 1", "Row 2, Col 2", "..."]
    ]
  },
  "image_url": "URL to a generated chart image if applicable"
}
```

### 4. References API

**Endpoint:** `/api/research/references`
**Method:** POST
**Description:** Generates references in a specific citation style

#### Request Body:
```json
{
  "text": "String containing the text to generate references for",
  "style": "apa | mla | chicago | harvard | ieee",
  "count": 5
}
```

#### Response:
```json
{
  "references": [
    {
      "id": "unique-reference-id",
      "reference": "Formatted reference string according to the specified style",
      "url": "Optional URL to the source",
      "doi": "Optional DOI if available",
      "year": "Publication year",
      "authors": ["Author 1", "Author 2", "..."],
      "title": "Title of the work",
      "journal": "Journal name if applicable",
      "publisher": "Publisher name if applicable"
    }
  ]
}
```

## Implementation Details

The Research Tools API uses a combination of:

1. **Natural Language Processing (NLP)** techniques for text analysis, entity extraction, and keyword identification
2. **Data Visualization** libraries for generating charts and tables
3. **Citation Management** utilities for formatting references according to different citation styles
4. **OpenAI's GPT models** as a fallback for more complex analysis tasks

The implementation follows a hybrid approach, using local processing where possible for better performance and falling back to AI-based processing for more complex tasks.

## Error Handling

All endpoints include robust error handling with appropriate HTTP status codes:

- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Server-side processing error

## Authentication

All endpoints require authentication using a valid JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Rate Limiting

These endpoints are subject to rate limiting based on the user's subscription plan. Please refer to the API documentation for specific limits.


EMAIL="qa+klaviyo-$(date +%s)@example.com"
curl -i -X POST https://doztra-research.onrender.com/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"'"$EMAIL"'","name":"QA Klaviyo","password":"StrongPass123!"}'

  curl -i -X POST https://doztra-research.onrender.com/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"shedrackaji.aji@gmail.com","name":"Dozie Aji","password":"StrongPass123!"}'


EMAIL="shedrack+$(date +%s)@dozmanconsulting.com"
curl -i -X POST https://doztra-research.onrender.com/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"'"$EMAIL"'","name":"Dozie Aji","password":"StrongPass123!"}'
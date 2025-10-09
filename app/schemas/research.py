from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisType(str, Enum):
    summary = "summary"
    sentiment = "sentiment"
    key_points = "key_points"
    full = "full"


class CitationStyle(str, Enum):
    apa = "apa"
    mla = "mla"
    chicago = "chicago"
    harvard = "harvard"
    ieee = "ieee"


class ChartType(str, Enum):
    bar = "bar"
    line = "line"
    pie = "pie"
    scatter = "scatter"


class DataType(str, Enum):
    table = "table"
    chart = "chart"


class VisualizationType(str, Enum):
    table = "table"
    chart = "chart"


# Request Models
class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., description="Text content to analyze")
    analysis_type: Optional[AnalysisType] = Field(
        default=AnalysisType.full, 
        description="Type of analysis to perform"
    )


class CitationRequest(BaseModel):
    text: str = Field(..., description="Text content to generate citations for")
    style: Optional[CitationStyle] = Field(
        default=CitationStyle.apa, 
        description="Citation style to use"
    )


class VisualizationRequest(BaseModel):
    text: str = Field(..., description="Text content with data to visualize")
    data_type: Optional[DataType] = Field(
        default=DataType.chart, 
        description="Type of visualization to generate"
    )
    chart_type: Optional[ChartType] = Field(
        default=ChartType.bar, 
        description="Type of chart to generate (if data_type is chart)"
    )


class ReferenceRequest(BaseModel):
    text: str = Field(..., description="Text content to generate references for")
    style: CitationStyle = Field(..., description="Citation style to use")
    count: Optional[int] = Field(
        default=5, 
        description="Number of references to generate",
        ge=1,
        le=20
    )


# Response Models
class SentimentAnalysis(BaseModel):
    score: float = Field(..., description="Sentiment score (-1 to 1)")
    label: str = Field(..., description="Sentiment label")


class Entity(BaseModel):
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type")
    relevance: float = Field(..., description="Relevance score")


class Topic(BaseModel):
    name: str = Field(..., description="Topic name")
    score: float = Field(..., description="Topic relevance score")


class Analysis(BaseModel):
    summary: Optional[str] = None
    sentiment: Optional[SentimentAnalysis] = None
    key_points: Optional[List[str]] = None
    entities: Optional[List[Entity]] = None
    topics: Optional[List[Topic]] = None


class AnalyzeTextResponse(BaseModel):
    analysis: Analysis


class InlineCitation(BaseModel):
    text: str = Field(..., description="Original text segment")
    citation: str = Field(..., description="Citation text")
    confidence: float = Field(..., description="Confidence score")


class Reference(BaseModel):
    id: str = Field(..., description="Unique reference ID")
    reference: str = Field(..., description="Formatted reference string")
    url: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[str] = None
    authors: Optional[List[str]] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None


class CitationResponse(BaseModel):
    inline_citations: List[InlineCitation]
    references: List[Reference]


class ChartDataset(BaseModel):
    label: str
    data: List[float]
    background_color: Optional[List[str]] = Field(None, alias="backgroundColor")
    border_color: Optional[List[str]] = Field(None, alias="borderColor")


class ChartData(BaseModel):
    labels: List[str]
    datasets: List[ChartDataset]


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[Any]]


class VisualizationResponse(BaseModel):
    visualization_type: VisualizationType = Field(..., alias="visualizationType")
    title: Optional[str] = None
    description: Optional[str] = None
    chart_type: Optional[ChartType] = Field(None, alias="chartType")
    chart_data: Optional[ChartData] = Field(None, alias="chartData")
    table_data: Optional[TableData] = Field(None, alias="tableData")
    image_url: Optional[str] = Field(None, alias="imageUrl")


class ReferenceResponse(BaseModel):
    references: List[Reference]

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class Position(BaseModel):
    x: float
    y: float


class Node(BaseModel):
    id: str
    type: str
    position: Position
    confidence: float
    bbox: List[float] = Field(description="Bounding box [x1, y1, x2, y2]")
    width: float
    height: float
    area: float
    parent_id: Optional[str] = None
    children: List[str] = []


class Edge(BaseModel):
    id: str
    source: str
    target: str
    keypoints: List[List[float]] = Field(
        description="Start and end keypoints [[x1,y1], [x2,y2]]"
    )
    cross_boundary: bool = False


class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class ThreatAnalysis(BaseModel):
    category: str = Field(
        description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege"
    )
    severity: str = Field(description="Threat severity: High, Medium, Low")
    affected_components: List[str] = Field(
        description="List of node IDs affected by this threat"
    )
    description: str = Field(description="Description of the threat")
    recommendation: str = Field(description="Mitigation recommendation")


class ThreatSummary(BaseModel):
    total_threats: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]


class StrideAnalysisResult(BaseModel):
    threats: List[ThreatAnalysis]
    summary: ThreatSummary


class Metadata(BaseModel):
    processing_time_ms: float
    model_version: Optional[str]
    total_detections: int
    confidence_threshold: float


class InferenceResponse(BaseModel):
    graph: Graph
    stride_analysis: StrideAnalysisResult
    metadata: Metadata
    visualization: Optional[str] = Field(
        None, description="Base64 encoded image with detections (optional)"
    )

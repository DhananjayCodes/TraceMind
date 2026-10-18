from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

class EvidencePath(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    summary: str
    query_type: str
    confidence: float

class InvestigationRequest(BaseModel):
    incident_id: str
    tenant_id: str = "acme"

class InvestigationResult(BaseModel):
    id: str
    incident_id: str
    status: Literal["complete", "running"]
    summary: str
    suspected_root_cause: str
    confidence: float
    recommended_action: str
    affected_services: list[str]
    owner: str
    evidence_paths: list[EvidencePath]
    historical_precedent: str
    memory_used: list[dict[str, Any]]
    agent_activity: list[dict[str, Any]]
    sources: list[str]

class ActionApproval(BaseModel):
    approved_by: str = Field(min_length=2)

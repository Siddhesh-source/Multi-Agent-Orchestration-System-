from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    description: str
    human_review: bool = False


class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    human_review: bool
    human_review_required: bool
    created_at: datetime
    duration_seconds: Optional[float] = None
    final_output: Optional[str] = None
    confidence_score: Optional[float] = None
    metacognition_feedback: Optional[str] = None
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentLogResponse(BaseModel):
    agent_name: str
    status: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None  # For enhanced agent data (debate, confidence, etc.)

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    human_review_required: bool
    final_output: Optional[str] = None
    confidence_score: Optional[float] = None
    metacognition_feedback: Optional[str] = None
    started_at: Optional[datetime] = None
    agents: List[AgentLogResponse] = []

    class Config:
        from_attributes = True


class TaskListItem(BaseModel):
    id: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    action: str   # "approve" or "reject"
    feedback: str = ""


class MemorySearchResponse(BaseModel):
    id: Optional[str] = None
    task_id: str
    task_description: str
    chunk: str
    content: Optional[str] = None
    score: float
    timestamp: str
    tier: Optional[str] = None  # episodic, semantic, procedural
    memory_type: Optional[str] = None

    class Config:
        from_attributes = True


# Backward compat alias used by existing route stubs
ReviewAction = ApproveRequest

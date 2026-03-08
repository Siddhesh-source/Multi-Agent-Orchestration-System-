from pydantic import BaseModel
from typing import Optional, List
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

    class Config:
        from_attributes = True


class AgentLogResponse(BaseModel):
    agent_name: str
    status: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    human_review_required: bool
    final_output: Optional[str] = None
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
    task_id: str
    task_description: str
    chunk: str
    score: float
    timestamp: str

    class Config:
        from_attributes = True


# Backward compat alias used by existing route stubs
ReviewAction = ApproveRequest

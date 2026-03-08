import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (
    TaskCreate, TaskResponse, TaskListItem,
    TaskStatusResponse, AgentLogResponse, ApproveRequest,
)
from api.dependencies import get_db
from db.database import AsyncSessionLocal
from db.models import Task, AgentLog
from core.orchestrator import TaskOrchestrator

router = APIRouter()

_AGENT_NAMES = ["Planner", "Research", "Executor", "Critic", "Memory"]


# ─── POST /api/task ───────────────────────────────────────────────────
@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    db_task = Task(
        id=task_id,
        description=task.description,
        status="pending",
        human_review=task.human_review,
        created_at=now,
        updated_at=now,
    )
    db.add(db_task)

    for name in _AGENT_NAMES:
        db.add(AgentLog(task_id=task_id, agent_name=name, status="pending"))

    await db.commit()
    await db.refresh(db_task)

    background_tasks.add_task(
        TaskOrchestrator().run,
        task_id,
        task.description,
        task.human_review,
    )

    return TaskResponse(
        id=task_id,
        description=task.description,
        status="pending",
        human_review=task.human_review,
        human_review_required=False,
        created_at=now,
        duration_seconds=None,
        final_output=None,
    )


# ─── GET /api/task/{task_id}/status ──────────────────────────────────
@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    rows = await db.execute(
        select(AgentLog)
        .where(AgentLog.task_id == task_id)
        .order_by(AgentLog.id.asc())
    )
    agents = [
        AgentLogResponse(
            agent_name=a.agent_name,
            status=a.status,
            input_text=a.input_text,
            output_text=a.output_text,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in rows.scalars().all()
    ]

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        human_review_required=task.human_review_required,
        final_output=task.final_output,
        agents=agents,
    )


# ─── POST /api/task/{task_id}/approve ────────────────────────────────
@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    task.human_approved = (body.action == "approve")
    task.human_feedback = body.feedback
    task.human_review_required = False
    task.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "received", "action": body.action}


# ─── GET /tasks (alias for frontend compatibility) ────────────────────
@router.get("", response_model=list[TaskListItem])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(Task).order_by(Task.created_at.desc()).limit(50)
    )
    return [
        TaskListItem(
            id=t.id,
            description=t.description,
            status=t.status,
            created_at=t.created_at,
        )
        for t in rows.scalars().all()
    ]

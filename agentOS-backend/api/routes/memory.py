from fastapi import APIRouter, Query
from api.models import MemorySearchResponse
from memory.chroma_store import chroma_store

router = APIRouter()


# ─── GET /api/memory/search ───────────────────────────────────────────
@router.get("/search", response_model=list[MemorySearchResponse])
async def search_memory(q: str = "", limit: int = Query(50, le=100)):
    # If no query, return all memories
    if not q:
        all_memories = chroma_store.get_all(limit=limit)
        return [
            MemorySearchResponse(
                task_id=m.get("task_id", m.get("id", "")),
                task_description=m.get("task_description", ""),
                chunk=m.get("content", m.get("chunk", "")),
                score=m.get("score", 1.0),
                timestamp=m.get("created_at", m.get("timestamp", "")),
            )
            for m in all_memories
        ]
    
    # Otherwise search by query
    results = await chroma_store.search_by_text(q, limit)
    return [
        MemorySearchResponse(
            task_id=r.get("task_id", ""),
            task_description=r.get("task_description", ""),
            chunk=r.get("chunk", ""),
            score=r.get("score", 0.0),
            timestamp=r.get("timestamp", ""),
        )
        for r in results
    ]


# ─── GET /api/memory/count ────────────────────────────────────────────
@router.get("/count")
async def memory_count():
    return {"count": chroma_store.count()}

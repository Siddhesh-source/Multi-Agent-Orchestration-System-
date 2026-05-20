from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from db.database import init_db
from core.llm import health_check
from api.routes import tasks, memory
from api.routes.files import router as files_router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    gemini_ok = await health_check()
    if gemini_ok:
        print("Gemini API connected.")
    else:
        print("WARNING: Gemini API not responding. Check API key.")
    print("AgentOS API ready.")
    yield


app = FastAPI(title="AgentOS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router,  prefix="/api/task",   tags=["tasks"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(files_router,  prefix="/api/files",  tags=["files"])


@app.get("/")
async def root():
    return {"status": "AgentOS running", "model": settings.GEMINI_MODEL}

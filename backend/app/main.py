from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routers import auth, assessments, quiz, predictions, dashboard, public, teacher, admin
from app.routers import teacher_tools, student_tools, export as export_router
from app.routers import research as research_router
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if not exist
    await init_db()
    yield

app = FastAPI(
    title="PE Assessment Framework",
    description="Big Data–Driven ML Framework for Multi-Dimensional PE Performance Assessment",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(assessments.router)
app.include_router(quiz.router)
app.include_router(predictions.router)
app.include_router(dashboard.router)
app.include_router(public.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(teacher_tools.router)
app.include_router(student_tools.router)
app.include_router(export_router.router)
app.include_router(research_router.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint — returns system status."""
    from app.config import settings

    models_loaded = all(
        os.path.exists(os.path.join(settings.MODEL_DIR, f))
        for f in ["bpnn.pt", "rf.pkl", "xgb.json", "weights.json", "feature_names.json"]
    )

    db_connected = True
    try:
        from app.core.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    return {
        "status": "ok",
        "models_loaded": models_loaded,
        "db": "connected" if db_connected else "disconnected",
    }

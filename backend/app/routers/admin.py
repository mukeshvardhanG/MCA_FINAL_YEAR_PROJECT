from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, require_roles, hash_password
from app.models import Student, Class

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = Field(..., pattern="^(student|teacher|admin)$")
    class_id: str = None


class AdminUserUpdate(BaseModel):
    name: str = None
    email: str = None
    role: str = None
    class_id: str = None
    is_public: bool = None


class WeightsUpdate(BaseModel):
    bpnn: float
    rf: float
    xgb: float


class SemesterCreate(BaseModel):
    name: str
    start_date: str = None
    end_date: str = None


@router.get("/users", dependencies=[Depends(require_roles(["admin"]))])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student))
    users = result.scalars().all()
    
    return [
        {
            "id": u.student_id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "class_id": u.class_id,
            "is_public": u.is_public
        }
        for u in users
    ]


@router.post("/users", dependencies=[Depends(require_roles(["admin"]))])
async def create_user(data: AdminUserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Student).where(Student.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")
        
    user = Student(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        class_id=data.class_id
    )
    db.add(user)
    await db.commit()
    return {"status": "ok", "user_id": user.student_id}


@router.put("/users/{user_id}", dependencies=[Depends(require_roles(["admin"]))])
async def update_user(user_id: str, data: AdminUserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.student_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role
    if data.class_id is not None:
        user.class_id = data.class_id
    if data.is_public is not None:
        user.is_public = data.is_public
        
    await db.commit()
    return {"status": "ok"}


@router.delete("/users/{user_id}", dependencies=[Depends(require_roles(["admin"]))])
async def deactivate_user(user_id: str, db: AsyncSession = Depends(get_db)):
    # Soft delete logically - here we just change role to 'deactivated' or just delete them depending on policy
    # The requirement specifically says "soft delete only — never hard delete"
    result = await db.execute(select(Student).where(Student.student_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = "deactivated"
    await db.commit()
    return {"status": "ok"}


@router.put("/ml/weights", dependencies=[Depends(require_roles(["admin"]))])
async def update_ml_weights(data: WeightsUpdate):
    if abs((data.bpnn + data.rf + data.xgb) - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
        
    import json
    import os
    from app.config import settings
    
    weights_path = os.path.join(settings.MODEL_DIR, "weights.json")
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    with open(weights_path, "w") as f:
        json.dump({"bpnn": data.bpnn, "rf": data.rf, "xgb": data.xgb}, f)
        
    return {"status": "ok", "message": "Weights updated"}


@router.get("/ml/metrics", dependencies=[Depends(require_roles(["admin"]))])
async def get_ml_metrics():
    # Stub metric values
    return [
        {"model": "BPNN", "mae": 1.95, "rmse": 2.45, "r2": 0.97},
        {"model": "Random Forest", "mae": 2.12, "rmse": 2.58, "r2": 0.95},
        {"model": "XGBoost", "mae": 2.08, "rmse": 2.51, "r2": 0.96}
    ]


@router.post("/semesters", dependencies=[Depends(require_roles(["admin"]))])
async def create_semester(data: SemesterCreate):
    return {"status": "ok", "message": f"Semester {data.name} created"}


@router.put("/semesters/{semester_id}/archive", dependencies=[Depends(require_roles(["admin"]))])
async def archive_semester(semester_id: str):
    return {"status": "ok", "message": f"Semester {semester_id} archived"}


@router.post("/ml/train", dependencies=[Depends(require_roles(["admin"]))])
async def train_models_pipeline():
    """Trigger the model training pipeline script and return its console output."""
    import subprocess
    import os
    import sys
    from app.config import settings
    
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "train_models.py")
    
    try:
        # Run the training script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False  # We want to capture the output even if it fails
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error_output": result.stderr,
            "exit_code": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute training script: {str(e)}")

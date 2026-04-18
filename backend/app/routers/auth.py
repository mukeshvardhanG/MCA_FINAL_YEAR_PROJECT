from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models import Student
from app.schemas import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    result = await db.execute(select(Student).where(Student.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    student = Student(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        age=req.age,
        gender=req.gender,
        grade_level=req.grade_level,
        role="student",  # Force all public registrations to student
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)

    token = create_access_token({
        "sub": str(student.student_id), 
        "email": student.email,
        "role": student.role,
        "class_id": str(student.class_id) if student.class_id else None
    })
    return AuthResponse(student_id=str(student.student_id), token=token, name=student.name, role=student.role)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.email == req.email))
    student = result.scalar_one_or_none()
    if not student or not verify_password(req.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "sub": str(student.student_id), 
        "email": student.email,
        "role": student.role,
        "class_id": str(student.class_id) if student.class_id else None
    })
    return AuthResponse(student_id=str(student.student_id), token=token, name=student.name, role=student.role or "student")


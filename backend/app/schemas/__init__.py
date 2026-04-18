from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


# ─── AUTH ────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str = Field(..., max_length=120)
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=6)
    age: int = Field(..., ge=10, le=30)
    gender: str = Field(..., pattern="^(M|F|Other)$")
    grade_level: int = Field(..., ge=1, le=12)

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    student_id: str
    token: str
    name: str
    role: str = "student"


# ─── ASSESSMENT ──────────────────────────────────────────────
class AssessmentCreate(BaseModel):
    semester_id: str = "2025-S2"
    running_speed_100m: float = Field(..., ge=9.0, le=25.0)
    endurance_1500m: float = Field(..., ge=4.0, le=15.0)
    # New Tier 1 inputs
    push_ups: Optional[int] = Field(default=0, ge=0, le=200)
    squats: Optional[int] = Field(default=0, ge=0, le=200)
    sit_ups: Optional[int] = Field(default=0, ge=0, le=200)
    height_cm: Optional[float] = Field(default=170.0, ge=100, le=250)
    weight_kg: Optional[float] = Field(default=65.0, ge=20, le=200)
    # Computed by frontend
    strength_score: float = Field(..., ge=0, le=100)
    bmi: float = Field(..., ge=10.0, le=60.0)
    reaction_time_ms: float = Field(..., ge=100, le=1000)
    # New integrated physical tests
    plank_hold_seconds: float = Field(default=0.0, ge=0, le=600)
    breath_hold_seconds: float = Field(default=0.0, ge=0, le=300)
    # Deprecated — kept optional for backward compatibility
    flexibility_score: float = Field(default=0.0, ge=0, le=100)
    coordination_score: float = Field(default=0.0, ge=0, le=100)
    physical_progress_index: float = Field(default=0.0, ge=-20, le=25)
    skill_acquisition_speed: float = Field(default=5.0, ge=1, le=10)

class AssessmentResponse(BaseModel):
    assessment_id: str
    student_id: str
    assessment_date: str
    semester_id: Optional[str] = None
    is_complete: bool = False
    running_speed_100m: Optional[float] = None
    endurance_1500m: Optional[float] = None
    flexibility_score: Optional[float] = None
    strength_score: Optional[float] = None
    bmi: Optional[float] = None
    coordination_score: Optional[float] = None
    reaction_time_ms: Optional[float] = None
    physical_progress_index: Optional[float] = None
    skill_acquisition_speed: Optional[float] = None
    plank_hold_seconds: Optional[float] = None
    breath_hold_seconds: Optional[float] = None
    motivation_score: Optional[float] = None
    self_confidence_score: Optional[float] = None
    stress_management_score: Optional[float] = None
    goal_orientation_score: Optional[float] = None
    mental_resilience_score: Optional[float] = None
    quiz_tier_reached: Optional[int] = 1
    teamwork_score: Optional[float] = None
    participation_score: Optional[float] = None
    communication_score: Optional[float] = None
    leadership_score: Optional[float] = None
    peer_collaboration_score: Optional[float] = None
    social_tier_reached: Optional[int] = 1


# ─── QUIZ ────────────────────────────────────────────────────
class QuizAnswer(BaseModel):
    question_id: str
    answer: str

class QuizSubmitRequest(BaseModel):
    assessment_id: str
    quiz_type: str = Field(..., pattern="^(psychological|social)$")
    tier: int = Field(..., ge=1, le=2)
    responses: List[QuizAnswer]

class QuizTierResult(BaseModel):
    tier1_score: Optional[float] = None
    tier2_score: Optional[float] = None
    final_score: Optional[float] = None
    positivity_ratio: Optional[float] = None
    requires_tier2: bool = False
    tier_reached: int = 1
    inconsistency_detected: bool = False


# ─── PREDICTION ──────────────────────────────────────────────
class PredictionResponse(BaseModel):
    prediction_id: str
    final_score: float
    performance_grade: str
    bpnn_score: float
    rf_score: float
    xgb_score: float
    confidence: Optional[float] = None
    agreement: Optional[float] = None
    status: str = "complete"

class PredictionStatusResponse(BaseModel):
    prediction_id: str
    status: str
    final_score: Optional[float] = None
    performance_grade: Optional[str] = None


# ─── PFI ─────────────────────────────────────────────────────
class PFIItem(BaseModel):
    feature_name: str
    importance_score: float
    rank: int
    std_dev: float = 0.0


# ─── INSIGHT ─────────────────────────────────────────────────
class InsightResponse(BaseModel):
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    action_steps: List[str]
    youtube_recommendations: List[str] = []
    psych_guidance: Optional[str] = None
    motivation: Optional[str] = None


# ─── DASHBOARD ───────────────────────────────────────────────
class RadarData(BaseModel):
    physical_avg: float
    psychological_avg: float
    social_avg: float
    cognitive_avg: float = 0.0
    technical_avg: float = 0.0
    behavioral_avg: float = 0.0

class TrendPoint(BaseModel):
    semester: str
    score: float

class DashboardResponse(BaseModel):
    current: Optional[PredictionResponse] = None
    assessment_date: Optional[str] = None
    radar: Optional[RadarData] = None
    trend: List[TrendPoint] = []
    pfi: List[PFIItem] = []
    insight: Optional[InsightResponse] = None
    class_avg_score: Optional[float] = None
    percentile_rank: Optional[float] = None


# ─── PUBLIC PROFILE ──────────────────────────────────────────
class PublicProfileResponse(BaseModel):
    name: str
    performance_grade: Optional[str] = None
    final_score: Optional[float] = None
    radar: Optional[RadarData] = None
    pfi_top5: List[PFIItem] = []
    ai_summary: Optional[str] = None


# ─── STUDENT REPORT ──────────────────────────────────────────
class StudentReportResponse(BaseModel):
    student_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    grade_level: Optional[int] = None
    assessment_date: Optional[str] = None
    semester_id: Optional[str] = None
    # Scores
    final_score: Optional[float] = None
    performance_grade: Optional[str] = None
    bpnn_score: Optional[float] = None
    rf_score: Optional[float] = None
    xgb_score: Optional[float] = None
    # Category averages
    radar: Optional[RadarData] = None
    # Feature importance
    pfi: List[PFIItem] = []
    # AI Insight
    insight: Optional[InsightResponse] = None
    # Comparison with base paper
    comparison: Optional[dict] = None


# ─── ATTENDANCE ──────────────────────────────────────────────
class AttendanceCreate(BaseModel):
    student_id: str
    date: str  # YYYY-MM-DD
    status: str = Field(default="present", pattern="^(present|absent|late)$")

class AttendanceBulkCreate(BaseModel):
    records: List[AttendanceCreate]

class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    student_name: Optional[str] = None
    date: str
    status: str
    attendance_rate: Optional[float] = None


# ─── TEACHER NOTES ───────────────────────────────────────────
class TeacherNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="general", pattern="^(feedback|improvement_plan|general)$")

class TeacherNoteResponse(BaseModel):
    id: str
    content: str
    category: str
    teacher_name: Optional[str] = None
    created_at: str


# ─── STUDENT GOALS ───────────────────────────────────────────
class StudentGoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    target_value: Optional[float] = None
    current_value: float = 0.0
    metric_type: Optional[str] = None
    deadline: Optional[str] = None

class StudentGoalUpdate(BaseModel):
    current_value: Optional[float] = None
    status: Optional[str] = Field(default=None, pattern="^(active|completed|expired)$")

class StudentGoalResponse(BaseModel):
    id: str
    title: str
    target_value: Optional[float] = None
    current_value: float
    metric_type: Optional[str] = None
    deadline: Optional[str] = None
    status: str
    progress_pct: Optional[float] = None
    created_at: str


# ─── NOTIFICATIONS ───────────────────────────────────────────
class NotificationCreate(BaseModel):
    user_id: str
    title: str = Field(..., max_length=200)
    message: Optional[str] = None
    type: str = Field(default="info", pattern="^(info|reminder|achievement|alert)$")

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str] = None
    type: str
    is_read: bool
    created_at: str

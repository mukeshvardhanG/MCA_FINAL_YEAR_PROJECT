import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Class(Base):
    __tablename__ = "classes"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(100), nullable=False)
    teacher_id = Column(String(36), ForeignKey("students.student_id"))
    semester = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher = relationship("Student", foreign_keys=[teacher_id])
    students = relationship("Student", foreign_keys="[Student.class_id]", back_populates="enrolled_class")


class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    grade_level = Column(Integer)
    role = Column(String(20), default="student")  # student | teacher | admin
    is_public = Column(Boolean, default=False)
    class_id = Column(String(36), ForeignKey("classes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="student")
    insights = relationship("Insight", back_populates="student")
    enrolled_class = relationship("Class", foreign_keys=[class_id], back_populates="students")


class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(String(36), primary_key=True, default=new_uuid)
    student_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    assessment_date = Column(Date, default=date.today)
    semester_id = Column(String(20))
    # Physical
    running_speed_100m = Column(Float)
    endurance_1500m = Column(Float)
    flexibility_score = Column(Float)
    strength_score = Column(Float)
    bmi = Column(Float)
    coordination_score = Column(Float)
    reaction_time_ms = Column(Float)
    physical_progress_index = Column(Float, default=0.0)
    skill_acquisition_speed = Column(Float, default=5.0)
    # New Tier 1 physical inputs
    push_ups = Column(Integer, default=0)
    squats = Column(Integer, default=0)
    sit_ups = Column(Integer, default=0)
    height_cm = Column(Float, default=170.0)
    weight_kg = Column(Float, default=65.0)
    # Psychological
    motivation_score = Column(Float)
    self_confidence_score = Column(Float)
    stress_management_score = Column(Float)
    goal_orientation_score = Column(Float)
    mental_resilience_score = Column(Float)
    quiz_tier_reached = Column(Integer, default=1)
    # Social
    teamwork_score = Column(Float)
    participation_score = Column(Float)
    communication_score = Column(Float)
    leadership_score = Column(Float)
    peer_collaboration_score = Column(Float)
    social_tier_reached = Column(Integer, default=1)
    # New physical metrics
    plank_hold_seconds = Column(Float, default=0.0)
    breath_hold_seconds = Column(Float, default=0.0)
    # Status
    is_complete = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="assessments")
    predictions = relationship("Prediction", back_populates="assessment")
    quiz_sessions = relationship("QuizSession", back_populates="assessment")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(String(36), primary_key=True, default=new_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.assessment_id"))
    student_id = Column(String(36), ForeignKey("students.student_id"))
    bpnn_score = Column(Float)
    rf_score = Column(Float)
    xgb_score = Column(Float)
    final_score = Column(Float, nullable=False)
    performance_grade = Column(String(2))
    model_version = Column(String(20), default="v1.0")
    status = Column(String(20), default="pending")
    predicted_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="predictions")
    student = relationship("Student", back_populates="predictions")
    pfi_results = relationship("PFIResult", back_populates="prediction", cascade="all, delete-orphan")
    insight = relationship("Insight", back_populates="prediction", uselist=False)


class PFIResult(Base):
    __tablename__ = "pfi_results"

    pfi_id = Column(String(36), primary_key=True, default=new_uuid)
    prediction_id = Column(String(36), ForeignKey("predictions.prediction_id"))
    feature_name = Column(String(80), nullable=False)
    importance_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)

    prediction = relationship("Prediction", back_populates="pfi_results")


class Insight(Base):
    __tablename__ = "insights"

    insight_id = Column(String(36), primary_key=True, default=new_uuid)
    prediction_id = Column(String(36), ForeignKey("predictions.prediction_id"))
    student_id = Column(String(36), ForeignKey("students.student_id"))
    summary = Column(Text)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    action_steps = Column(JSON)
    psych_guidance = Column(Text)
    motivation = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="insight")
    student = relationship("Student", back_populates="insights")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    session_id = Column(String(36), primary_key=True, default=new_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.assessment_id"))
    quiz_type = Column(String(20))
    tier1_responses = Column(JSON)
    tier2_responses = Column(JSON)
    tier1_score = Column(Float)
    tier2_score = Column(Float)
    final_score = Column(Float)
    tier_reached = Column(Integer)
    locked = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    assessment = relationship("Assessment", back_populates="quiz_sessions")


# ─── NEW MODELS ──────────────────────────────────────────────

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True, default=new_uuid)
    student_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    class_id = Column(String(36), ForeignKey("classes.id"))
    date = Column(Date, default=date.today)
    status = Column(String(10), default="present")  # present | absent | late
    linked_assessment_id = Column(String(36), ForeignKey("assessments.assessment_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    enrolled_class = relationship("Class")


class TeacherNote(Base):
    __tablename__ = "teacher_notes"

    id = Column(String(36), primary_key=True, default=new_uuid)
    student_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    teacher_id = Column(String(36), ForeignKey("students.student_id"))
    content = Column(Text, nullable=False)
    category = Column(String(30), default="general")  # feedback | improvement_plan | general
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", foreign_keys=[student_id])
    teacher = relationship("Student", foreign_keys=[teacher_id])


class StudentGoal(Base):
    __tablename__ = "student_goals"

    id = Column(String(36), primary_key=True, default=new_uuid)
    student_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    title = Column(String(200), nullable=False)
    target_value = Column(Float)
    current_value = Column(Float, default=0.0)
    metric_type = Column(String(50))  # push_ups, sprint_time, endurance, etc.
    deadline = Column(Date, nullable=True)
    status = Column(String(20), default="active")  # active | completed | expired
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(String(36), primary_key=True, default=new_uuid)
    student_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    badge_type = Column(String(50), nullable=False)  # first_assessment, streak, strength_champion, etc.
    badge_name = Column(String(100), nullable=False)
    description = Column(String(255))
    earned_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("students.student_id", ondelete="CASCADE"))
    title = Column(String(200), nullable=False)
    message = Column(Text)
    type = Column(String(30), default="info")  # info | reminder | achievement | alert
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Student")


# ─── RESEARCH-GRADE EXPERIMENT TABLES ──────────────────────────

class ErrorLog(Base):
    """Stores worst-case and best-case prediction records for auditing."""
    __tablename__ = "error_logs"

    id             = Column(String(36), primary_key=True, default=new_uuid)
    run_id         = Column(String(36), nullable=False)       # experiment run UUID
    dataset_type   = Column(String(20), default="synthetic")  # synthetic | real
    model_name     = Column(String(40), nullable=False)       # Ensemble | XGBoost | etc.
    case_type      = Column(String(10), nullable=False)       # best | worst
    y_true         = Column(Float, nullable=False)
    y_pred         = Column(Float, nullable=False)
    abs_error      = Column(Float, nullable=False)
    rank           = Column(Integer)                          # rank within top-10
    recorded_at    = Column(DateTime, default=datetime.utcnow)


class LLMEvaluation(Base):
    """Stores automated quality scores for generated student insights."""
    __tablename__ = "llm_evaluations"

    id               = Column(String(36), primary_key=True, default=new_uuid)
    run_id           = Column(String(36), nullable=False)
    case_label       = Column(String(100), nullable=False)    # e.g. "High Performer (Grade A)"
    performance_grade = Column(String(2))
    final_score      = Column(Float)
    relevance_score  = Column(Float)
    correctness_score = Column(Float)
    usefulness_score  = Column(Float)
    avg_score        = Column(Float)
    n_action_steps   = Column(Integer)
    has_psych_guidance = Column(Boolean, default=False)
    evaluated_at     = Column(DateTime, default=datetime.utcnow)


class ExperimentResult(Base):
    """Stores structured experiment metric outputs for reproducibility."""
    __tablename__ = "experiment_results"

    id             = Column(String(36), primary_key=True, default=new_uuid)
    run_id         = Column(String(36), nullable=False)
    experiment_name = Column(String(80), nullable=False)      # e.g. "residual_analysis"
    dataset_type   = Column(String(20), default="synthetic")  # synthetic | real | both
    model_name     = Column(String(40), nullable=True)        # BPNN | RF | XGBoost | Ensemble | N/A
    metric_key     = Column(String(60), nullable=False)       # e.g. "r2_score", "mean_residual"
    metric_value   = Column(Float, nullable=True)
    metric_str     = Column(String(255), nullable=True)       # for string-type results
    run_at         = Column(DateTime, default=datetime.utcnow)


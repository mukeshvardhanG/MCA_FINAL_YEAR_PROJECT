-- PE Assessment MVP — Database Schema
-- Run: psql -U postgres -d pe_assessment -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. STUDENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    student_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(120) NOT NULL,
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    age             INTEGER CHECK (age BETWEEN 10 AND 30),
    gender          VARCHAR(10) CHECK (gender IN ('M','F','Other')),
    grade_level     INTEGER CHECK (grade_level BETWEEN 1 AND 12),
    is_public       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. ASSESSMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id               UUID REFERENCES students(student_id) ON DELETE CASCADE,
    assessment_date          DATE NOT NULL DEFAULT CURRENT_DATE,
    semester_id              VARCHAR(20),
    -- Physical indicators
    running_speed_100m       FLOAT CHECK (running_speed_100m > 0),
    endurance_1500m          FLOAT CHECK (endurance_1500m > 0),
    flexibility_score        FLOAT,
    strength_score           FLOAT,
    bmi                      FLOAT,
    coordination_score       FLOAT,
    reaction_time_ms         FLOAT,
    physical_progress_index  FLOAT DEFAULT 0.0,
    skill_acquisition_speed  FLOAT DEFAULT 5.0,
    -- Psychological indicators (from quiz)
    motivation_score         FLOAT CHECK (motivation_score BETWEEN 0 AND 10),
    self_confidence_score    FLOAT CHECK (self_confidence_score BETWEEN 0 AND 10),
    stress_management_score  FLOAT CHECK (stress_management_score BETWEEN 0 AND 10),
    goal_orientation_score   FLOAT CHECK (goal_orientation_score BETWEEN 0 AND 10),
    mental_resilience_score  FLOAT CHECK (mental_resilience_score BETWEEN 0 AND 10),
    quiz_tier_reached        INTEGER DEFAULT 1 CHECK (quiz_tier_reached IN (1,2)),
    -- Social indicators (from quiz)
    teamwork_score           FLOAT CHECK (teamwork_score BETWEEN 0 AND 10),
    participation_score      FLOAT CHECK (participation_score BETWEEN 0 AND 10),
    communication_score      FLOAT CHECK (communication_score BETWEEN 0 AND 10),
    leadership_score         FLOAT CHECK (leadership_score BETWEEN 0 AND 10),
    peer_collaboration_score FLOAT CHECK (peer_collaboration_score BETWEEN 0 AND 10),
    social_tier_reached      INTEGER DEFAULT 1 CHECK (social_tier_reached IN (1,2)),
    -- Status
    is_complete              BOOLEAN DEFAULT FALSE,
    created_at               TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. PREDICTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id      UUID REFERENCES assessments(assessment_id),
    student_id         UUID REFERENCES students(student_id),
    bpnn_score         FLOAT,
    rf_score           FLOAT,
    xgb_score          FLOAT,
    final_score        FLOAT NOT NULL,
    performance_grade  VARCHAR(2),
    model_version      VARCHAR(20) DEFAULT 'v1.0',
    status             VARCHAR(20) DEFAULT 'pending',
    predicted_at       TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. PFI RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS pfi_results (
    pfi_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id    UUID REFERENCES predictions(prediction_id),
    feature_name     VARCHAR(80) NOT NULL,
    importance_score FLOAT NOT NULL,
    rank             INTEGER NOT NULL
);

-- ============================================================
-- 5. INSIGHTS (Groq API output)
-- ============================================================
CREATE TABLE IF NOT EXISTS insights (
    insight_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id   UUID REFERENCES predictions(prediction_id),
    student_id      UUID REFERENCES students(student_id),
    summary         TEXT,
    strengths       JSONB,
    weaknesses      JSONB,
    action_steps    JSONB,
    psych_guidance  TEXT,
    motivation      TEXT,
    generated_at    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 6. QUIZ SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS quiz_sessions (
    session_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id    UUID REFERENCES assessments(assessment_id),
    quiz_type        VARCHAR(20) CHECK (quiz_type IN ('psychological','social')),
    tier1_responses  JSONB,
    tier2_responses  JSONB,
    tier1_score      FLOAT,
    tier2_score      FLOAT,
    final_score      FLOAT,
    tier_reached     INTEGER,
    completed_at     TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_assessments_student ON assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_predictions_student ON predictions(student_id);
CREATE INDEX IF NOT EXISTS idx_predictions_assessment ON predictions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_pfi_prediction ON pfi_results(prediction_id);
CREATE INDEX IF NOT EXISTS idx_insights_student ON insights(student_id);
CREATE INDEX IF NOT EXISTS idx_insights_prediction ON insights(prediction_id);
CREATE INDEX IF NOT EXISTS idx_quiz_assessment ON quiz_sessions(assessment_id);

import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { extractErrorMessage } from '../../services/errorUtils';
import TierEscalationBanner from './TierEscalationBanner';
import HumanBenchmarkTests from './HumanBenchmarkTests';
import SocialInteractiveTests from './SocialInteractiveTests';

export default function QuizModal({ assessmentId, quizType, onClose, onComplete }) {
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [tier, setTier] = useState(1);
  const [showEscalation, setShowEscalation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadQuestions(1);
  }, []);

  const loadQuestions = async (t) => {
    try {
      setLoading(true);
      let url = `/quiz/questions?type=${quizType}&tier=${t}`;
      if (t === 2 && assessmentId) url += `&assessment_id=${assessmentId}`;
      const res = await api.get(url);
      setQuestions(res.data);
      setCurrentIdx(0);
      setAnswers({});
    } catch (err) {
      console.error(err);
      alert('Failed to load questions. Check console/network.');
    } finally {
      setLoading(false);
    }
  };

  const currentQ = questions[currentIdx];
  const progress = questions.length ? ((currentIdx + 1) / questions.length) * 100 : 0;

  const handleAnswer = (answer) => {
    setAnswers({ ...answers, [currentQ.question_id]: answer });
  };

  const handleNext = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
    }
  };

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx(currentIdx - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    const responses = Object.entries(answers).map(([qid, ans]) => ({
      question_id: qid,
      answer: String(ans),
    }));

    try {
      const res = await api.post('/quiz/submit', {
        assessment_id: assessmentId,
        quiz_type: quizType,
        tier,
        responses,
      });

      const data = res.data;

      if (tier === 1 && data.requires_tier2) {
        // Always escalate to Tier 2 — show banner then switch to interactive tests
        setShowEscalation(true);
        setTimeout(() => {
          setTier(2);
          setShowEscalation(false);
          setResult(null);
        }, 2500);
      } else {
        setResult(data);
        setTimeout(() => onComplete(data), 1500);
      }
    } catch (err) {
      console.error(err);
      alert(extractErrorMessage(err, 'Quiz submission failed'));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Tier 2 interactive test completion
  const handleInteractiveComplete = async (testResults) => {
    setSubmitting(true);
    try {
      const payload = {
        assessment_id: assessmentId,
        quiz_type: quizType,
      };
      
      if (quizType === 'psychological') {
        payload.memory_score = testResults.memory_score;
        payload.pattern_score = testResults.pattern_score;
      } else {
        payload.emotion_score = testResults.emotion_score;
        payload.trust_score = testResults.trust_score;
      }

      const res = await api.post('/quiz/submit-interactive', payload);
      setResult(res.data);
      setTimeout(() => onComplete(res.data), 1500);
    } catch (err) {
      console.error(err);
      alert(extractErrorMessage(err, 'Failed to submit interactive test results'));
    } finally {
      setSubmitting(false);
    }
  };

  const allAnswered = questions.length > 0 && Object.keys(answers).length === questions.length;

  if (loading && tier === 1) {
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="loading-overlay"><div className="spinner"></div><p>Loading questions...</p></div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={tier === 2 && !showEscalation && !result ? { maxWidth: 620 } : {}}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: '1.2rem' }}>
            {quizType === 'psychological' ? '🧠' : '🤝'} {quizType.charAt(0).toUpperCase() + quizType.slice(1)} Quiz
            <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.85rem', marginLeft: 8 }}>
              {tier === 1 ? 'Tier 1 — Questions' : 'Tier 2 — Interactive Tests'}
            </span>
          </h2>
          <button className="btn btn-sm btn-secondary" onClick={onClose}>✕</button>
        </div>

        {showEscalation && <TierEscalationBanner />}

        {result && !showEscalation && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <p style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--accent-success)' }}>
              ✅ {tier === 2 ? 'Interactive Tests' : 'Quiz'} Complete!
            </p>
            <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>
              Final Score: {result.final_score ?? result.tier1_score}/10 (Tier {result.tier_reached})
            </p>
          </div>
        )}

        {/* Tier 2: Interactive Tests */}
        {tier === 2 && !showEscalation && !result && (
          quizType === 'psychological' ? (
            <HumanBenchmarkTests
              quizType={quizType}
              onComplete={handleInteractiveComplete}
            />
          ) : (
            <SocialInteractiveTests
              onComplete={handleInteractiveComplete}
            />
          )
        )}

        {/* Tier 1: Normal Quiz Questions */}
        {tier === 1 && !showEscalation && !result && currentQ && (
          <>
            <div className="quiz-progress">
              <div className="quiz-progress-bar" style={{ width: `${progress}%` }}></div>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: 8 }}>
              Question {currentIdx + 1} of {questions.length}
            </p>

            <p className="quiz-question-text">{currentQ.text}</p>

            {currentQ.question_type === 'likert' && currentQ.options && currentQ.options.map((opt, idx) => (
              <button key={idx}
                className={`quiz-option ${answers[currentQ.question_id] === String(idx + 1) ? 'selected' : ''}`}
                onClick={() => handleAnswer(String(idx + 1))}>
                {opt}
              </button>
            ))}

            {currentQ.question_type === 'mcq' && currentQ.options && currentQ.options.map((opt, idx) => (
              <button key={idx}
                className={`quiz-option ${answers[currentQ.question_id] === String(idx) ? 'selected' : ''}`}
                onClick={() => handleAnswer(String(idx))}>
                {opt}
              </button>
            ))}

            {currentQ.question_type === 'short_answer' && (
              <>
                <textarea className="quiz-textarea"
                  placeholder="Type your answer here..."
                  value={answers[currentQ.question_id] || ''}
                  onChange={(e) => handleAnswer(e.target.value)}
                />
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 8, fontStyle: 'italic' }}>
                  💡 Your response will be securely analyzed by our AI engine to provide personalized insights.
                </p>
              </>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
              <button className="btn btn-secondary btn-sm" onClick={handlePrev} disabled={currentIdx === 0}>← Previous</button>
              {currentIdx < questions.length - 1 ? (
                <button className="btn btn-primary btn-sm" onClick={handleNext}
                  disabled={!answers[currentQ.question_id]}>Next →</button>
              ) : (
                <button className="btn btn-primary btn-sm" onClick={handleSubmit}
                  disabled={!allAnswered || submitting}>
                  {submitting ? <span className="spinner" style={{ width: 16, height: 16 }}></span> : 'Submit Tier 1'}
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}


import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useChartData } from '../hooks/useChartData';
import { usePrediction } from '../hooks/usePrediction';
import StatsSummaryPanel from '../components/assessment/StatsSummaryPanel';
import PhysicalMetricsForm from '../components/assessment/PhysicalMetricsForm';
import PrivacyTogglePanel from '../components/assessment/PrivacyTogglePanel';
import RadarChart from '../components/charts/RadarChart';
import PerformanceTrendLine from '../components/charts/PerformanceTrendLine';
import PFIBarChart from '../components/charts/PFIBarChart';
import ProgressDeltaPanel from '../components/charts/ProgressDeltaPanel';
import AIInsightCard from '../components/insights/AIInsightCard';
import QuizModal from '../components/quiz/QuizModal';
import GoalSettingPanel from '../components/student/GoalSettingPanel';
import BadgeDisplay from '../components/student/BadgeDisplay';
import api from '../services/api';

import { useNavigate } from 'react-router-dom';

// ─── Demo / Sample Data ─────────────────────────────────────────
const DEMO_RADAR = [
  { subject: 'Physical', value: 7.2, fullMark: 10 },
  { subject: 'Psychological', value: 8.0, fullMark: 10 },
  { subject: 'Social', value: 6.5, fullMark: 10 },
  { subject: 'Cognitive', value: 7.8, fullMark: 10 },
  { subject: 'Technical', value: 6.9, fullMark: 10 },
  { subject: 'Behavioral', value: 7.4, fullMark: 10 },
];

const DEMO_TREND = [
  { name: '2024-S1', score: 62.4 },
  { name: '2024-S2', score: 68.1 },
  { name: '2025-S1', score: 74.5 },
  { name: '2025-S2', score: 79.3 },
];

const DEMO_PFI = [
  { name: 'Motivation Level', importance: 0.6307, error: 0.0946 },
  { name: 'Class Participation', importance: 0.5960, error: 0.0894 },
  { name: 'Goal Orientation', importance: 0.5187, error: 0.0778 },
  { name: 'Peer Collaboration', importance: 0.4407, error: 0.0661 },
  { name: 'Sprint Speed (100m)', importance: 0.4176, error: 0.0626 },
  { name: 'Coordination', importance: 0.3805, error: 0.0571 },
  { name: 'Self-Confidence', importance: 0.3274, error: 0.0491 },
  { name: 'Reaction Time', importance: 0.3202, error: 0.0480 },
  { name: 'Teamwork', importance: 0.2872, error: 0.0431 },
  { name: 'Physical Progress', importance: 0.2737, error: 0.0411 },
].reverse();

const DEMO_INSIGHT = {
  summary: 'Based on your assessment, you demonstrate strong psychological resilience and above-average physical fitness. Focus areas include social collaboration and sprint speed improvement.',
  strengths: [
    'High motivation and goal orientation scores',
    'Consistent improvement across semesters',
    'Above-average stress management',
  ],
  weaknesses: [
    'Sprint speed could be improved with interval training',
    'Peer collaboration needs active effort in group activities',
  ],
  action_steps: [
    'Add 2 sprint interval sessions per week',
    'Volunteer for team captain roles in PE class',
    'Set measurable weekly fitness goals',
  ],
  psych_guidance: 'Your mental resilience is a key asset. Use visualization techniques before competitive events to channel your focus.',
  motivation: '"The only person you are destined to become is the person you decide to be." — Ralph Waldo Emerson',
};

const DEMO_CURRENT = {
  prediction_id: 'demo',
  final_score: 79.3,
  performance_grade: 'B+',
  bpnn_score: 77.1,
  rf_score: 80.5,
  xgb_score: 80.2,
  status: 'complete',
};

export default function DashboardPage({ user, onLogout }) {
  const { data, loading, error, refetch } = useChartData(user.student_id);
  const prediction = usePrediction();
  const [assessmentId, setAssessmentId] = useState(null);
  const [quizModal, setQuizModal] = useState(null);
  const [psychDone, setPsychDone] = useState(false);
  const [socialDone, setSocialDone] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const navigate = useNavigate();
  const resultsRef = useRef(null);

  const handleMetricsSubmit = useCallback((id) => {
    setAssessmentId(id);
    setPsychDone(false);
    setSocialDone(false);
    setDemoMode(false);
  }, []);

  const handleQuizComplete = useCallback((result) => {
    if (quizModal?.type === 'psychological') setPsychDone(true);
    if (quizModal?.type === 'social') setSocialDone(true);
    setQuizModal(null);
  }, [quizModal]);

  React.useEffect(() => {
    if (prediction.status === 'complete') {
      // Wait for background prediction to fully save, then refetch and scroll to results
      const timer = setTimeout(async () => {
        await refetch();
        // Scroll to top results after data loads
        if (resultsRef.current) {
          resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [prediction.status, refetch]);

  const handlePredict = async () => {
    if (!assessmentId) return;
    await prediction.triggerPrediction(assessmentId);
  };

  // Determine which data to display: real or demo
  const hasRealData = !!data?.current;
  const showDemo = demoMode && !hasRealData;

  const displayRadar = hasRealData ? data?.radar : (showDemo ? DEMO_RADAR : null);
  const displayTrend = hasRealData ? data?.trend : (showDemo ? DEMO_TREND : null);
  const displayPfi = hasRealData ? data?.pfi : (showDemo ? DEMO_PFI : null);
  const displayInsight = hasRealData ? data?.insight : (showDemo ? DEMO_INSIGHT : null);
  const displayCurrent = hasRealData ? data?.current : (showDemo ? DEMO_CURRENT : null);
  const displayClassAvg = hasRealData ? data?.classAvg : (showDemo ? 72.4 : null);
  const displayPercentile = hasRealData ? data?.percentileRank : (showDemo ? 74.0 : null);

  return (
    <div>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-logo">⚡ PE Assessment</div>
          <div className="navbar-user">
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: 15 }}>Model Version: v1.2 | Last trained: Apr 2026 | Dataset: Hybrid (S + R validation)</span>
            <span>👋 {user.name}</span>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/admin')}>📊 Training Stats</button>
            <PrivacyTogglePanel studentId={user.student_id} />
            <button className="btn btn-sm btn-danger" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </nav>

      <div className="dashboard">
        {error && (
          <div style={{ background: 'var(--accent-danger)', color: 'white', padding: 16, borderRadius: 8, marginBottom: 16 }}>
            <h3>Error loading dashboard data</h3>
            <p>{String(error)}</p>
          </div>
        )}
        <div className="dashboard-header">
          <h1>Student Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            {data?.assessmentDate ? `Last assessment: ${data.assessmentDate}` : 'No assessments yet — submit physical metrics to begin'}
          </p>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-secondary" onClick={() => window.print()} style={{ marginTop: 8 }}>📄 Download Report (PDF)</button>
            {!hasRealData && !demoMode && (
              <button
                className="btn btn-primary"
                onClick={() => setDemoMode(true)}
                style={{ marginTop: 8, background: 'linear-gradient(135deg, #6366f1, #06b6d4)', border: 'none' }}
              >
                ✨ Try Demo Mode
              </button>
            )}
          </div>
          {showDemo && (
            <div style={{ marginTop: 8, padding: '6px 14px', borderRadius: 8, background: 'rgba(99, 102, 241, 0.12)', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary, #6366f1)', fontWeight: 600 }}>🎯 Demo Mode Active</span>
              <button className="btn btn-sm btn-secondary" onClick={() => setDemoMode(false)}>Exit Demo</button>
            </div>
          )}
        </div>

        {/* Stats */}
        <div ref={resultsRef}>
          <StatsSummaryPanel current={displayCurrent} classAvg={displayClassAvg} percentileRank={displayPercentile} />
        </div>

        {/* Comparison Stats (Progress Delta) */}
        {!showDemo && hasRealData && <ProgressDeltaPanel refreshTrigger={data?.assessmentDate} />}

        {/* Charts Row */}
        <div className="dashboard-grid">
          <RadarChart data={displayRadar} />
          <PerformanceTrendLine data={displayTrend} />
        </div>

        {/* PFI + AI Insight */}
        <div className="dashboard-grid">
          <PFIBarChart data={displayPfi} />
          <AIInsightCard insight={displayInsight} confidence={displayCurrent?.confidence} pfiData={displayPfi} />
        </div>

        {/* Comparison Chart — Base Paper vs Our Project */}
        <div className="dashboard-full">
          <div className="card">
            <p className="card-title">📊 Comparison: Base Paper vs Our Framework</p>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Aspect</th>
                  <th className="base-paper">Base Paper</th>
                  <th className="our-project">Our Framework</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>ML Method</td><td className="base-paper">❌ Single BPNN Model</td><td className="our-project">✅ Weighted Ensemble (BPNN + RF + XGBoost)</td></tr>
                <tr><td>Explainability</td><td className="base-paper">❌ None (black-box)</td><td className="our-project">✅ Permutation Feature Importance (PFI)</td></tr>
                <tr><td>Quiz Validation</td><td className="base-paper">❌ Single-tier static questionnaire</td><td className="our-project">✅ Two-tier adaptive quiz + cross-validation</td></tr>
                <tr><td>Preprocessing</td><td className="base-paper">⚠️ Manual / Pandas</td><td className="our-project">🚀 PySpark (scalable pipeline)</td></tr>
                <tr><td>Accuracy</td><td className="base-paper">⚠️ ~90%</td><td className="our-project">🚀 R² = 0.985 (S) <br/> R² = 0.964 (R)</td></tr>
                <tr><td>AI Recommendations</td><td className="base-paper">❌ None</td><td className="our-project">✅ Groq API (LLaMA3) + Template Fallback</td></tr>
                <tr><td>Dashboard</td><td className="base-paper">⚠️ Basic output</td><td className="our-project">🚀 Interactive charts + real-time insights</td></tr>
                <tr><td>Public Profile</td><td className="base-paper">❌ Not available</td><td className="our-project">✅ Shareable profile with privacy control</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Actions Panel */}
        <div className="dashboard-full">
          <div className="card">
            <p className="card-title">🎯 Assessment Flow</p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              {!assessmentId && <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Step 1: Submit physical metrics below ↓</span>}
              {assessmentId && !psychDone && (
                <button className="btn btn-primary" onClick={() => setQuizModal({ type: 'psychological' })}>🧠 Take Psych Quiz</button>
              )}
              {assessmentId && psychDone && <span style={{ color: 'var(--accent-success)' }}>✅ Psych Quiz Done</span>}
              {assessmentId && !socialDone && (
                <button className="btn btn-primary" onClick={() => setQuizModal({ type: 'social' })}>🤝 Take Social Quiz</button>
              )}
              {assessmentId && socialDone && <span style={{ color: 'var(--accent-success)' }}>✅ Social Quiz Done</span>}
              {assessmentId && psychDone && socialDone && (
                <button className="btn btn-primary" onClick={handlePredict}
                  disabled={prediction.status === 'processing'}>
                  {prediction.status === 'processing' ? (
                    <><span className="spinner" style={{ width: 16, height: 16 }}></span> Predicting...</>
                  ) : '🚀 Generate Prediction'}
                </button>
              )}
              {prediction.status === 'complete' && (
                <span
                  style={{ color: 'var(--accent-success)', cursor: 'pointer', textDecoration: 'underline' }}
                  onClick={() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                >
                  ✅ Prediction complete — click here to see results ↑
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Physical Metrics Form */}
        {!assessmentId && (
          <div className="dashboard-full">
            <PhysicalMetricsForm onSubmit={handleMetricsSubmit} />
          </div>
        )}

        {/* Goals & Badges — always visible */}
        <div className="dashboard-grid">
          <GoalSettingPanel pfiData={displayPfi} />
          <BadgeDisplay />
        </div>

        {/* Notifications Panel */}
        <NotificationBell />
      </div>

      {/* Quiz Modal */}
      {quizModal && (
        <QuizModal
          assessmentId={assessmentId}
          quizType={quizModal.type}
          onClose={() => setQuizModal(null)}
          onComplete={handleQuizComplete}
        />
      )}
    </div>
  );
}


// ─── Notification Bell ─────────────────────────────────
function NotificationBell() {
  const [notifs, setNotifs] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const [notifsRes, countRes] = await Promise.all([
          api.get('/student/notifications'),
          api.get('/student/notifications/unread-count'),
        ]);
        setNotifs(notifsRes.data);
        setUnread(countRes.data.unread);
      } catch (err) {
        // Notifications are non-critical, fail silently
      }
    };
    load();
  }, []);

  const markRead = async (id) => {
    try {
      await api.put(`/student/notifications/${id}/read`);
      setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnread(prev => Math.max(0, prev - 1));
    } catch (err) { }
  };

  if (notifs.length === 0 && unread === 0) return null;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}>
        <p className="card-title" style={{ margin: 0 }}>
          🔔 Notifications {unread > 0 && <span className="notif-badge">{unread}</span>}
        </p>
        <span style={{ color: 'var(--text-muted)' }}>{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
          {notifs.slice(0, 10).map(n => (
            <div key={n.id} className={`notif-item ${n.is_read ? 'read' : 'unread'}`}
              onClick={() => !n.is_read && markRead(n.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: n.is_read ? 400 : 600 }}>{n.title}</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {new Date(n.created_at).toLocaleDateString()}
                </span>
              </div>
              {n.message && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>{n.message}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

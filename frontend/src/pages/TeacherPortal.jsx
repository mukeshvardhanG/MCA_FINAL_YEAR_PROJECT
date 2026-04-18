import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import api from '../services/api';

// ─── Class Overview (Main Teacher View) ──────────────────────
function ClassOverview({ user, onLogout }) {
  const [data, setData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterGrade, setFilterGrade] = useState('All');
  const [filterPerf, setFilterPerf] = useState('All');
  const [tab, setTab] = useState('students'); // students | analytics | attendance | notifications
  const [compareMode, setCompareMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [classRes, analyticsRes] = await Promise.all([
        api.get('/teacher/class'),
        api.get('/teacher/analytics/detailed').catch(() => ({ data: null })),
      ]);
      setData(classRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      console.error('Failed to load class data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = data?.students?.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase());
    const matchesGrade = filterGrade === 'All' || s.grade === filterGrade;
    let matchesPerf = true;
    if (filterPerf === 'Top') matchesPerf = s.overall_score >= 85;
    else if (filterPerf === 'Mid') matchesPerf = s.overall_score >= 55 && s.overall_score < 85;
    else if (filterPerf === 'Low') matchesPerf = s.overall_score !== null && s.overall_score < 55;
    else if (filterPerf === 'Unassessed') matchesPerf = s.overall_score === null;
    return matchesSearch && matchesGrade && matchesPerf;
  }) || [];

  const grades = ['All', ...new Set(data?.students?.map(s => s.grade).filter(Boolean) || [])];

  const toggleCompare = (sid) => {
    setSelectedForCompare(prev => {
      if (prev.includes(sid)) return prev.filter(id => id !== sid);
      if (prev.length >= 2) return [prev[1], sid];
      return [...prev, sid];
    });
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-logo">📋 Teacher Portal</div>
          <div className="navbar-user">
            <span>👋 {user?.name || 'Teacher'}</span>
            <button className="btn btn-sm btn-danger" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </nav>

      <div className="dashboard">
        {/* Summary Cards */}
        <div className="stats-panel">
          <div className="stat-card"><div className="stat-value">{data?.total_students || 0}</div><div className="stat-label">Total Students</div></div>
          <div className="stat-card grade-b"><div className="stat-value">{data?.avg_score || 0}</div><div className="stat-label">Class Average</div></div>
          <div className="stat-card grade-a"><div className="stat-value">{data?.completion_rate || 0}%</div><div className="stat-label">Completion Rate</div></div>
          <div className="stat-card grade-c"><div className="stat-value">{filtered.filter(s => s.status !== 'Complete').length}</div><div className="stat-label">Pending</div></div>
        </div>

        {/* Tab Navigation */}
        <div className="teacher-tabs">
          {['students', 'analytics', 'attendance', 'notifications'].map(t => (
            <button key={t} className={`teacher-tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t === 'students' ? '👥 Students' : t === 'analytics' ? '📊 Analytics' : t === 'attendance' ? '📅 Attendance' : '🔔 Notifications'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {tab === 'students' && (
          <>
            {/* Filters */}
            <div className="teacher-filters">
              <input type="text" placeholder="Search by name..." value={search} onChange={e => setSearch(e.target.value)} className="form-input" style={{ flex: 1 }} />
              <select value={filterGrade} onChange={e => setFilterGrade(e.target.value)} className="form-select" style={{ width: 140 }}>
                {grades.map(g => <option key={g} value={g}>{g === 'All' ? 'All Grades' : `Grade ${g}`}</option>)}
              </select>
              <select value={filterPerf} onChange={e => setFilterPerf(e.target.value)} className="form-select" style={{ width: 160 }}>
                <option value="All">All Performance</option>
                <option value="Top">🟢 Top (85+)</option>
                <option value="Mid">🟡 Mid (55-84)</option>
                <option value="Low">🔴 Low (&lt;55)</option>
                <option value="Unassessed">⬜ Unassessed</option>
              </select>
              <button className={`btn btn-sm ${compareMode ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setCompareMode(!compareMode); setSelectedForCompare([]); }}>
                {compareMode ? '✕ Cancel Compare' : '⚖️ Compare'}
              </button>
              <button className="btn btn-sm btn-secondary" onClick={() => window.open(`/api/export/class/${data?.class_id}`, '_blank')}>
                📥 Export CSV
              </button>
            </div>

            {compareMode && selectedForCompare.length === 2 && (
              <button className="btn btn-primary" style={{ marginBottom: 12 }}
                onClick={() => navigate(`/teacher/compare?a=${selectedForCompare[0]}&b=${selectedForCompare[1]}`)}>
                Compare {selectedForCompare.length} Students →
              </button>
            )}

            {/* Student Table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="teacher-table">
                <thead>
                  <tr>
                    {compareMode && <th style={{ width: 40 }}></th>}
                    <th>Name</th>
                    <th>Score</th>
                    <th>Grade</th>
                    <th>Last Assessment</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr><td colSpan={compareMode ? 7 : 6} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No students found.</td></tr>
                  ) : filtered.map(s => (
                    <tr key={s.id} className="teacher-row" onClick={() => !compareMode && navigate(`/teacher/student/${s.id}`)}>
                      {compareMode && (
                        <td onClick={e => e.stopPropagation()}>
                          <input type="checkbox" checked={selectedForCompare.includes(s.id)}
                            onChange={() => toggleCompare(s.id)} style={{ width: 18, height: 18, accentColor: 'var(--accent-primary)' }} />
                        </td>
                      )}
                      <td style={{ fontWeight: 600 }}>{s.name}</td>
                      <td>{s.overall_score !== null ? <span className="score-pill">{s.overall_score}</span> : '—'}</td>
                      <td><span className={`grade-badge ${s.grade || ''}`}>{s.grade || '—'}</span></td>
                      <td style={{ color: 'var(--text-muted)' }}>{s.last_assessment || 'Never'}</td>
                      <td><span className={`status-badge ${s.status?.toLowerCase().replace(' ', '-')}`}>{s.status}</span></td>
                      <td style={{ textAlign: 'right' }}><span style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>View →</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {tab === 'analytics' && <AnalyticsPanel analytics={analytics} />}
        {tab === 'attendance' && <AttendancePanel classId={data?.class_id} students={data?.students} />}
        {tab === 'notifications' && <NotificationPanel students={data?.students} />}
      </div>
    </div>
  );
}


// ─── Analytics Panel ────────────────────────────────────────
function AnalyticsPanel({ analytics }) {
  if (!analytics || analytics.message) {
    return <div className="card"><p style={{ color: 'var(--text-muted)' }}>No analytics data available yet.</p></div>;
  }

  const { distribution, top_performers, bottom_performers, class_average, total_students, assessed_students } = analytics;

  const maxDist = Math.max(...Object.values(distribution || {}), 1);

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Quick Stats */}
      <div className="stats-panel">
        <div className="stat-card"><div className="stat-value">{class_average}</div><div className="stat-label">Class Average</div></div>
        <div className="stat-card"><div className="stat-value">{assessed_students}/{total_students}</div><div className="stat-label">Assessed</div></div>
      </div>

      {/* Distribution */}
      <div className="card">
        <p className="card-title">📊 Score Distribution</p>
        <div style={{ display: 'flex', gap: 12, alignItems: 'end', height: 180, padding: '16px 0' }}>
          {Object.entries(distribution || {}).map(([label, count]) => (
            <div key={label} style={{ flex: 1, textAlign: 'center' }}>
              <div style={{
                height: `${(count / maxDist) * 140}px`, minHeight: 4,
                background: label.includes('A') ? 'var(--accent-success)' : label.includes('B') ? 'var(--accent-primary)' : label.includes('C') ? 'var(--accent-warning)' : 'var(--accent-danger)',
                borderRadius: '6px 6px 0 0', transition: 'height 0.5s ease', margin: '0 auto', width: '60%',
              }} />
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>{label}</p>
              <p style={{ fontSize: '1.1rem', fontWeight: 700 }}>{count}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Top & Bottom Performers */}
      <div className="dashboard-grid">
        <div className="card">
          <p className="card-title">🏆 Top Performers</p>
          {top_performers?.map((s, i) => (
            <div key={i} className="performer-row">
              <span className="performer-rank">{i + 1}</span>
              <span style={{ flex: 1 }}>{s.name}</span>
              <span className="score-pill">{s.score}</span>
              <span className={`grade-badge ${s.grade}`}>{s.grade}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <p className="card-title">📉 Needs Attention</p>
          {bottom_performers?.map((s, i) => (
            <div key={i} className="performer-row">
              <span style={{ flex: 1 }}>{s.name}</span>
              <span className="score-pill low">{s.score}</span>
              <span className={`grade-badge ${s.grade}`}>{s.grade}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


// ─── Attendance Panel ───────────────────────────────────────
function AttendancePanel({ classId, students }) {
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState([]);
  const [markDate, setMarkDate] = useState(new Date().toISOString().split('T')[0]);
  const [marking, setMarking] = useState({});
  const [saving, setSaving] = useState(false);
  const [showSummary, setShowSummary] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [recRes, sumRes] = await Promise.all([
          api.get('/teacher/attendance'),
          api.get('/teacher/attendance/summary'),
        ]);
        setRecords(recRes.data);
        setSummary(sumRes.data);
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, []);

  const handleMark = async () => {
    setSaving(true);
    try {
      const entries = (students || []).map(s => ({
        student_id: s.id,
        date: markDate,
        status: marking[s.id] || 'present',
      }));
      await api.post('/teacher/attendance', { records: entries });
      alert('Attendance recorded!');
      // Reload
      const [recRes, sumRes] = await Promise.all([
        api.get('/teacher/attendance'),
        api.get('/teacher/attendance/summary'),
      ]);
      setRecords(recRes.data);
      setSummary(sumRes.data);
    } catch (err) {
      alert('Failed to save attendance');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Toggle */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button className={`btn btn-sm ${showSummary ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setShowSummary(true)}>📊 Summary</button>
        <button className={`btn btn-sm ${!showSummary ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setShowSummary(false)}>✏️ Mark Attendance</button>
      </div>

      {showSummary ? (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="teacher-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Total Days</th>
                <th>Present</th>
                <th>Attendance Rate</th>
                <th>Latest Score</th>
                <th>Correlation</th>
              </tr>
            </thead>
            <tbody>
              {summary.map(s => (
                <tr key={s.student_id}>
                  <td style={{ fontWeight: 600 }}>{s.name}</td>
                  <td>{s.total_days}</td>
                  <td>{s.present_days}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 6, background: 'var(--bg-input)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: `${s.attendance_rate}%`, height: '100%', background: s.attendance_rate >= 80 ? 'var(--accent-success)' : s.attendance_rate >= 60 ? 'var(--accent-warning)' : 'var(--accent-danger)', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, minWidth: 40 }}>{s.attendance_rate}%</span>
                    </div>
                  </td>
                  <td>{s.latest_score !== null ? <span className="score-pill">{s.latest_score}</span> : '—'}</td>
                  <td>
                    {s.attendance_rate > 0 && s.latest_score !== null ? (
                      <span style={{ color: s.attendance_rate >= 75 && s.latest_score >= 70 ? 'var(--accent-success)' : 'var(--accent-warning)', fontWeight: 500 }}>
                        {s.attendance_rate >= 75 && s.latest_score >= 70 ? '✅ Positive' : '⚠️ Review'}
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card">
          <p className="card-title">✏️ Mark Attendance</p>
          <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
            <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Date:</label>
            <input type="date" value={markDate} onChange={e => setMarkDate(e.target.value)} className="form-input" style={{ width: 180 }} />
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {(students || []).map(s => (
              <div key={s.id} className="attendance-row">
                <span style={{ flex: 1, fontWeight: 500 }}>{s.name}</span>
                {['present', 'absent', 'late'].map(status => (
                  <button key={status} className={`attendance-btn ${(marking[s.id] || 'present') === status ? status : ''}`}
                    onClick={() => setMarking({ ...marking, [s.id]: status })}>
                    {status === 'present' ? '✅' : status === 'absent' ? '❌' : '⏰'} {status}
                  </button>
                ))}
              </div>
            ))}
          </div>
          <button className="btn btn-primary" onClick={handleMark} disabled={saving} style={{ marginTop: 16 }}>
            {saving ? 'Saving...' : '💾 Save Attendance'}
          </button>
        </div>
      )}
    </div>
  );
}


// ─── Notification Panel ─────────────────────────────────────
function NotificationPanel({ students }) {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState('all');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!title.trim()) return alert('Title is required');
    setSending(true);
    try {
      await api.post('/teacher/notify', {
        user_id: target,
        title,
        message,
        type: 'reminder',
      });
      alert('Notification sent!');
      setTitle('');
      setMessage('');
    } catch (err) {
      alert('Failed to send notification');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="card">
      <p className="card-title">🔔 Send Notification / Reminder</p>
      <div style={{ display: 'grid', gap: 14 }}>
        <div className="form-group">
          <label className="form-label">Send To</label>
          <select value={target} onChange={e => setTarget(e.target.value)} className="form-select">
            <option value="all">📢 All Students in Class</option>
            {(students || []).map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Title</label>
          <input value={title} onChange={e => setTitle(e.target.value)} className="form-input" placeholder="e.g. Fitness Test Reminder" />
        </div>
        <div className="form-group">
          <label className="form-label">Message</label>
          <textarea value={message} onChange={e => setMessage(e.target.value)} className="form-input" rows={3}
            placeholder="e.g. Please complete your assessment before Friday..." style={{ resize: 'vertical', minHeight: 80 }} />
        </div>
        <button className="btn btn-primary" onClick={handleSend} disabled={sending}>
          {sending ? 'Sending...' : '📤 Send Notification'}
        </button>
      </div>
    </div>
  );
}


// ─── Individual Student View ────────────────────────────────
function StudentView({ user }) {
  const [student, setStudent] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [noteCategory, setNoteCategory] = useState('feedback');
  const [savingNote, setSavingNote] = useState(false);
  const navigate = useNavigate();
  const studentId = window.location.pathname.split('/').pop();

  useEffect(() => {
    const load = async () => {
      try {
        const [studentRes, notesRes] = await Promise.all([
          api.get(`/teacher/student/${studentId}`),
          api.get(`/teacher/notes/${studentId}`).catch(() => ({ data: [] })),
        ]);
        setStudent(studentRes.data);
        setNotes(notesRes.data);
      } catch (err) {
        console.error('Failed to load student:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [studentId]);

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    setSavingNote(true);
    try {
      await api.post(`/teacher/notes/${studentId}`, { content: newNote, category: noteCategory });
      const res = await api.get(`/teacher/notes/${studentId}`);
      setNotes(res.data);
      setNewNote('');
    } catch (err) {
      alert('Failed to save note');
    } finally {
      setSavingNote(false);
    }
  };

  if (loading) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}><div className="spinner"></div></div>;
  if (!student) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)', color: 'var(--text-muted)' }}>Student not found.</div>;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <nav className="navbar">
        <div className="navbar-content">
          <button className="btn btn-sm btn-secondary" onClick={() => navigate('/teacher')}>← Back to Class</button>
          <div className="navbar-logo">{student.name}</div>
          <button className="btn btn-sm btn-secondary" onClick={() => {
            const url = `/api/export/report/${studentId}?format=csv`;
            window.open(url, '_blank');
          }}>📥 Export Report</button>
        </div>
      </nav>

      <div className="dashboard">
        {/* Student Info */}
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            <div><span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Name</span><p style={{ fontWeight: 600 }}>{student.name}</p></div>
            <div><span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Age</span><p>{student.age || '—'}</p></div>
            <div><span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Gender</span><p>{student.gender || '—'}</p></div>
            <div><span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Grade Level</span><p>{student.grade_level || '—'}</p></div>
          </div>
        </div>

        {/* Score Summary */}
        <div className="stats-panel">
          <div className="stat-card grade-a"><div className="stat-value">{student.final_score ?? '—'}</div><div className="stat-label">Overall Score</div></div>
          <div className="stat-card grade-b"><div className="stat-value">{student.performance_grade || '—'}</div><div className="stat-label">Grade</div></div>
          <div className="stat-card"><div className="stat-value">{student.bpnn_score ?? '—'}</div><div className="stat-label">BPNN</div></div>
          <div className="stat-card"><div className="stat-value">{student.xgb_score ?? '—'}</div><div className="stat-label">XGBoost</div></div>
        </div>

        {/* AI Insight */}
        {student.insight && (
          <div className="card">
            <p className="card-title">🤖 AI Insights</p>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>{student.insight.summary}</p>
            {student.insight.strengths?.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <p style={{ color: 'var(--accent-success)', fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>💪 Strengths</p>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {student.insight.strengths.map((s, i) => <li key={i} style={{ color: 'var(--text-secondary)', padding: '2px 0 2px 16px', position: 'relative', fontSize: '0.9rem' }}>▹ {s}</li>)}
                </ul>
              </div>
            )}
            {student.insight.weaknesses?.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <p style={{ color: 'var(--accent-danger)', fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>📈 Areas for Improvement</p>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {student.insight.weaknesses.map((w, i) => <li key={i} style={{ color: 'var(--text-secondary)', padding: '2px 0 2px 16px', position: 'relative', fontSize: '0.9rem' }}>▹ {w}</li>)}
                </ul>
              </div>
            )}
            {student.insight.action_steps?.length > 0 && (
              <div>
                <p style={{ color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.85rem', marginBottom: 4 }}>🎯 Action Steps</p>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {student.insight.action_steps.map((a, i) => <li key={i} style={{ color: 'var(--text-secondary)', padding: '2px 0 2px 16px', position: 'relative', fontSize: '0.9rem' }}>▹ {a}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Teacher Notes / Feedback */}
        <div className="card">
          <p className="card-title">📝 Teacher Notes & Feedback</p>

          {/* Add Note */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
            <select value={noteCategory} onChange={e => setNoteCategory(e.target.value)} className="form-select" style={{ width: 160 }}>
              <option value="feedback">💬 Feedback</option>
              <option value="improvement_plan">📋 Improvement Plan</option>
              <option value="general">📎 General Note</option>
            </select>
            <textarea value={newNote} onChange={e => setNewNote(e.target.value)} className="form-input"
              placeholder="Write feedback or an improvement plan for this student..." rows={2}
              style={{ flex: 1, minWidth: 200, resize: 'vertical' }} />
            <button className="btn btn-primary btn-sm" onClick={handleAddNote} disabled={savingNote || !newNote.trim()}>
              {savingNote ? '...' : '💾 Save'}
            </button>
          </div>

          {/* Notes List */}
          {notes.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No notes yet. Add feedback above.</p>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {notes.map(n => (
                <div key={n.id} className="note-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className={`note-category ${n.category}`}>
                      {n.category === 'feedback' ? '💬' : n.category === 'improvement_plan' ? '📋' : '📎'} {n.category.replace('_', ' ')}
                    </span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{new Date(n.created_at).toLocaleDateString()}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>{n.content}</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 4 }}>— {n.teacher_name}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// ─── Student Comparison View ────────────────────────────────
function CompareView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const params = new URLSearchParams(window.location.search);
  const idA = params.get('a');
  const idB = params.get('b');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/teacher/compare?student_a=${idA}&student_b=${idB}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (idA && idB) load();
  }, [idA, idB]);

  if (loading) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}><div className="spinner"></div></div>;
  if (!data) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)', color: 'var(--text-muted)' }}>Comparison data not available.</div>;

  const { student_a: a, student_b: b } = data;

  const compareRow = (label, valA, valB, higherBetter = true) => {
    const na = valA === null || valA === undefined;
    const nb = valB === null || valB === undefined;
    let colorA = 'var(--text-primary)', colorB = 'var(--text-primary)';
    if (!na && !nb) {
      const better = higherBetter ? valA > valB : valA < valB;
      colorA = better ? 'var(--accent-success)' : valA === valB ? 'var(--text-primary)' : 'var(--accent-danger)';
      colorB = !better ? 'var(--accent-success)' : valA === valB ? 'var(--text-primary)' : 'var(--accent-danger)';
    }
    return (
      <tr key={label}>
        <td style={{ textAlign: 'right', fontWeight: 600, color: colorA, padding: '8px 16px' }}>{na ? '—' : valA}</td>
        <td style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '8px 12px', fontSize: '0.85rem' }}>{label}</td>
        <td style={{ fontWeight: 600, color: colorB, padding: '8px 16px' }}>{nb ? '—' : valB}</td>
      </tr>
    );
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <nav className="navbar">
        <div className="navbar-content">
          <button className="btn btn-sm btn-secondary" onClick={() => navigate('/teacher')}>← Back</button>
          <div className="navbar-logo">⚖️ Student Comparison</div>
        </div>
      </nav>

      <div className="dashboard">
        <div className="card">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'right', padding: '12px 16px', borderBottom: '2px solid var(--border-primary)', color: 'var(--accent-primary)' }}>{a.name}</th>
                <th style={{ textAlign: 'center', padding: '12px', borderBottom: '2px solid var(--border-primary)', color: 'var(--text-muted)' }}>Metric</th>
                <th style={{ padding: '12px 16px', borderBottom: '2px solid var(--border-primary)', color: 'var(--accent-secondary)' }}>{b.name}</th>
              </tr>
            </thead>
            <tbody>
              {compareRow('Overall Score', a.overall_score, b.overall_score)}
              {compareRow('Grade', a.grade, b.grade)}
              {compareRow('Sprint 100m (s)', a.physical?.sprint_100m, b.physical?.sprint_100m, false)}
              {compareRow('Endurance 1500m', a.physical?.endurance_1500m, b.physical?.endurance_1500m, false)}
              {compareRow('Strength', a.physical?.strength, b.physical?.strength)}
              {compareRow('BMI', a.physical?.bmi, b.physical?.bmi)}
              {compareRow('Reaction Time (ms)', a.physical?.reaction_time, b.physical?.reaction_time, false)}
              {compareRow('Plank Hold (s)', a.physical?.plank_hold, b.physical?.plank_hold)}
              {compareRow('Breath Hold (s)', a.physical?.breath_hold, b.physical?.breath_hold)}
              <tr><td colSpan={3} style={{ padding: '8px', borderBottom: '1px solid var(--border-primary)' }}></td></tr>
              {compareRow('Motivation', a.psychological?.motivation, b.psychological?.motivation)}
              {compareRow('Self-Confidence', a.psychological?.self_confidence, b.psychological?.self_confidence)}
              {compareRow('Stress Mgmt', a.psychological?.stress_management, b.psychological?.stress_management)}
              {compareRow('Goal Orientation', a.psychological?.goal_orientation, b.psychological?.goal_orientation)}
              {compareRow('Mental Resilience', a.psychological?.mental_resilience, b.psychological?.mental_resilience)}
              <tr><td colSpan={3} style={{ padding: '8px', borderBottom: '1px solid var(--border-primary)' }}></td></tr>
              {compareRow('Teamwork', a.social?.teamwork, b.social?.teamwork)}
              {compareRow('Participation', a.social?.participation, b.social?.participation)}
              {compareRow('Communication', a.social?.communication, b.social?.communication)}
              {compareRow('Leadership', a.social?.leadership, b.social?.leadership)}
              {compareRow('Peer Collab', a.social?.peer_collaboration, b.social?.peer_collaboration)}
              <tr><td colSpan={3} style={{ padding: '8px', borderBottom: '1px solid var(--border-primary)' }}></td></tr>
              {compareRow('Attendance Rate %', a.attendance_rate, b.attendance_rate)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


// ─── Shared Helpers ─────────────────────────────────────────
// (gradeColor and statusColor are handled via CSS classes now)

// ─── Main Export ────────────────────────────────────────────
export default function TeacherPortal({ user, onLogout }) {
  return (
    <Routes>
      <Route index element={<ClassOverview user={user} onLogout={onLogout} />} />
      <Route path="student/:id" element={<StudentView user={user} />} />
      <Route path="compare" element={<CompareView />} />
    </Routes>
  );
}

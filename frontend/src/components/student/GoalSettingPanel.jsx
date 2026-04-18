import React, { useState, useEffect } from 'react';
import api from '../../services/api';

/**
 * GoalSettingPanel — Student self-service goal management with progress tracking.
 */
export default function GoalSettingPanel({ pfiData }) {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', target_value: '', metric_type: '', deadline: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadGoals(); }, []);

  const loadGoals = async () => {
    try {
      const res = await api.get('/student/goals');
      setGoals(res.data);
    } catch (err) {
      console.error('Failed to load goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await api.post('/student/goals', {
        title: form.title,
        target_value: form.target_value ? parseFloat(form.target_value) : null,
        metric_type: form.metric_type || null,
        deadline: form.deadline || null,
      });
      setForm({ title: '', target_value: '', metric_type: '', deadline: '' });
      setShowForm(false);
      await loadGoals();
    } catch (err) {
      alert('Failed to create goal');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (goalId, currentValue) => {
    const newVal = prompt('Enter new progress value:', currentValue);
    if (newVal === null) return;
    try {
      await api.put(`/student/goals/${goalId}`, { current_value: parseFloat(newVal) });
      await loadGoals();
    } catch (err) {
      alert('Failed to update goal');
    }
  };

  const handleComplete = async (goalId) => {
    try {
      await api.put(`/student/goals/${goalId}`, { status: 'completed' });
      await loadGoals();
    } catch (err) {
      alert('Failed to complete goal');
    }
  };

  const metricTypes = [
    { value: 'push_ups', label: '💪 Push-ups' },
    { value: 'squats', label: '🦵 Squats' },
    { value: 'sprint_time', label: '🏃 Sprint Time (s)' },
    { value: 'endurance', label: '🫁 Endurance (min)' },
    { value: 'plank_hold', label: '🧱 Plank Hold (s)' },
    { value: 'breath_hold', label: '🌬️ Breath Hold (s)' },
    { value: 'reaction_time', label: '⚡ Reaction Time (ms)' },
    { value: 'weight', label: '⚖️ Weight (kg)' },
    { value: 'other', label: '📝 Other' },
  ];

  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');
  
  let recGoalFeature = "cardiovascular endurance";
  if (pfiData && pfiData.length > 0) {
      recGoalFeature = pfiData[pfiData.length - 1].name?.toLowerCase() || pfiData[pfiData.length - 1].feature_name;
  }

  if (loading) return <div className="card"><p style={{ color: 'var(--text-muted)' }}>Loading goals...</p></div>;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <p className="card-title" style={{ margin: 0 }}>🎯 My Goals</p>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '＋ New Goal'}
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <form onSubmit={handleCreate} className="goal-form">
          <input className="form-input" placeholder="Goal title (e.g., 'Do 50 push-ups')" value={form.title}
            onChange={e => setForm({ ...form, title: e.target.value })} required />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            <select className="form-select" value={form.metric_type} onChange={e => setForm({ ...form, metric_type: e.target.value })}>
              <option value="">Metric type...</option>
              {metricTypes.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
            <input className="form-input" type="number" placeholder="Target value" value={form.target_value}
              onChange={e => setForm({ ...form, target_value: e.target.value })} />
            <input className="form-input" type="date" value={form.deadline}
              onChange={e => setForm({ ...form, deadline: e.target.value })} />
          </div>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? 'Saving...' : '💾 Create Goal'}
          </button>
        </form>
      )}

      {/* Suggested Goal */}
      {!showForm && activeGoals.length < 3 && (
        <div style={{ background: 'rgba(99,102,241,0.1)', padding: 12, borderRadius: 8, marginBottom: 16, border: '1px dashed rgba(99,102,241,0.3)' }}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 600 }}>💡 AI Recommended Goal</p>
          <p style={{ margin: '4px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Based on your latest assessment weaknesses:</p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ margin: 0, fontWeight: 500 }}>Improve {recGoalFeature} by +10%</p>
            <button className="btn btn-sm btn-secondary" onClick={() => {
              setForm({ title: `Improve ${recGoalFeature} by 10%`, target_value: '', metric_type: 'other', deadline: '' });
              setShowForm(true);
            }}>Accept</button>
          </div>
        </div>
      )}

      {/* Active Goals */}
      {activeGoals.length === 0 && !showForm && (
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
          No active goals. Set one to start tracking your progress!
        </p>
      )}

      <div style={{ display: 'grid', gap: 10 }}>
        {activeGoals.map(g => (
          <div key={g.id} className="goal-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div>
                <p style={{ fontWeight: 600, marginBottom: 2 }}>{g.title}</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {g.metric_type && <span>{metricTypes.find(m => m.value === g.metric_type)?.label || g.metric_type} • </span>}
                  {g.deadline && <span>Due: {new Date(g.deadline).toLocaleDateString()}</span>}
                </p>
              </div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn btn-sm btn-secondary" onClick={() => handleUpdate(g.id, g.current_value)} title="Update progress">📊</button>
                <button className="btn btn-sm btn-secondary" onClick={() => handleComplete(g.id)} title="Mark complete">✅</button>
              </div>
            </div>
            {g.target_value && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{g.current_value} / {g.target_value}</span>
                  <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{g.progress_pct?.toFixed(0) || 0}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${Math.min(100, g.progress_pct || 0)}%` }} />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Completed Goals */}
      {completedGoals.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>✅ Completed ({completedGoals.length})</p>
          {completedGoals.slice(0, 3).map(g => (
            <div key={g.id} style={{ padding: '6px 0', color: 'var(--text-muted)', fontSize: '0.85rem', textDecoration: 'line-through' }}>
              {g.title}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

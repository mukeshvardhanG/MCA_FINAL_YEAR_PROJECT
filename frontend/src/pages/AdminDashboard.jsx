import React, { useEffect, useState } from 'react';
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import api, { getAdminStats } from '../services/api';
import ResearchDashboard from '../components/research/ResearchDashboard';

// ─── User Management ─────────────────────────────────────────
function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student', class_id: '' });
  const [saving, setSaving] = useState(false);

  const fetchUsers = async () => {
    try {
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/admin/users', form);
      setShowForm(false);
      setForm({ name: '', email: '', password: '', role: 'student', class_id: '' });
      fetchUsers();
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (id) => {
    if (!confirm('Deactivate this user?')) return;
    try {
      await api.delete(`/admin/users/${id}`);
      fetchUsers();
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const roleBadge = (role) => {
    const m = {
      admin: 'bg-red-500/20 text-red-400',
      teacher: 'bg-cyan-500/20 text-cyan-400',
      student: 'bg-green-500/20 text-green-400',
      deactivated: 'bg-slate-600/50 text-slate-400',
    };
    return m[role] || m.student;
  };

  const roleBadgeLight = (role) => {
    const m = {
      admin: 'bg-red-100 text-red-700 border border-red-200',
      teacher: 'bg-cyan-100 text-cyan-700 border border-cyan-200',
      student: 'bg-green-100 text-green-700 border border-green-200',
      deactivated: 'bg-gray-100 text-gray-500 border border-gray-200',
    };
    return m[role] || m.student;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1e1b4b' }}>User Management</h2>
        <button onClick={() => setShowForm(!showForm)} style={{ padding: '8px 18px', borderRadius: 8, background: showForm ? '#fee2e2' : 'linear-gradient(135deg,#4f46e5,#7c3aed)', color: showForm ? '#dc2626' : 'white', border: 'none', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}>
          {showForm ? 'Cancel' : '+ Create User'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} style={{ background: '#f5f3ff', borderRadius: 12, border: '1.5px solid #e0e7ff', padding: '24px' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" placeholder="Full Name" required value={form.name} onChange={e => setForm({...form, name: e.target.value})}
              style={{ background: '#fff', border: '1.5px solid #e0e7ff', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: '#1e1b4b', outline: 'none' }} />
            <input type="email" placeholder="Email" required value={form.email} onChange={e => setForm({...form, email: e.target.value})}
              style={{ background: '#fff', border: '1.5px solid #e0e7ff', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: '#1e1b4b', outline: 'none' }} />
            <input type="password" placeholder="Password" required minLength={6} value={form.password} onChange={e => setForm({...form, password: e.target.value})}
              style={{ background: '#fff', border: '1.5px solid #e0e7ff', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: '#1e1b4b', outline: 'none' }} />
            <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}
              style={{ background: '#fff', border: '1.5px solid #e0e7ff', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: '#1e1b4b', outline: 'none' }}>
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button type="submit" disabled={saving} style={{ marginTop: 16, padding: '10px 24px', borderRadius: 8, background: saving ? '#e0e7ff' : 'linear-gradient(135deg,#059669,#0891b2)', color: 'white', border: 'none', fontWeight: 600, fontSize: '0.85rem', cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.7 : 1 }}>
            {saving ? 'Creating...' : 'Create User'}
          </button>
        </form>
      )}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}><div style={{ width: 32, height: 32, border: '4px solid #e0e7ff', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div></div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e0e7ff', overflow: 'hidden', boxShadow: '0 2px 16px rgba(79,70,229,0.08)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#f0effe' }}>
                <th style={{ textAlign: 'left', padding: '12px 20px', fontWeight: 700, color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Name</th>
                <th style={{ textAlign: 'left', padding: '12px 20px', fontWeight: 700, color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Email</th>
                <th style={{ textAlign: 'left', padding: '12px 20px', fontWeight: 700, color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Role</th>
                <th style={{ padding: '12px 20px' }}></th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid #e0e7ff', transition: 'background 0.15s' }} onMouseEnter={e=>e.currentTarget.style.background='#f5f3ff'} onMouseLeave={e=>e.currentTarget.style.background=''}>
                  <td style={{ padding: '12px 20px', fontWeight: 600, color: '#1e1b4b' }}>{u.name}</td>
                  <td style={{ padding: '12px 20px', color: '#6b7280' }}>{u.email}</td>
                  <td style={{ padding: '12px 20px' }}>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${roleBadgeLight(u.role)}`}>{u.role}</span>
                  </td>
                  <td style={{ padding: '12px 20px', textAlign: 'right' }}>
                    {u.role !== 'deactivated' && (
                      <button onClick={() => handleDeactivate(u.id)} style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Deactivate</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── ML Configuration ─────────────────────────────────────────
function MLConfiguration() {
  const [stats, setStats] = useState(null);
  const [weights, setWeights] = useState({ bpnn: 0.4, rf: 0.3, xgb: 0.3 });
  const [metrics, setMetrics] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [trainingLogs, setTrainingLogs] = useState(null);
  const [trainingInProgress, setTrainingInProgress] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsData, metricsData] = await Promise.all([
          getAdminStats(),
          api.get('/admin/ml/metrics').then(r => r.data)
        ]);
        setStats(statsData);
        setWeights(statsData.ensemble_weights);
        setMetrics(metricsData);
      } catch (err) {
        console.error('Failed to load ML config:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const weightSum = (weights.bpnn + weights.rf + weights.xgb).toFixed(3);
  const isValid = Math.abs(parseFloat(weightSum) - 1.0) < 0.005;

  const handleSave = async () => {
    if (!isValid) { alert('Weights must sum to 1.0'); return; }
    setSaving(true);
    try {
      await api.put('/admin/ml/weights', weights);
      alert('Weights updated successfully!');
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTrainModels = async () => {
    if (!confirm('This will retrain the BPNN, Random Forest, and XGBoost models on the current dataset. This process may take 15-30 seconds. Continue?')) return;
    setTrainingInProgress(true);
    setTrainingLogs("Initiating Model Training Pipeline...\nConnecting to ML Engine...\n");
    try {
      const res = await api.post('/admin/ml/train');
      const { output, error_output, status } = res.data;
      
      let finalLogs = output || "";
      if (error_output) {
        finalLogs += "\n\n[ERRORS / WARNINGS]\n" + error_output;
      }
      
      if (status === 'error') {
        finalLogs += "\n\n❌ Training Pipeline Failed.";
      }
      
      setTrainingLogs(finalLogs);
      // Reload stats after training
      const [statsData, metricsData] = await Promise.all([
        getAdminStats(),
        api.get('/admin/ml/metrics').then(r => r.data)
      ]);
      setStats(statsData);
      setMetrics(metricsData);
    } catch (err) {
      setTrainingLogs(prev => prev + `\n\n❌ CRITICAL ERROR:\n${err.response?.data?.detail || err.message}`);
    } finally {
      setTrainingInProgress(false);
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}><div style={{ width: 32, height: 32, border: '4px solid #e0e7ff', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div></div>;
  }

  return (
    <div className="space-y-6">
      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1e1b4b' }}>ML Configuration</h2>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div style={{ background: '#fff', borderRadius: 12, border: '1.5px solid rgba(8,145,178,0.25)', padding: 20, boxShadow: '0 2px 12px rgba(8,145,178,0.08)' }}>
            <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#6b7280', marginBottom: 4, fontWeight: 700 }}>Dataset Size (Dataset2)</p>
            <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0891b2' }}>{stats.dataset_size?.toLocaleString()}</p>
            <p style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: 2 }}>S Training Records</p>
          </div>
          <div style={{ background: '#fff', borderRadius: 12, border: '1.5px solid rgba(5,150,105,0.25)', padding: 20, boxShadow: '0 2px 12px rgba(5,150,105,0.08)' }}>
            <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#6b7280', marginBottom: 4, fontWeight: 700 }}>Ensemble R² (Test Set)</p>
            <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#059669' }}>{(stats.accuracy_r2 * 100).toFixed(2)}%</p>
            <p style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: 2 }}>80/20 split on Dataset2</p>
          </div>
          <div style={{ background: '#fff', borderRadius: 12, border: '1.5px solid rgba(217,119,6,0.25)', padding: 20, boxShadow: '0 2px 12px rgba(217,119,6,0.08)' }}>
            <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#6b7280', marginBottom: 4, fontWeight: 700 }}>MAE</p>
            <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#d97706' }}>{stats.mae?.toFixed(4)}</p>
            <p style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: 2 }}>Mean Absolute Error</p>
          </div>
        </div>
      )}

      {/* Dataset Split Info */}
      <div style={{ background: 'linear-gradient(135deg,#f0effe,#e8f4ff)', borderRadius: 12, border: '1.5px solid #c7d2fe', padding: '16px 20px' }}>
        <h3 style={{ fontWeight: 700, color: '#4f46e5', fontSize: '0.9rem', marginBottom: 8 }}>📊 Dataset Split Architecture</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          <div style={{ background: 'white', borderRadius: 8, padding: '10px 14px', border: '1px solid #c7d2fe' }}>
            <div style={{ fontWeight: 700, color: '#4f46e5', fontSize: '0.85rem' }}>📦 Dataset2 (Training)</div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>S — 10,000 records</div>
            <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: 2 }}>80% Train / 20% Test Split</div>
          </div>
          <div style={{ background: 'white', borderRadius: 8, padding: '10px 14px', border: '1px solid #c7d2fe' }}>
            <div style={{ fontWeight: 700, color: '#0891b2', fontSize: '0.85rem' }}>🔬 Dataset1 (R Pilot)</div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>R DB records — Testing only</div>
            <div style={{ fontSize: '0.75rem', color: '#dc2626', marginTop: 2 }}>Never used for training</div>
          </div>
          <div style={{ background: 'white', borderRadius: 8, padding: '10px 14px', border: '1px solid #c7d2fe' }}>
            <div style={{ fontWeight: 700, color: '#7c3aed', fontSize: '0.85rem' }}>✅ Dataset3 (Validation)</div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>S held-out — 2,000 records</div>
            <div style={{ fontSize: '0.75rem', color: '#dc2626', marginTop: 2 }}>Pure validation — never seen in training</div>
          </div>
        </div>
      </div>

      {/* Weight Sliders */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e0e7ff', padding: '24px', boxShadow: '0 2px 12px rgba(79,70,229,0.07)' }}>
        <h3 style={{ fontWeight: 700, color: '#1e1b4b', marginBottom: 20, fontSize: '1rem' }}>Ensemble Weights</h3>
        {['bpnn', 'rf', 'xgb'].map(key => (
          <div key={key} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: 6 }}>
              <span style={{ fontWeight: 600, color: '#374151' }}>{key === 'bpnn' ? 'BPNN (PyTorch)' : key === 'rf' ? 'Random Forest' : 'XGBoost'}</span>
              <span style={{ fontFamily: 'monospace', color: '#4f46e5', fontWeight: 700 }}>{weights[key].toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="1" step="0.01" value={weights[key]}
              onChange={e => setWeights({...weights, [key]: parseFloat(e.target.value)})}
              style={{ width: '100%', height: 8, accentColor: '#4f46e5', cursor: 'pointer' }} />
          </div>
        ))}
        <div style={{ fontSize: '0.9rem', fontFamily: 'monospace', color: isValid ? '#059669' : '#dc2626', fontWeight: 700, marginBottom: 16 }}>
          Sum: {weightSum} {isValid ? '✓ Valid' : '✗ Must equal 1.0'}
        </div>
        <button onClick={handleSave} disabled={!isValid || saving}
          style={{ padding: '10px 24px', borderRadius: 8, background: (!isValid || saving) ? '#e0e7ff' : 'linear-gradient(135deg,#4f46e5,#0891b2)', color: 'white', border: 'none', fontWeight: 700, fontSize: '0.9rem', cursor: (!isValid || saving) ? 'not-allowed' : 'pointer', opacity: (!isValid || saving) ? 0.6 : 1 }}>
          {saving ? 'Saving...' : 'Save Weights'}
        </button>
      </div>

      {/* Model Metrics Table */}
      {metrics.length > 0 && (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e0e7ff', overflow: 'hidden', boxShadow: '0 2px 12px rgba(79,70,229,0.07)' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #e0e7ff', background: '#f0effe' }}><h3 style={{ fontWeight: 700, color: '#4f46e5' }}>Model Performance Metrics</h3></div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#f5f3ff' }}>
                <th style={{ textAlign: 'left', padding: '10px 20px', color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700 }}>Model</th>
                <th style={{ textAlign: 'left', padding: '10px 20px', color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700 }}>MAE</th>
                <th style={{ textAlign: 'left', padding: '10px 20px', color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700 }}>RMSE</th>
                <th style={{ textAlign: 'left', padding: '10px 20px', color: '#4f46e5', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700 }}>R²</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map(m => (
                <tr key={m.model} style={{ borderBottom: '1px solid #e0e7ff' }}>
                  <td style={{ padding: '10px 20px', fontWeight: 600, color: '#1e1b4b' }}>{m.model}</td>
                  <td style={{ padding: '10px 20px', color: '#374151' }}>{m.mae}</td>
                  <td style={{ padding: '10px 20px', color: '#374151' }}>{m.rmse}</td>
                  <td style={{ padding: '10px 20px', color: '#059669', fontWeight: 700 }}>{m.r2}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}



      {/* Model Training Simulator */}
      <div style={{ background: '#fff', borderRadius: 12, border: '1.5px solid rgba(79,70,229,0.2)', padding: '24px', boxShadow: '0 2px 12px rgba(79,70,229,0.07)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontWeight: 700, color: '#1e1b4b', fontSize: '1rem' }}>Model Training Simulator</h3>
            <p style={{ fontSize: '0.85rem', color: '#6b7280', marginTop: 4 }}>Execute the ML pipeline to retrain models on Dataset2 and view live output.</p>
          </div>
          <button
            onClick={handleTrainModels}
            disabled={trainingInProgress}
            style={{ padding: '10px 22px', borderRadius: 8, background: trainingInProgress ? '#e0e7ff' : 'linear-gradient(135deg,#4f46e5,#7c3aed)', color: 'white', border: 'none', fontWeight: 700, fontSize: '0.9rem', cursor: trainingInProgress ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            {trainingInProgress && <div style={{ width: 16, height: 16, border: '2.5px solid rgba(255,255,255,0.4)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div>}
            {trainingInProgress ? 'Training...' : '▶ Train Models'}
          </button>
        </div>

        {/* Architecture diagram */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#f0f4ff', padding: '14px 20px', borderRadius: 10, border: '1px solid #e0e7ff', fontFamily: 'monospace', fontSize: '0.75rem', textAlign: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <div style={{ padding: '8px 12px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#0891b2', fontWeight: 700 }}>Dataset2<br/>(CSV Training)</div>
          <div style={{ color: '#6b7280' }}>➡</div>
          <div style={{ padding: '8px 12px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#d97706', fontWeight: 700 }}>Preprocessing<br/>(Scaling/Imputation)</div>
          <div style={{ color: '#6b7280' }}>➡</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <div style={{ padding: '4px 10px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#059669', fontWeight: 700 }}>BPNN (PyTorch)</div>
            <div style={{ padding: '4px 10px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#059669', fontWeight: 700 }}>Random Forest</div>
            <div style={{ padding: '4px 10px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#059669', fontWeight: 700 }}>XGBoost</div>
          </div>
          <div style={{ color: '#6b7280' }}>➡</div>
          <div style={{ padding: '8px 12px', border: '1px solid #c7d2fe', borderRadius: 6, background: 'white', color: '#7c3aed', fontWeight: 700 }}>Ensemble<br/>(Weighted Avg)</div>
        </div>

        {/* Terminal Output */}
        {(trainingLogs !== null || trainingInProgress) && (
          <div style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid #1e293b' }}>
            <div style={{ background: '#1e293b', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>Terminal — train_models.py (Dataset2)</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }}></div>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }}></div>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }}></div>
              </div>
            </div>
            <pre style={{ padding: '16px', fontSize: '0.75rem', fontFamily: 'monospace', color: '#4ade80', whiteSpace: 'pre-wrap', maxHeight: '384px', overflowY: 'auto', margin: 0, background: '#0d1117' }}>
              {trainingLogs || 'Awaiting output...'}
              {trainingInProgress && <span style={{ animation: 'pulse 1s ease infinite' }}>_</span>}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Semester Management ──────────────────────────────────────
function SemesterManagement() {
  const [semName, setSemName] = useState('');

  const handleCreate = async () => {
    if (!semName.trim()) return;
    try {
      await api.post('/admin/semesters', { name: semName });
      alert(`Semester "${semName}" created.`);
      setSemName('');
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1e1b4b' }}>Semester Management</h2>
      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e0e7ff', padding: '24px', boxShadow: '0 2px 12px rgba(79,70,229,0.07)' }}>
        <p style={{ fontSize: '0.9rem', color: '#6b7280', marginBottom: 16 }}>Create a new semester period for assessments.</p>
        <div style={{ display: 'flex', gap: 12 }}>
          <input type="text" placeholder="e.g. 2026-S1" value={semName} onChange={e => setSemName(e.target.value)}
            style={{ flex: 1, background: '#f4f6fb', border: '1.5px solid #e0e7ff', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: '#1e1b4b', outline: 'none', fontFamily: 'Inter,sans-serif' }} />
          <button onClick={handleCreate} style={{ padding: '10px 24px', borderRadius: 8, background: 'linear-gradient(135deg,#059669,#0891b2)', color: 'white', border: 'none', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
            Create Semester
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Admin Layout ─────────────────────────────────────────────
export default function AdminDashboard({ user, onLogout }) {
  const tabs = [
    { path: '/admin', label: '👥 Users', end: true },
    { path: '/admin/ml', label: '🧠 ML Config' },
    { path: '/admin/research', label: '🔬 Research' },
    { path: '/admin/semesters', label: '📅 Semesters' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4ff', color: '#1e1b4b', fontFamily: 'Inter,sans-serif' }}>
      {/* Navbar */}
      <nav style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.92)', backdropFilter: 'blur(20px)', borderBottom: '1px solid #e0e7ff', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 12px rgba(79,70,229,0.07)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg,#4f46e5,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: '1.1rem', color: 'white' }}>A</div>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: '1.05rem', color: '#1e1b4b' }}>Admin Panel</h1>
            <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>{user?.name || 'Admin'}</p>
          </div>
        </div>
        <button onClick={onLogout} style={{ padding: '8px 18px', borderRadius: 8, background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>
          Logout
        </button>
      </nav>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid #e0e7ff', background: 'rgba(255,255,255,0.7)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', display: 'flex', gap: 4 }}>
          {tabs.map(t => (
            <NavLink key={t.path} to={t.path} end={t.end}
              style={({ isActive }) => ({
                padding: '12px 18px',
                fontSize: '0.9rem',
                fontWeight: isActive ? 700 : 500,
                borderBottom: isActive ? '2.5px solid #4f46e5' : '2.5px solid transparent',
                color: isActive ? '#4f46e5' : '#6b7280',
                textDecoration: 'none',
                transition: 'all 0.2s',
                display: 'block',
              })}
            >
              {t.label}
            </NavLink>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '24px' }}>
        <Routes>
          <Route index element={<UserManagement />} />
          <Route path="ml" element={<MLConfiguration />} />
          <Route path="research" element={<ResearchDashboard />} />
          <Route path="semesters" element={<SemesterManagement />} />
        </Routes>
      </div>
    </div>
  );
}

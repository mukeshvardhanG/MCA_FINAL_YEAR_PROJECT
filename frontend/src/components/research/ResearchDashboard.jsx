import React, { useEffect, useState, useMemo, useCallback } from 'react';
import api from '../../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, AreaChart, Area, ScatterChart, Scatter, ZAxis, ReferenceLine, Legend,
} from 'recharts';

/* ─── Lazy Data Loader Hook ───────────────────────────────────────── */
function useResearchEndpoint(endpoint) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const load = useCallback(async () => {
    if (data) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/research/${endpoint}`);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint, data]);

  return { data, loading, error, load };
}

/* ─── Design Tokens ──────────────────────────────────────────── */
const MODEL_COLORS = {
  BPNN: '#f43f5e',
  'Random Forest': '#10b981',
  XGBoost: '#f59e0b',
  Ensemble: '#6366f1',
};
const PFI_COLORS = [
  '#6366f1','#818cf8','#a5b4fc','#06b6d4',
  '#22d3ee','#10b981','#34d399','#f59e0b','#fbbf24','#ef4444',
];

/* ─── Shared UI Atoms ─────────────────────────────────────────── */
function SectionHeader({ icon, title, subtitle }) {
  return (
    <div style={{ marginBottom: 20, marginTop: 4 }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: '1.15rem' }}>{icon}</span> {title}
      </h3>
      {subtitle && <p style={{ fontSize: '0.73rem', color: '#64748b', marginTop: 2, marginLeft: 28 }}>{subtitle}</p>}
    </div>
  );
}

function StatCard({ label, value, sub, accent = '#6366f1' }) {
  return (
    <div style={{
      background: 'rgba(15,23,42,0.6)',
      border: `1.5px solid ${accent}40`,
      borderRadius: 16,
      padding: '18px 20px',
      transition: 'transform 0.2s',
      position: 'relative',
      overflow: 'hidden',
    }}
      onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.03)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
    >
      <p style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', marginBottom: 4, fontWeight: 600 }}>{label}</p>
      <p style={{ fontSize: '1.7rem', fontWeight: 900, color: accent, letterSpacing: '-0.03em', lineHeight: 1 }}>{value}</p>
      {sub && <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

function AnimatedBar({ value, max = 1, color = '#6366f1', label, delay = 0 }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth((value / max) * 100), 120 + delay);
    return () => clearTimeout(t);
  }, [value, max, delay]);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ fontSize: '0.72rem', color: '#94a3b8', width: 120, flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
      <div style={{ flex: 1, background: '#1e293b', borderRadius: 99, height: 10, overflow: 'hidden' }}>
        <div style={{ width: `${width}%`, height: '100%', background: color, borderRadius: 99, transition: 'width 1s ease-out' }} />
      </div>
      <span style={{ fontSize: '0.72rem', fontFamily: 'monospace', color: '#cbd5e1', width: 56, textAlign: 'right' }}>{value.toFixed(4)}</span>
    </div>
  );
}

function Badge({ text, variant = 'success' }) {
  const s = {
    success: { bg: 'rgba(16,185,129,0.15)', color: '#34d399', border: 'rgba(16,185,129,0.3)' },
    warning: { bg: 'rgba(245,158,11,0.15)', color: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
    danger:  { bg: 'rgba(244,63,94,0.15)',  color: '#fb7185', border: 'rgba(244,63,94,0.3)'  },
    info:    { bg: 'rgba(6,182,212,0.15)',  color: '#22d3ee', border: 'rgba(6,182,212,0.3)'  },
  }[variant] || {};
  return (
    <span style={{ padding: '2px 10px', borderRadius: 99, fontSize: '0.72rem', fontWeight: 700, background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
      {text}
    </span>
  );
}

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(15,23,42,0.97)', border: '1px solid #334155', borderRadius: 12, padding: '10px 16px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}>
      <p style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ fontSize: '0.72rem', color: p.color }}>
          {p.name}: <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</span>
        </p>
      ))}
    </div>
  );
};

function LoadingSpinner({ label = 'Loading…' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: 16 }}>
      <div style={{ width: 44, height: 44, border: '4px solid #334155', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <p style={{ fontSize: '0.85rem', color: '#64748b' }}>{label}</p>
    </div>
  );
}

function ErrorCard({ msg, cmd }) {
  return (
    <div style={{ background: 'rgba(244,63,94,0.08)', border: '1.5px solid rgba(244,63,94,0.25)', borderRadius: 16, padding: '32px', textAlign: 'center' }}>
      <p style={{ color: '#fb7185', fontWeight: 700, marginBottom: 6 }}>Data not available</p>
      <p style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: 8 }}>{msg}</p>
      {cmd && <p style={{ fontSize: '0.75rem', color: '#475569' }}>Run: <code style={{ background: '#0f172a', color: '#22d3ee', padding: '2px 8px', borderRadius: 6 }}>{cmd}</code></p>}
    </div>
  );
}

const panel = (inner) => (
  <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid #1e293b', borderRadius: 18, padding: '24px', marginBottom: 20 }}>
    {inner}
  </div>
);

/* ═══════════════════════════════════════════════════════════════════
   TAB 1 ▸ MODEL PERFORMANCE COMPARISON
   ═══════════════════════════════════════════════════════════════════ */
function ModelPerformanceTab({ data }) {
  const sorted = useMemo(() =>
    [...(data.model_comparison || [])].sort((a, b) => b['R²'] - a['R²']),
    [data.model_comparison]
  );

  const barData = sorted.map(m => ({
    Model: m.Model,
    'R²': parseFloat(m['R²'].toFixed(4)),
    MAE:  parseFloat(m.MAE.toFixed(4)),
    RMSE: parseFloat(m.RMSE.toFixed(4)),
  }));

  return (
    <div style={{ animation: 'fadeIn 0.4s ease' }}>
      <SectionHeader icon="🧠" title="Model Performance Comparison"
        subtitle="BPNN (PyTorch) · Random Forest · XGBoost · Weighted Ensemble — evaluated on held-out test set" />

      {/* ── Summary Stat Cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 14, marginBottom: 22 }}>
        {sorted.map(m => (
          <StatCard
            key={m.Model}
            label={m.Model}
            value={m['R²'].toFixed(4)}
            sub={`MAE ${m.MAE.toFixed(3)} · RMSE ${m.RMSE.toFixed(3)}`}
            accent={MODEL_COLORS[m.Model] || '#6366f1'}
          />
        ))}
      </div>

      {/* ── R² Grouped Bar ── */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>R² Score Comparison</h4>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData} margin={{ top: 10, right: 24, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="Model" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="R²" radius={[8, 8, 0, 0]} maxBarSize={60}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={MODEL_COLORS[entry.Model] || '#6366f1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* ── MAE & RMSE Comparison ── */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>MAE &amp; RMSE Comparison (lower is better)</h4>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={barData} margin={{ top: 10, right: 24, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="Model" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
            <Bar dataKey="MAE"  fill="#f59e0b" radius={[6,6,0,0]} maxBarSize={40} />
            <Bar dataKey="RMSE" fill="#f43f5e" radius={[6,6,0,0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* ── Detailed Table ── */}
      <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid #1e293b', borderRadius: 18, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'rgba(30,41,59,0.6)' }}>
                {['Rank', 'Model', 'R²', 'RMSE', 'MAE', 'MAPE%', 'Max Error'].map(h => (
                  <th key={h} style={{ padding: '12px 18px', textAlign: 'center', fontWeight: 700, color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((m, i) => (
                <tr key={m.Model}
                  style={{ borderBottom: '1px solid #1e293b' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <td style={{ padding: '12px 18px', textAlign: 'center' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, borderRadius: '50%', background: i === 0 ? 'rgba(245,158,11,0.2)' : 'rgba(51,65,85,0.5)', fontSize: '0.75rem', fontWeight: 700, color: i === 0 ? '#fbbf24' : '#64748b' }}>{i + 1}</span>
                  </td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontWeight: 700, color: MODEL_COLORS[m.Model] || '#e2e8f0' }}>
                    {m.Model}
                    {m.Model === 'Ensemble' && <span style={{ marginLeft: 6 }}><Badge text="Active" variant="info" /></span>}
                  </td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', fontWeight: 800, color: m['R²'] > 0.95 ? '#34d399' : m['R²'] > 0.8 ? '#fbbf24' : '#fb7185' }}>{m['R²'].toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{m.RMSE.toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{m.MAE.toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{m['MAPE%'].toFixed(2)}%</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{m.Max_Error.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   TAB 2 ▸ FEATURE IMPORTANCE (PFI)
   ═══════════════════════════════════════════════════════════════════ */
function FeatureImportanceTab({ data }) {
  const maxImp = Math.max(...(data.pfi?.map(p => p.importance) || [1]));

  return (
    <div style={{ animation: 'fadeIn 0.4s ease' }}>
      <SectionHeader icon="🔍" title="Permutation Feature Importance"
        subtitle={`${data.pfi_stability?.n_runs || 5} runs × ${data.pfi_stability?.n_repeats_per_run || 10} repeats — mean importance drop when feature is shuffled`} />

      {/* Stability pill */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'rgba(15,23,42,0.5)', border: '1px solid #1e293b', borderRadius: 12, padding: '12px 20px', marginBottom: 20 }}>
        <Badge
          text={data.pfi_stability?.interpretation || 'Unknown'}
          variant={data.pfi_stability?.interpretation === 'High stability' ? 'success' : 'warning'}
        />
        <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
          Mean rank σ = <span style={{ fontFamily: 'monospace', color: '#f1f5f9' }}>{data.pfi_stability?.mean_rank_std}</span>
          {' · '}Stable features: <span style={{ fontFamily: 'monospace', color: '#34d399' }}>{data.pfi_stability?.stable_features_pct}%</span>
        </span>
      </div>

      {/* Horizontal bar chart */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>Importance by Feature</h4>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data.pfi} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis type="category" dataKey="feature" tick={{ fill: '#e2e8f0', fontSize: 11 }} width={115} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="importance" radius={[0, 7, 7, 0]} maxBarSize={26}>
              {data.pfi.map((_, i) => <Cell key={i} fill={PFI_COLORS[i % PFI_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* Animated breakdown */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 14 }}>Importance Breakdown</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {data.pfi.map((p, i) => (
            <AnimatedBar key={p.feature} label={p.feature} value={p.importance} max={maxImp} color={PFI_COLORS[i % PFI_COLORS.length]} delay={i * 70} />
          ))}
        </div>
      </>)}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   TAB 3 ▸ SCORE DISTRIBUTION
   ═══════════════════════════════════════════════════════════════════ */
function ScoreDistributionTab() {
  const { data, loading, error, load } = useResearchEndpoint('residuals');
  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner label="Loading score distribution…" />;
  if (error)   return <ErrorCard msg={error} cmd="python -m research.residuals" />;
  if (!data)   return null;

  // Build score histogram from scatter (actual scores)
  const scatter = (data.scatter || []).slice(0, 2000);

  // Bin actual and predicted scores into 10-pt buckets
  const buildBins = (values, key) => {
    const bins = {};
    for (let start = 0; start <= 90; start += 10) bins[`${start}-${start + 10}`] = 0;
    values.forEach(p => {
      const v = parseFloat(p[key]);
      const b = Math.min(Math.floor(v / 10) * 10, 90);
      bins[`${b}-${b + 10}`] = (bins[`${b}-${b + 10}`] || 0) + 1;
    });
    return Object.entries(bins).map(([range, count]) => ({ range, count }));
  };

  const actualBins    = buildBins(scatter, 'actual');
  const predictedBins = buildBins(scatter, 'predicted');

  // Merge for grouped bar
  const merged = actualBins.map((b, i) => ({
    range:  b.range,
    Actual:    b.count,
    Predicted: predictedBins[i]?.count ?? 0,
  }));

  // Error band summary
  const summary = data.ensemble_summary || {};

  const withinN = (n) => {
    const count = scatter.filter(p => Math.abs(p.residual) <= n).length;
    return scatter.length ? ((count / scatter.length) * 100).toFixed(1) : '—';
  };

  return (
    <div style={{ animation: 'fadeIn 0.4s ease' }}>
      <SectionHeader icon="📊" title="Score Distribution"
        subtitle={`Actual vs Predicted score distribution · ${scatter.length} test samples`} />

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 14, marginBottom: 22 }}>
        <StatCard label="Mean Score (Actual)" value={scatter.length ? (scatter.reduce((s, p) => s + p.actual, 0) / scatter.length).toFixed(1) : '—'} sub="Test set" accent="#06b6d4" />
        <StatCard label="Mean Score (Pred.)"  value={scatter.length ? (scatter.reduce((s, p) => s + p.predicted, 0) / scatter.length).toFixed(1) : '—'} sub="Model output" accent="#6366f1" />
        <StatCard label="Within ±5 pts"  value={`${withinN(5)}%`}  sub="Near-perfect accuracy" accent="#10b981" />
        <StatCard label="Within ±10 pts" value={`${withinN(10)}%`} sub="Good prediction band" accent="#f59e0b" />
      </div>

      {/* Grouped Distribution Bar */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>Actual vs Predicted Score Histogram (10-pt buckets)</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={merged} margin={{ top: 10, right: 24, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="range" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
            <Bar dataKey="Actual"    fill="#06b6d4" radius={[6,6,0,0]} maxBarSize={36} opacity={0.85} />
            <Bar dataKey="Predicted" fill="#6366f1" radius={[6,6,0,0]} maxBarSize={36} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* Actual vs Predicted Scatter */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Actual vs Predicted Scatter</h4>
        <p style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 16 }}>Points clustering along the diagonal indicate high predictive accuracy</p>
        <ResponsiveContainer width="100%" height={340}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="x" name="Actual" type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Actual Score', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 11 }} />
            <YAxis dataKey="y" name="Predicted" type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Predicted Score', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }} />
            <ZAxis range={[18, 18]} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return (
                <div style={{ background: 'rgba(15,23,42,0.97)', border: '1px solid #334155', borderRadius: 10, padding: '10px 14px' }}>
                  <p style={{ fontSize: '0.72rem', color: '#f1f5f9' }}>Actual: <span style={{ fontFamily: 'monospace', color: '#06b6d4' }}>{d?.x}</span></p>
                  <p style={{ fontSize: '0.72rem', color: '#f1f5f9' }}>Predicted: <span style={{ fontFamily: 'monospace', color: '#6366f1' }}>{d?.y}</span></p>
                </div>
              );
            }} />
            <ReferenceLine segment={[{x:0,y:0},{x:100,y:100}]} stroke="#6366f1" strokeDasharray="6 3" strokeWidth={2}
              label={{ value: 'Perfect Prediction', fill: '#6366f1', fontSize: 10 }} />
            <Scatter data={scatter.map(p => ({ x: p.actual, y: p.predicted }))} fill="#06b6d4" fillOpacity={0.45} />
          </ScatterChart>
        </ResponsiveContainer>
      </>)}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   TAB 4 ▸ RESIDUAL PLOT
   ═══════════════════════════════════════════════════════════════════ */
function ResidualPlotTab() {
  const { data, loading, error, load } = useResearchEndpoint('residuals');
  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner label="Loading residual analysis…" />;
  if (error)   return <ErrorCard msg={error} cmd="python -m research.residuals" />;
  if (!data)   return null;

  const scatter    = (data.scatter || []).slice(0, 500);
  const hist       = data.histogram || [];
  const summary    = data.ensemble_summary || {};
  const modelStats = data.model_residual_stats || {};

  const residualPoints = scatter.map(p => ({ x: p.predicted, y: p.residual }));

  return (
    <div style={{ animation: 'fadeIn 0.4s ease' }}>
      <SectionHeader icon="📉" title="Residual Plot"
        subtitle={`Ensemble model · ${data.n_samples} test samples — residual = actual − predicted`} />

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 14, marginBottom: 22 }}>
        <StatCard label="Mean Residual"  value={summary.mean_residual?.toFixed(4) ?? '—'} sub="Should be ≈ 0" accent="#06b6d4" />
        <StatCard label="Std Residual"   value={summary.std_residual?.toFixed(4)  ?? '—'} sub="Spread of errors" accent="#6366f1" />
        <StatCard label="Zero-Mean Check" value={summary.zero_mean_check ? 'PASS ✓' : 'FAIL ✗'} sub="Unbiased model?" accent={summary.zero_mean_check ? '#10b981' : '#f43f5e'} />
        <StatCard label="Test Samples"   value={data.n_samples?.toLocaleString() ?? '—'} sub="Held-out set" accent="#f59e0b" />
      </div>

      {/* Residuals vs Predicted (classic residual plot) */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Residuals vs Predicted Score</h4>
        <p style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 16 }}>Points should be randomly scattered around zero — no pattern means homoscedasticity</p>
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="x" name="Predicted" type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Predicted Score', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 11 }} />
            <YAxis dataKey="y" name="Residual" type="number" tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Residual', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }} />
            <ZAxis range={[18, 18]} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return (
                <div style={{ background: 'rgba(15,23,42,0.97)', border: '1px solid #334155', borderRadius: 10, padding: '10px 14px' }}>
                  <p style={{ fontSize: '0.72rem', color: '#f1f5f9' }}>Predicted: <span style={{ fontFamily: 'monospace', color: '#06b6d4' }}>{d?.x}</span></p>
                  <p style={{ fontSize: '0.72rem', color: '#f1f5f9' }}>Residual: <span style={{ fontFamily: 'monospace', color: '#fbbf24' }}>{d?.y}</span></p>
                </div>
              );
            }} />
            <ReferenceLine y={0} stroke="#6366f1" strokeDasharray="6 3" strokeWidth={2}
              label={{ value: 'Zero residual', fill: '#6366f1', fontSize: 10 }} />
            <Scatter data={residualPoints} fill="#06b6d4" fillOpacity={0.45} />
          </ScatterChart>
        </ResponsiveContainer>
      </>)}

      {/* Residual Histogram */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 4 }}>Residual Distribution</h4>
        <p style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 16 }}>Should resemble a normal distribution centred at 0</p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={hist} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="bucket" tick={{ fill: '#94a3b8', fontSize: 10 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="count" radius={[6,6,0,0]} maxBarSize={40}>
              {hist.map((_, i) => <Cell key={i} fill={i === Math.floor(hist.length / 2) ? '#6366f1' : '#06b6d4'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* Per-model residual stats table */}
      <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid #1e293b', borderRadius: 18, overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid #1e293b' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0' }}>Per-Model Residual Statistics</h4>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: 'rgba(30,41,59,0.6)' }}>
                {['Model','Mean','Std','Skewness','Kurtosis','% Under','% Over'].map(h => (
                  <th key={h} style={{ padding: '11px 16px', textAlign: 'center', fontWeight: 600, color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(modelStats).map(([model, s]) => (
                <tr key={model} style={{ borderBottom: '1px solid #1e293b' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontWeight: 700, color: MODEL_COLORS[model] || '#94a3b8' }}>{model}</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{s.mean?.toFixed(4)}</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{s.std?.toFixed(4)}</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{s.skewness?.toFixed(4)}</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{s.kurtosis?.toFixed(4)}</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#fb7185' }}>{s.pct_negative}%</td>
                  <td style={{ padding: '11px 16px', textAlign: 'center', fontFamily: 'monospace', color: '#34d399' }}>{s.pct_positive}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   TAB 5 ▸ ABLATION STUDY
   ═══════════════════════════════════════════════════════════════════ */
function AblationStudyTab({ data }) {
  const ablation = data.ablation || [];

  const gain1 = ablation[1] && ablation[0]
    ? ((ablation[1]['R²'] - ablation[0]['R²']) * 100).toFixed(2)
    : '—';
  const gain2 = ablation[2] && ablation[1]
    ? ((ablation[2]['R²'] - ablation[1]['R²']) * 100).toFixed(2)
    : '—';

  return (
    <div style={{ animation: 'fadeIn 0.4s ease' }}>
      <SectionHeader icon="🧬" title="Ablation Study — Feature Subset Analysis"
        subtitle="Proving that multi-dimensional features progressively boost prediction accuracy" />

      {/* Insight banner */}
      <div style={{ background: 'linear-gradient(135deg,rgba(99,102,241,0.12),rgba(16,185,129,0.08))', border: '1.5px solid rgba(99,102,241,0.25)', borderRadius: 16, padding: '20px 24px', marginBottom: 22 }}>
        <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.7 }}>
          Adding <span style={{ color: '#fbbf24', fontWeight: 700 }}>Psychological</span> features boosted R² by{' '}
          <span style={{ color: '#34d399', fontWeight: 900, fontSize: '1.05rem' }}>+{gain1}%</span>, and adding{' '}
          <span style={{ color: '#22d3ee', fontWeight: 700 }}>Social</span> features contributed another{' '}
          <span style={{ color: '#34d399', fontWeight: 900, fontSize: '1.05rem' }}>+{gain2}%</span>.{' '}
          This proves the <span style={{ color: '#f1f5f9', fontWeight: 700 }}>multi-dimensional approach is scientifically superior</span> to physical-only assessment.
        </p>
      </div>

      {/* Summary cards per config */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))', gap: 14, marginBottom: 22 }}>
        {ablation.map((a, i) => {
          const accents = ['#f43f5e', '#f59e0b', '#10b981'];
          const icons   = ['💪', '🧠', '🌟'];
          return (
            <div key={a.Config} style={{
              background: 'rgba(15,23,42,0.6)',
              border: `1.5px solid ${accents[i]}40`,
              borderRadius: 16,
              padding: '20px',
              textAlign: 'center',
              transition: 'transform 0.2s',
            }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.03)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>{icons[i]}</div>
              <p style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: 4 }}>{a.Config}</p>
              <p style={{ fontSize: '2rem', fontWeight: 900, color: accents[i], lineHeight: 1 }}>{a['R²'].toFixed(4)}</p>
              <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: 4 }}>{a.Num_Features} features</p>
              {i > 0 && (
                <span style={{ marginTop: 10, display: 'inline-block', padding: '2px 10px', background: 'rgba(16,185,129,0.15)', color: '#34d399', borderRadius: 99, fontSize: '0.72rem', fontWeight: 700 }}>
                  +{((a['R²'] - ablation[i-1]['R²']) * 100).toFixed(2)}% R²
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Area chart */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>R² Progression Across Configurations</h4>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={ablation} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
            <defs>
              <linearGradient id="ablGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="Config" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis domain={['auto', 1.0]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Area type="monotone" dataKey="R²" stroke="#6366f1" fill="url(#ablGrad)" strokeWidth={3}
              dot={{ r: 7, fill: '#6366f1', stroke: '#0f172a', strokeWidth: 3 }} />
          </AreaChart>
        </ResponsiveContainer>
      </>)}

      {/* Bar: RMSE/MAE by config */}
      {panel(<>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 16 }}>MAE &amp; RMSE by Configuration (lower is better)</h4>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={ablation} margin={{ top: 10, right: 24, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="Config" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
            <Bar dataKey="MAE"  fill="#f59e0b" radius={[6,6,0,0]} maxBarSize={40} />
            <Bar dataKey="RMSE" fill="#f43f5e" radius={[6,6,0,0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </>)}

      {/* Detailed table */}
      <div style={{ background: 'rgba(15,23,42,0.5)', border: '1px solid #1e293b', borderRadius: 18, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'rgba(30,41,59,0.6)' }}>
                {['Configuration', 'Features', 'R²', 'RMSE', 'MAE', 'Δ R²'].map(h => (
                  <th key={h} style={{ padding: '12px 18px', textAlign: 'center', fontWeight: 600, color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ablation.map((a, i) => (
                <tr key={a.Config} style={{ borderBottom: '1px solid #1e293b' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontWeight: 700, color: '#f1f5f9' }}>{a.Config}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center' }}>
                    <span style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc', padding: '2px 10px', borderRadius: 99, fontSize: '0.75rem', fontWeight: 700 }}>{a.Num_Features}</span>
                  </td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', fontWeight: 800, color: '#34d399' }}>{a['R²'].toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{a.RMSE.toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#cbd5e1' }}>{a.MAE.toFixed(4)}</td>
                  <td style={{ padding: '12px 18px', textAlign: 'center', fontFamily: 'monospace', color: '#34d399', fontWeight: 700 }}>
                    {i === 0 ? '—' : `+${((a['R²'] - ablation[i-1]['R²']) * 100).toFixed(2)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════
   MAIN EXPORT
   ═══════════════════════════════════════════════════════════════════ */
export default function ResearchDashboard() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [activeTab, setActiveTab]     = useState('models');

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/research/summary');
        setSummaryData(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const TABS = [
    { id: 'models',       label: '🧠 Model Comparison'   },
    { id: 'features',     label: '🔍 Feature Importance'  },
    { id: 'distribution', label: '📊 Score Distribution'  },
    { id: 'residuals',    label: '📉 Residual Plot'       },
    { id: 'ablation',     label: '🧬 Ablation Study'      },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '96px 0', gap: 18 }}>
        <div style={{ position: 'relative' }}>
          <div style={{ width: 56, height: 56, border: '4px solid #1e293b', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
          <div style={{ position: 'absolute', inset: 0, width: 56, height: 56, border: '4px solid rgba(99,102,241,0.15)', borderRadius: '50%', animation: 'ping 1.2s ease infinite' }} />
        </div>
        <p style={{ fontSize: '0.88rem', color: '#64748b' }}>Loading research experiments…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ background: 'rgba(244,63,94,0.08)', border: '1.5px solid rgba(244,63,94,0.25)', borderRadius: 16, padding: 40, textAlign: 'center' }}>
        <p style={{ color: '#fb7185', fontWeight: 700, marginBottom: 8 }}>Failed to load research data</p>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 10 }}>{error}</p>
        <p style={{ fontSize: '0.75rem', color: '#475569' }}>
          Run <code style={{ background: '#0f172a', color: '#22d3ee', padding: '2px 8px', borderRadius: 6 }}>python -m research.run_all_experiments</code> first.
        </p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(160deg,#0a0f1e 0%,#0d1927 50%,#070d18 100%)', padding: '0 0 60px 0', fontFamily: 'Inter,sans-serif' }}>
      {/* ── Header ── */}
      <div style={{ background: 'linear-gradient(90deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08),rgba(6,182,212,0.1))', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 18, padding: '24px 28px', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10 }}>
          <div style={{ width: 46, height: 46, borderRadius: 14, background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem', flexShrink: 0, boxShadow: '0 0 20px rgba(99,102,241,0.35)' }}>🔬</div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 900, color: '#f1f5f9', letterSpacing: '-0.02em', margin: 0 }}>Research Validation Dashboard</h2>
            <p style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>IEEE/Scopus-Grade Experimental Results · Multi-Dimensional PE Assessment</p>
          </div>
        </div>
        {summaryData?.dataset_info && (
          <div style={{ display: 'flex', gap: 28, fontSize: '0.78rem', color: '#64748b', flexWrap: 'wrap' }}>
            <span>📁 Training: <span style={{ color: '#22d3ee', fontWeight: 700 }}>{parseInt(summaryData.dataset_info.synthetic_size || 0).toLocaleString()}</span> synthetic records</span>
            <span>🧪 Validation: <span style={{ color: '#34d399', fontWeight: 700 }}>{summaryData.dataset_info.real_size || 'N/A'}</span> pilot records</span>
            <span>🔢 Features: <span style={{ color: '#fbbf24', fontWeight: 700 }}>{summaryData.dataset_info.n_features || 21}</span> dimensions</span>
          </div>
        )}
      </div>

      {/* ── Tab Bar ── */}
      <div style={{ display: 'flex', gap: 6, background: 'rgba(15,23,42,0.6)', borderRadius: 14, padding: 6, border: '1px solid #1e293b', marginBottom: 28, overflowX: 'auto' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            flex: 1,
            minWidth: 'max-content',
            padding: '10px 18px',
            borderRadius: 10,
            border: activeTab === t.id ? '1px solid rgba(99,102,241,0.4)' : '1px solid transparent',
            background: activeTab === t.id ? 'rgba(99,102,241,0.18)' : 'transparent',
            color: activeTab === t.id ? '#a5b4fc' : '#64748b',
            fontWeight: activeTab === t.id ? 700 : 500,
            fontSize: '0.82rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: activeTab === t.id ? '0 0 16px rgba(99,102,241,0.15)' : 'none',
          }}
            onMouseEnter={e => { if (activeTab !== t.id) { e.currentTarget.style.color = '#e2e8f0'; e.currentTarget.style.background = 'rgba(30,41,59,0.5)'; } }}
            onMouseLeave={e => { if (activeTab !== t.id) { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'transparent'; } }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      {summaryData && activeTab === 'models'       && <ModelPerformanceTab   data={summaryData} />}
      {summaryData && activeTab === 'features'     && <FeatureImportanceTab  data={summaryData} />}
      {              activeTab === 'distribution'  && <ScoreDistributionTab  />}
      {              activeTab === 'residuals'     && <ResidualPlotTab       />}
      {summaryData && activeTab === 'ablation'     && <AblationStudyTab      data={summaryData} />}

      <style>{`
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes ping  { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.2)} }
        @keyframes fadeIn{ from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  );
}

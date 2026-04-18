import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ErrorBar } from 'recharts';

const DEFAULT_COLORS = ['#6366f1', '#818cf8', '#a5b4fc', '#06b6d4', '#22d3ee', '#10b981', '#34d399', '#f59e0b', '#fbbf24', '#ef4444'];
const TOP_COLORS = ['#ef4444', '#eab308', '#3b82f6']; // Red, Yellow, Blue

export default function PFIBarChart({ data }) {
  if (!data || !data.length) {
    return <div className="card chart-card"><p className="card-title">🔍 Feature Importance (PFI)</p><p style={{color:'var(--text-muted)', textAlign:'center', paddingTop:60}}>No PFI data</p></div>;
  }

  return (
    <div className="card chart-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p className="card-title" style={{ margin: 0 }}>🔍 Top 10 Feature Importance (PFI)</p>
        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 12, background: 'rgba(99,102,241,0.15)', color: 'var(--accent-primary)', fontWeight: 600 }}>Explainable AI (PFI-based)</span>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 4, marginBottom: 8 }}>Error bars show ±1 std. dev. from permutation importance</p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data.map(d => ({ ...d, name: d.name || d.feature_name }))} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" horizontal={false} />
          <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
          <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} width={95} />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 8, color: 'var(--text-primary)' }}
            formatter={(value) => [value.toFixed(4), 'Importance']} />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            <ErrorBar dataKey="error" width={4} strokeWidth={1.5} stroke="var(--text-muted)" />
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={index < 3 ? TOP_COLORS[index] : DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}


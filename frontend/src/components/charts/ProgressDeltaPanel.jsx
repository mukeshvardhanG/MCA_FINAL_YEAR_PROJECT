import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../services/api';

export default function ProgressDeltaPanel({ refreshTrigger }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/assessments/');
        setHistory(res.data || []);
      } catch (err) {
        // Skip errors softly in dashboard panels
      }
    };
    load();
  }, [refreshTrigger]);

  if (history.length < 2) return null;

  const current = history[0];
  const previous = history[1];

  const getDelta = (cur, prev) => {
    if (cur == null || prev == null) return null;
    return cur - prev;
  };

  const renderDelta = (val, prevVal, isNegativeGood = false) => {
    const delta = getDelta(val, prevVal);
    if (delta == null || Number.isNaN(delta)) return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    if (delta === 0) return <span style={{ color: 'var(--text-muted)' }}>0 (No change)</span>;
    
    const isImprovement = isNegativeGood ? delta < 0 : delta > 0;
    const sign = delta > 0 ? '+' : '';
    const color = isImprovement ? 'var(--accent-success)' : 'var(--accent-warning)';
    return (
      <span style={{ color, fontWeight: 600 }}>
        {sign}{Number.isInteger(delta) ? delta : delta.toFixed(1)} {isImprovement ? '🔥' : '📉'}
      </span>
    );
  };

  const chartData = [
    { name: 'Push-ups', Previous: previous.push_ups || 0, Current: current.push_ups || 0 },
    { name: 'Squats', Previous: previous.squats || 0, Current: current.squats || 0 },
    { name: 'Sit-ups', Previous: previous.sit_ups || 0, Current: current.sit_ups || 0 },
    { name: 'Plank (s)', Previous: previous.plank_hold_seconds || 0, Current: current.plank_hold_seconds || 0 },
  ];

  return (
    <div className="card dashboard-full" style={{ marginBottom: 20 }}>
      <p className="card-title">📈 Comparative Progress (Current vs Previous)</p>
      
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20, marginBottom: 20 }}>
        <div style={{ flex: '1 1 300px', background: 'var(--bg-input)', padding: 16, borderRadius: 8 }}>
          <p style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>Absolute Deltas</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: '0.9rem' }}>
            <div>💪 Strength Score: {renderDelta(current.strength_score, previous.strength_score)}</div>
            <div>⚡ Sprint (100m): {renderDelta(current.running_speed_100m, previous.running_speed_100m, true)}s</div>
            <div>🏃 Endurance (1500m): {renderDelta(current.endurance_1500m, previous.endurance_1500m, true)}m</div>
            <div>⏱️ Reaction Time: {renderDelta(current.reaction_time_ms, previous.reaction_time_ms, true)}ms</div>
            <div>⚖️ BMI Change: {renderDelta(current.bmi, previous.bmi, true)}</div>
            <div>🫁 Breath Hold: {renderDelta(current.breath_hold_seconds, previous.breath_hold_seconds)}s</div>
          </div>
        </div>

        <div style={{ flex: '2 1 400px', height: 260 }}>
          <p style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 16, textAlign: 'center' }}>Physical Stats Breakdown</p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 0, right: 30, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8 }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
              <Legend verticalAlign="top" height={36} />
              <Bar dataKey="Previous" fill="var(--text-muted)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Current" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

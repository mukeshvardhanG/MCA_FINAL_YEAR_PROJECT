import React from 'react';
import { Radar, RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

export default function RadarChart({ data }) {
  if (!data || !data.length) {
    return <div className="card chart-card"><p className="card-title">📊 Category Radar</p><p style={{color:'var(--text-muted)', textAlign:'center', paddingTop:60}}>No data available</p></div>;
  }

  return (
    <div className="card chart-card">
      <p className="card-title">📊 Performance Radar</p>
      <ResponsiveContainer width="100%" height={280}>
        <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="var(--border-primary)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 13 }} />
          <PolarRadiusAxis angle={90} domain={[0, 10]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
          <Radar name="Score" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 8, color: 'var(--text-primary)' }} />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}

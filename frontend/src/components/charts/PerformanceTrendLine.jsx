import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function PerformanceTrendLine({ data }) {
  if (!data || !data.length) {
    return <div className="card chart-card"><p className="card-title">📈 Performance Trend</p><p style={{color:'var(--text-muted)', textAlign:'center', paddingTop:60}}>No trend data yet</p></div>;
  }

  const sortedData = [...data]
    .map(item => ({ ...item, name: item.name || item.semester || 'Unknown' }))
    .sort((a, b) => {
      const [yearA, semA] = a.name.split('-S');
      const [yearB, semB] = b.name.split('-S');
      return yearA !== yearB ? yearA - yearB : semA - semB;
    });
  
  const dedupedData = [...new Map(sortedData.map(item => [item.name, item])).values()];

  const lastScore = dedupedData.length > 0 ? dedupedData[dedupedData.length - 1].score : 0;
  let predictionStr = "";
  if (dedupedData.length >= 2) {
      const prevScore = dedupedData[dedupedData.length - 2].score;
      const diff = lastScore - prevScore;
      const predScore = lastScore + (diff > 0 ? Math.min(diff, 5) : Math.max(diff, -5));
      predictionStr = `⭐ Next score prediction: ${Math.floor(predScore - 2)}–${Math.ceil(predScore + 2)}`;
  } else if (dedupedData.length === 1) {
      predictionStr = `⭐ Next score prediction: ${Math.floor(lastScore)}–${Math.ceil(lastScore + 4)}`;
  }

  return (
    <div className="card chart-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p className="card-title" style={{ margin: 0 }}>📈 Performance Trend</p>
        {predictionStr && <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>{predictionStr}</span>}
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={dedupedData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-primary)" />
          <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
          <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
          <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 8, color: 'var(--text-primary)' }} />
          <Line type="monotone" dataKey="score" stroke="#06b6d4" strokeWidth={3} dot={{ fill: '#06b6d4', r: 5 }} activeDot={{ r: 7, fill: '#6366f1' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import api from '../../services/api';

/**
 * BadgeDisplay — Shows earned badges with animations and progress hints.
 */

const BADGE_DEFINITIONS = {
  first_assessment: { icon: '🏆', color: '#f59e0b', glow: 'rgba(245, 158, 11, 0.3)' },
  goal_achieved: { icon: '🎯', color: '#10b981', glow: 'rgba(16, 185, 129, 0.3)' },
  strength_champion: { icon: '💪', color: '#ef4444', glow: 'rgba(239, 68, 68, 0.3)' },
  mental_warrior: { icon: '🧠', color: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.3)' },
  streak_master: { icon: '🔥', color: '#f97316', glow: 'rgba(249, 115, 22, 0.3)' },
  team_player: { icon: '🤝', color: '#06b6d4', glow: 'rgba(6, 182, 212, 0.3)' },
  speed_demon: { icon: '⚡', color: '#eab308', glow: 'rgba(234, 179, 8, 0.3)' },
  endurance_king: { icon: '🫁', color: '#22c55e', glow: 'rgba(34, 197, 94, 0.3)' },
  perfect_attendance: { icon: '📅', color: '#3b82f6', glow: 'rgba(59, 130, 246, 0.3)' },
};

export default function BadgeDisplay() {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/student/badges');
        setBadges(res.data);
      } catch (err) {
        console.error('Failed to load badges:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return null;

  return (
    <div className="card">
      <p className="card-title" style={{ margin: '0 0 12px' }}>🏅 Achievements</p>

      {badges.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '16px 0' }}>
          <p style={{ fontSize: '2rem', marginBottom: 8 }}>🎮</p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Complete assessments and goals to earn badges!
          </p>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12, flexWrap: 'wrap' }}>
            {Object.entries(BADGE_DEFINITIONS).slice(0, 5).map(([type, def]) => (
              <div key={type} className="badge-locked" title={type.replace('_', ' ')}>
                <span style={{ fontSize: '1.2rem', opacity: 0.3 }}>{def.icon}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="badge-grid">
          {badges.map((b, i) => {
            const def = BADGE_DEFINITIONS[b.badge_type] || { icon: '⭐', color: '#6366f1', glow: 'rgba(99, 102, 241, 0.3)' };
            return (
              <div key={b.id} className="badge-card" style={{
                '--badge-color': def.color,
                '--badge-glow': def.glow,
                animationDelay: `${i * 0.1}s`,
              }}>
                <div className="badge-icon-wrap">
                  <span className="badge-icon">{b.badge_name?.split(' ')[0] || def.icon}</span>
                </div>
                <p className="badge-name">{b.badge_name?.replace(/^[^\s]+\s/, '') || b.badge_type}</p>
                <p className="badge-desc">{b.description}</p>
                <p className="badge-date">{new Date(b.earned_at).toLocaleDateString()}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

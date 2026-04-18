import React, { useState } from 'react';
import api from '../../services/api';

export default function PrivacyTogglePanel({ studentId, initialPublic }) {
  const [isPublic, setIsPublic] = useState(initialPublic || false);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    setLoading(true);
    try {
      await api.patch(`/public/toggle-visibility?is_public=${!isPublic}`);
      setIsPublic(!isPublic);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ padding: 16 }}>
      <div className="privacy-toggle">
        <div
          className={`toggle-switch ${isPublic ? 'active' : ''}`}
          onClick={handleToggle}
          style={{ opacity: loading ? 0.5 : 1 }}
        />
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          Public Profile {isPublic ? '(Visible)' : '(Hidden)'}
        </span>
        {isPublic && (
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            — /profile/{studentId?.slice(0, 8)}...
          </span>
        )}
      </div>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 8, marginBottom: 0, lineHeight: 1.4 }}>
        {isPublic
          ? '🔓 Your profile is visible. Anyone with your unique link can see your performance score, radar chart, and top feature importances.'
          : '🔒 Your profile is hidden. Toggle on to generate a shareable link for coaches, teachers, or recruiters.'}
      </p>
    </div>
  );
}

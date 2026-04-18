import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { transformRadarData, transformPFIData } from '../services/chartTransforms';
import RadarChart from '../components/charts/RadarChart';
import PFIBarChart from '../components/charts/PFIBarChart';

export default function PublicProfilePage() {
  const { studentId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await axios.get(`/api/public/profile/${studentId}`);
        setProfile(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Profile not found or not public');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [studentId]);

  if (loading) {
    return <div className="loading-overlay"><div className="spinner"></div><p>Loading profile...</p></div>;
  }

  if (error) {
    return (
      <div className="public-profile" style={{ textAlign: 'center', paddingTop: 80 }}>
        <h2>🔒 Profile Not Available</h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>{error}</p>
      </div>
    );
  }

  const radarData = transformRadarData(profile.radar);
  const pfiData = transformPFIData(profile.pfi_top5);
  const grade = profile.performance_grade || 'N/A';

  return (
    <div>
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-logo">⚡ PE Assessment — Public Profile</div>
        </div>
      </nav>

      <div className="public-profile">
        <div className="public-profile-header">
          <h1>{profile.name}</h1>
          {profile.final_score !== null && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', marginBottom: 8 }}>
              Overall Score: <strong style={{ color: 'var(--text-primary)' }}>{profile.final_score}/100</strong>
            </p>
          )}
          <span className={`grade-badge ${grade}`}>Grade {grade}</span>
        </div>

        <div className="dashboard-grid">
          <RadarChart data={radarData} />
          <PFIBarChart data={pfiData} />
        </div>

        {profile.ai_summary && (
          <div className="card" style={{ marginTop: 20 }}>
            <p className="card-title">🤖 AI Assessment Summary</p>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>{profile.ai_summary}</p>
          </div>
        )}

        {/* Comparison Chart */}
        <div className="card" style={{ marginTop: 20 }}>
          <p className="card-title">📊 Our Framework vs Base Paper</p>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Aspect</th>
                <th className="base-paper">Base Paper</th>
                <th className="our-project">Our Framework</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>ML Method</td><td className="base-paper">Single BPNN</td><td className="our-project">BPNN + RF + XGBoost Ensemble</td></tr>
              <tr><td>Explainability</td><td className="base-paper">None</td><td className="our-project">PFI (Top 10 Features)</td></tr>
              <tr><td>Quiz Validation</td><td className="base-paper">Static</td><td className="our-project">Two-Tier Adaptive</td></tr>
              <tr><td>AI Recommendations</td><td className="base-paper">None</td><td className="our-project">Groq API (LLaMA3)</td></tr>
              <tr><td>Accuracy</td><td className="base-paper">~90%</td><td className="our-project">≥93%</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

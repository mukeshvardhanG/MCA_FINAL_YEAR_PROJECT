import React from 'react';

const PLACEHOLDER_INSIGHT = {
  summary: 'Complete an assessment and trigger a prediction to see your personalized AI insights here.',
  strengths: ['Your strengths will appear after your first assessment'],
  weaknesses: ['Areas for improvement will be identified by our AI engine'],
  action_steps: ['Submit physical metrics → Take quizzes → Generate prediction'],
  psych_guidance: 'Personalized psychological guidance will appear here based on your quiz results.',
  motivation: '"The journey of a thousand miles begins with a single step." — Lao Tzu',
};

const getYouTubeLink = (text) => {
  if (!text) return 'https://www.youtube.com/';
  const lower = text.toLowerCase();
  let query = 'physical+education+improvement+tips';
  if (lower.includes('sprint') || lower.includes('speed') || lower.includes('100m')) query = 'how+to+improve+sprint+speed+for+athletes';
  else if (lower.includes('strength') || lower.includes('push') || lower.includes('sit up')) query = 'strength+training+for+high+school+students';
  else if (lower.includes('endurance') || lower.includes('1500m') || lower.includes('run')) query = '1500m+running+tips+for+beginners';
  else if (lower.includes('flexibility') || lower.includes('stretch')) query = 'daily+stretching+routine+for+athletes';
  else if (lower.includes('coordination') || lower.includes('reaction')) query = 'sports+coordination+and+agility+drills';
  else query = encodeURIComponent(text + ' physical workout improvement');
  
  return `https://www.youtube.com/results?search_query=${query}`;
};

const isPhysicalWeakness = (text) => {
  const lower = text.toLowerCase();
  const physicalKeywords = ['sprint', 'speed', '100m', 'strength', 'push', 'sit up', 'squat', 'endurance', '1500m', 'run', 'flexibility', 'stretch', 'coordination', 'reaction', 'bmi', 'plank', 'breath', 'physical'];
  return physicalKeywords.some(kw => lower.includes(kw));
};

export default function AIInsightCard({ insight, confidence, pfiData }) {
  const displayInsight = insight || PLACEHOLDER_INSIGHT;
  const isPlaceholder = !insight;

  const rawConf = confidence || 91;
  let confText = 'Low';
  if (rawConf > 85) confText = 'High (High reliability)';
  else if (rawConf >= 70) confText = 'Medium (Acceptable reliability)';
  else confText = 'Low (High error margin)';

  let topStrengthText = "High motivation boosted your score";
  let topWeakText = "Lower teamwork reduced final grade";
  
  if (pfiData && pfiData.length >= 2) {
      topStrengthText = `High ${pfiData[0].name?.toLowerCase() || pfiData[0].feature_name} boosted score significantly`;
      topWeakText = `Lower ${pfiData[pfiData.length - 1].name?.toLowerCase() || pfiData[pfiData.length - 1].feature_name} reduced final grade`;
  }


  return (
    <div className="insight-card card" style={{ position: 'relative' }}>
      {isPlaceholder && (
        <div style={{
          position: 'absolute', top: 12, right: 12,
          padding: '3px 10px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 600,
          background: 'rgba(99,102,241,0.12)', color: 'var(--accent-primary, #6366f1)',
        }}>
          PREVIEW
        </div>
      )}

      <p className="card-title">🤖 {isPlaceholder ? 'AI Insights' : 'AI-Powered Insights'}</p>

      <div className="insight-section">
        <p className="insight-section-title">📊 Summary</p>
        <p style={{ fontWeight: 600, color: 'var(--accent-primary)', marginBottom: 6 }}>
          Prediction Confidence: {confText}
        </p>
        <p style={isPlaceholder ? { fontStyle: 'italic', color: 'var(--text-muted)' } : {}}>{displayInsight.summary}</p>
      </div>

      <div className="insight-section" style={{ background: 'rgba(16, 185, 129, 0.1)', padding: 12, borderRadius: 8, marginTop: 12, marginBottom: 12, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
        <p className="insight-section-title" style={{ margin: 0, marginBottom: 8 }}>🤔 Why this score?</p>
        <ul style={{ margin: 0, marginLeft: 16, fontSize: '0.85rem' }}>
          <li>{topStrengthText}</li>
          <li>{topWeakText}</li>
        </ul>
      </div>

      <div className="insight-section">
        <p className="insight-section-title">✅ Strengths</p>
        <ul>
          {(displayInsight.strengths || []).map((s, i) => <li key={i} style={isPlaceholder ? { color: 'var(--text-muted)' } : {}}>{s}</li>)}
        </ul>
      </div>

      <div className="insight-section">
        <p className="insight-section-title">⚠️ Areas to Improve</p>
        <ul style={{ paddingLeft: '20px' }}>
          {(displayInsight.weaknesses || []).map((w, i) => {
            const isPhysical = isPhysicalWeakness(w);
            return (
              <li key={i} style={isPlaceholder ? { color: 'var(--text-muted)', marginBottom: 8 } : { marginBottom: 8 }}>
                {w}
                {!isPlaceholder && isPhysical && (
                  <a 
                    href={getYouTubeLink(w)} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    style={{ marginLeft: 10, fontSize: '0.8rem', color: '#dc2626', textDecoration: 'none', fontWeight: 'bold', background: '#fee2e2', padding: '2px 8px', borderRadius: 12 }}>
                    ▶ Watch Training Protocol
                  </a>
                )}
              </li>
            );
          })}
        </ul>
        {/* Render explicit youtube recommendations from backend if present */}
        {!isPlaceholder && displayInsight.youtube_recommendations && displayInsight.youtube_recommendations.length > 0 && (
          <div style={{ marginTop: 12, background: 'rgba(239, 68, 68, 0.05)', padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            <p style={{ margin: 0, fontSize: '0.8rem', fontWeight: 600, color: '#dc2626', marginBottom: 6 }}>📺 AI Recommended Video Searches</p>
            <ul style={{ margin: 0, paddingLeft: 16, fontSize: '0.85rem' }}>
              {displayInsight.youtube_recommendations.map((yt, i) => (
                 <li key={`yt-${i}`} style={{ marginBottom: 4 }}>
                   <a href={`https://www.youtube.com/results?search_query=${encodeURIComponent(yt)}`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>{yt}</a>
                 </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="insight-section">
        <p className="insight-section-title">🎯 Action Steps</p>
        <ul>
          {(displayInsight.action_steps || []).map((a, i) => <li key={i} style={isPlaceholder ? { color: 'var(--text-muted)' } : {}}>{a}</li>)}
        </ul>
      </div>

      <div className="insight-section">
        <p className="insight-section-title">🧠 Psychological Guidance</p>
        <p style={isPlaceholder ? { fontStyle: 'italic', color: 'var(--text-muted)' } : {}}>
          {displayInsight.psych_guidance || 'Your mental resilience and motivation act as strong foundations. Continue to use positive visualization techniques before physical assessments to maintain peak performance.'}
        </p>
      </div>

      <div className="insight-section">
        <p className="insight-section-title">💬 Motivation</p>
        <p style={{ fontStyle: 'italic', color: isPlaceholder ? 'var(--text-muted)' : 'var(--accent-secondary)' }}>
          {displayInsight.motivation || '"The only bad workout is the one that didn\'t happen."'}
        </p>
      </div>
    </div>
  );
}

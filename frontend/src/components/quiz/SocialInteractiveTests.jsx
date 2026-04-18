import React, { useState, useCallback } from 'react';

// ═══════════════════════════════════════════════════════════
// TEST 1: EMOTION RECOGNITION
// ═══════════════════════════════════════════════════════════
function EmotionRecognitionTest({ onResult }) {
  const [phase, setPhase] = useState('ready'); // ready | playing | done
  const [round, setRound] = useState(0);
  const [score, setScore] = useState(0);
  const [feedback, setFeedback] = useState(null);

  const SCENARIOS = [
    { text: "A teammate continuously interrupts you during a presentation.", correct: "Frustration", options: ["Joy", "Sadness", "Frustration", "Fear"] },
    { text: "Your peer comes to you visibly shaking before a big exam.", correct: "Anxiety", options: ["Anger", "Anxiety", "Excitement", "Disgust"] },
    { text: "Your group project receives the top grade in the class.", correct: "Pride", options: ["Pride", "Guilt", "Jealousy", "Boredom"] },
    { text: "A friend admits they made a mistake that cost the team points.", correct: "Empathy", options: ["Rage", "Empathy", "Apathy", "Amusement"] },
    { text: "You notice someone sitting alone at lunch every day.", correct: "Compassion", options: ["Disgust", "Compassion", "Fear", "Pride"] },
  ];

  const handleChoose = (opt, correctOpt) => {
    if (feedback) return;
    const isCorrect = opt === correctOpt;
    setFeedback({ selected: opt, correct: isCorrect });
    
    if (isCorrect) setScore(s => s + 1);

    setTimeout(() => {
      if (round < SCENARIOS.length - 1) {
        setRound(r => r + 1);
        setFeedback(null);
      } else {
        const finalScore = Math.round(((score + (isCorrect ? 1 : 0)) / SCENARIOS.length) * 100);
        setPhase('done');
        onResult(finalScore);
      }
    }, 1200);
  };

  if (phase === 'done') {
    const finalScore = Math.round((score / SCENARIOS.length) * 100);
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🎭 Emotion Recognition</p>
        <p className="hb-result">{score}/{SCENARIOS.length}</p>
        <p className="hb-result-label">Score: {finalScore}/100</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span style={{ fontSize: '1.2rem' }}>🎭</span>
        <span style={{ fontWeight: 700 }}>Emotion Recognition</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Scenario {round + 1}/{SCENARIOS.length}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            Read the social scenario and identify the most appropriate feeling or response.
          </p>
          <button className="btn btn-primary" onClick={() => setPhase('playing')}>▶️ Start Test</button>
        </div>
      )}

      {phase === 'playing' && (
        <div>
          <div style={{ padding: '20px', background: 'var(--bg-input)', borderRadius: '8px', marginBottom: '20px', fontStyle: 'italic', textAlign: 'center' }}>
            "{SCENARIOS[round].text}"
          </div>
          <div className="pattern-options" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {SCENARIOS[round].options.map((opt, i) => {
              let btnClass = "btn btn-secondary";
              if (feedback) {
                if (opt === SCENARIOS[round].correct) btnClass += " correct";
                else if (opt === feedback.selected && !feedback.correct) btnClass += " wrong";
              }
              return (
                <button 
                  key={i} 
                  className={btnClass}
                  style={feedback ? { opacity: opt === SCENARIOS[round].correct ? 1 : 0.5 } : {}}
                  onClick={() => handleChoose(opt, SCENARIOS[round].correct)}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TEST 2: COOPERATIVE PLANNING (Replaces Trust Simulator)
// ═══════════════════════════════════════════════════════════
function CooperativePlanningTest({ onResult }) {
  const [phase, setPhase] = useState('ready'); // ready | playing | done
  const [round, setRound] = useState(0);
  const [score, setScore] = useState(0);
  const [feedback, setFeedback] = useState(null);

  const SCENARIOS = [
    { 
      text: "You and a peer are organizing a team event. They are suddenly overwhelmed with other work. What do you do?", 
      correct: "Offer to take on some of their tasks to ensure the event succeeds.", 
      options: [
        "Complain to the teacher that they aren't helping.", 
        "Offer to take on some of their tasks to ensure the event succeeds.", 
        "Do only your part and let the event fail if they can't finish.", 
        "Ignore the problem and hope they figure it out."
      ] 
    },
    { 
      text: "During a relay race, your teammate drops the baton and falls behind. How do you react?", 
      correct: "Encourage them to keep going and focus on doing your best on your leg.", 
      options: [
        "Yell at them for ruining the team's chances.", 
        "Give up since you can't win anymore.", 
        "Encourage them to keep going and focus on doing your best on your leg.", 
        "Demand that they be removed from the team next time."
      ] 
    },
    { 
      text: "Your group must decide on a strategy for a game, but you and another peer disagree. The rest of the team is neutral.", 
      correct: "Suggest a compromise that incorporates the best parts of both ideas.", 
      options: [
        "Refuse to play unless your strategy is chosen.", 
        "Suggest a compromise that incorporates the best parts of both ideas.", 
        "Quietly agree but don't try hard during the game.", 
        "Argue loudly until they give in."
      ] 
    },
  ];

  const handleChoose = (opt, correctOpt) => {
    if (feedback) return;
    const isCorrect = opt === correctOpt;
    setFeedback({ selected: opt, correct: isCorrect });
    
    if (isCorrect) setScore(s => s + 1);

    setTimeout(() => {
      if (round < SCENARIOS.length - 1) {
        setRound(r => r + 1);
        setFeedback(null);
      } else {
        const finalScore = Math.round(((score + (isCorrect ? 1 : 0)) / SCENARIOS.length) * 100);
        setPhase('done');
        onResult(finalScore);
      }
    }, 1500);
  };

  if (phase === 'done') {
    const finalScore = Math.round((score / SCENARIOS.length) * 100);
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🤝 Cooperative Planning</p>
        <p className="hb-result">{score}/{SCENARIOS.length} scenarios solved</p>
        <p className="hb-result-label">Cooperation Score: {finalScore}/100</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span style={{ fontSize: '1.2rem' }}>🤝</span>
        <span style={{ fontWeight: 700 }}>Peer Cooperation</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Scenario {round + 1}/{SCENARIOS.length}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            Read the team scenarios and choose the action that best supports your peers and the team goal.
          </p>
          <button className="btn btn-primary" onClick={() => setPhase('playing')}>▶️ Start Simulation</button>
        </div>
      )}

      {phase === 'playing' && (
        <div>
          <div style={{ padding: '20px', background: 'var(--bg-input)', borderRadius: '8px', marginBottom: '20px', fontStyle: 'italic', textAlign: 'center' }}>
            "{SCENARIOS[round].text}"
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px' }}>
            {SCENARIOS[round].options.map((opt, i) => {
              let btnClass = "btn btn-secondary";
              if (feedback) {
                if (opt === SCENARIOS[round].correct) btnClass += " correct";
                else if (opt === feedback.selected && !feedback.correct) btnClass += " wrong";
              }
              return (
                <button 
                  key={i} 
                  className={btnClass}
                  style={{ 
                    ...(feedback ? { opacity: opt === SCENARIOS[round].correct ? 1 : 0.5 } : {}),
                    textAlign: 'left', padding: '12px 16px'
                  }}
                  onClick={() => handleChoose(opt, SCENARIOS[round].correct)}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN ORCHESTRATOR
// ═══════════════════════════════════════════════════════════
export default function SocialInteractiveTests({ onComplete }) {
  const [currentTest, setCurrentTest] = useState(0); // 0=emotion, 1=trust
  const [results, setResults] = useState({});

  const testNames = ['🎭 Emotion Recognition', '🤝 Peer Cooperation'];

  const handleTestDone = (testKey, value) => {
    const newResults = { ...results, [testKey]: value };
    setResults(newResults);

    if (currentTest < 1) {
      setTimeout(() => setCurrentTest(currentTest + 1), 1000);
    } else {
      // All done — submit
      setTimeout(() => {
        onComplete({
          emotion_score: newResults.emotion_score || 50,
          trust_score: newResults.trust_score || 50,
        });
      }, 500);
    }
  };

  return (
    <div>
      {/* Progress indicators */}
      <div className="hb-progress">
        {testNames.map((name, i) => (
          <div key={i} className={`hb-step ${i < currentTest ? 'done' : i === currentTest ? 'active' : ''}`}>
            <span className="hb-step-dot">{i < currentTest ? '✓' : i + 1}</span>
            <span className="hb-step-label">{name}</span>
          </div>
        ))}
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', marginBottom: 12 }}>
        🤝 Social Assessment — Interactive Tier 2
      </p>

      {/* Current test */}
      {currentTest === 0 && (
        <EmotionRecognitionTest onResult={(v) => handleTestDone('emotion_score', v)} />
      )}
      {currentTest === 1 && (
        <CooperativePlanningTest onResult={(v) => handleTestDone('trust_score', v)} />
      )}
    </div>
  );
}

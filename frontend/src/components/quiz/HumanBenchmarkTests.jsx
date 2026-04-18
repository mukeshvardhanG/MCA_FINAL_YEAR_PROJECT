import React, { useState, useCallback } from 'react';

/**
 * HumanBenchmarkTests — Interactive cognitive and social tests for Tier 2.
 * 
 * Psychological: Memory Sequence, Pattern Recognition
 * Social: Emotion Recognition, Trust Simulator
 */

// ═══════════════════════════════════════════════════════════
// TEST 1: MEMORY SEQUENCE (Psychological)
// ═══════════════════════════════════════════════════════════
function MemorySequenceTest({ onResult }) {
  const [phase, setPhase] = useState('ready'); // ready | showing | input | done
  const [sequence, setSequence] = useState([]);
  const [userSeq, setUserSeq] = useState([]);
  const [showingIdx, setShowingIdx] = useState(-1);
  const [level, setLevel] = useState(3);
  const [maxLevel, setMaxLevel] = useState(0);
  const [flash, setFlash] = useState(-1);
  const GRID_SIZE = 9; // 3x3 grid

  const generateSequence = useCallback((len) => {
    const seq = [];
    while (seq.length < len) {
      const n = Math.floor(Math.random() * GRID_SIZE);
      if (seq[seq.length - 1] !== n) seq.push(n);
    }
    return seq;
  }, []);

  const startRound = useCallback(() => {
    const seq = generateSequence(level);
    setSequence(seq);
    setUserSeq([]);
    setPhase('showing');
    setShowingIdx(-1);

    seq.forEach((_, i) => {
      setTimeout(() => setShowingIdx(i), (i + 1) * 600);
    });
    setTimeout(() => {
      setShowingIdx(-1);
      setPhase('input');
    }, (seq.length + 1) * 600);
  }, [level, generateSequence]);

  const handleTileClick = (idx) => {
    if (phase !== 'input') return;
    setFlash(idx);
    setTimeout(() => setFlash(-1), 200);

    const newUserSeq = [...userSeq, idx];
    setUserSeq(newUserSeq);

    if (newUserSeq[newUserSeq.length - 1] !== sequence[newUserSeq.length - 1]) {
      const score = Math.round((maxLevel / 9) * 100);
      setPhase('done');
      onResult(Math.max(score, Math.round(((level - 1) / 9) * 100)));
      return;
    }

    if (newUserSeq.length === sequence.length) {
      const newMax = Math.max(maxLevel, level);
      setMaxLevel(newMax);
      if (level >= 9) {
        setPhase('done');
        onResult(100);
      } else {
        setLevel(level + 1);
        setTimeout(() => startRound(), 500);
      }
    }
  };

  if (phase === 'done') {
    const score = Math.round((Math.max(maxLevel, level - 1) / 9) * 100);
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🧠 Memory Sequence</p>
        <p className="hb-result">{Math.max(maxLevel, level - 1)} tiles</p>
        <p className="hb-result-label">Score: {score}/100</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span style={{ fontSize: '1.2rem' }}>🧠</span>
        <span style={{ fontWeight: 700 }}>Memory Sequence</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Level {level}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            Watch the tiles light up, then repeat the sequence!
          </p>
          <button className="btn btn-primary" onClick={startRound}>▶️ Start Memory Test</button>
        </div>
      )}

      {(phase === 'showing' || phase === 'input') && (
        <>
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: 8 }}>
            {phase === 'showing' ? '👀 Watch carefully...' : `🖱️ Your turn! (${userSeq.length}/${sequence.length})`}
          </p>
          <div className="memory-grid">
            {Array.from({ length: GRID_SIZE }).map((_, i) => (
              <div key={i}
                className={`memory-tile ${
                  (phase === 'showing' && sequence[showingIdx] === i) ? 'active' :
                  flash === i ? 'flash' : ''
                }`}
                onClick={() => handleTileClick(i)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TEST 2: PATTERN RECOGNITION (Psychological)
// ═══════════════════════════════════════════════════════════
function PatternRecognitionTest({ onResult }) {
  const [phase, setPhase] = useState('ready'); // ready | playing | done
  const [round, setRound] = useState(0);
  const [score, setScore] = useState(0);
  const [pattern, setPattern] = useState(null);
  const [options, setOptions] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const totalRounds = 8;

  const SHAPES = ['●', '▲', '■', '◆', '★', '⬟', '⬢', '⬡'];
  const COLORS = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

  const generatePattern = useCallback(() => {
    const len = Math.min(3 + Math.floor(round / 2), 6);
    const seq = [];
    for (let i = 0; i < len; i++) {
      seq.push({
        shape: SHAPES[Math.floor(Math.random() * SHAPES.length)],
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      });
    }
    return seq;
  }, [round]);

  const startRound = useCallback(() => {
    const pat = generatePattern();
    setPattern(pat);

    const opts = [];
    for (let i = 0; i < 3; i++) {
      const wrong = pat.map(p => ({
        shape: Math.random() > 0.5 ? SHAPES[Math.floor(Math.random() * SHAPES.length)] : p.shape,
        color: Math.random() > 0.5 ? COLORS[Math.floor(Math.random() * COLORS.length)] : p.color,
      }));
      if (JSON.stringify(wrong) !== JSON.stringify(pat)) {
        opts.push({ items: wrong, correct: false });
      } else {
        opts.push({ items: wrong.map(p => ({ ...p, shape: SHAPES[(SHAPES.indexOf(p.shape) + 1) % SHAPES.length] })), correct: false });
      }
    }
    const correctIdx = Math.floor(Math.random() * 4);
    opts.splice(correctIdx, 0, { items: pat, correct: true });
    setOptions(opts);
    setFeedback(null);
    setPhase('playing');
  }, [generatePattern]);

  const handleChoose = (opt, idx) => {
    if (feedback !== null) return;
    const isCorrect = opt.correct;
    setFeedback({ idx, correct: isCorrect });
    if (isCorrect) setScore(s => s + 1);

    setTimeout(() => {
      const nextRound = round + 1;
      if (nextRound >= totalRounds) {
        setPhase('done');
        onResult(Math.round(((score + (isCorrect ? 1 : 0)) / totalRounds) * 100));
      } else {
        setRound(nextRound);
        startRound();
      }
    }, 800);
  };

  if (phase === 'done') {
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🔍 Pattern Recognition</p>
        <p className="hb-result">{score}/{totalRounds}</p>
        <p className="hb-result-label">Score: {Math.round((score / totalRounds) * 100)}/100</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span style={{ fontSize: '1.2rem' }}>🔍</span>
        <span style={{ fontWeight: 700 }}>Pattern Recognition</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Round {round + 1}/{totalRounds}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            Find the option that matches the pattern exactly!
          </p>
          <button className="btn btn-primary" onClick={startRound}>▶️ Start Pattern Test</button>
        </div>
      )}

      {phase === 'playing' && pattern && (
        <>
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', margin: '8px 0' }}>
            Find the matching pattern:
          </p>
          <div className="pattern-target">
            {pattern.map((p, i) => (
              <span key={i} style={{ color: p.color, fontSize: '1.8rem' }}>{p.shape}</span>
            ))}
          </div>
          <div className="pattern-options">
            {options.map((opt, idx) => (
              <div key={idx}
                className={`pattern-option ${
                  feedback !== null && feedback.idx === idx
                    ? (feedback.correct ? 'correct' : 'wrong')
                    : feedback !== null && opt.correct ? 'show-correct' : ''
                }`}
                onClick={() => handleChoose(opt, idx)}>
                {opt.items.map((p, i) => (
                  <span key={i} style={{ color: p.color, fontSize: '1.4rem' }}>{p.shape}</span>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TEST 3: EMOTION RECOGNITION (Social)
// ═══════════════════════════════════════════════════════════
function EmotionRecognitionTest({ onResult }) {
  const [phase, setPhase] = useState('ready');
  const [round, setRound] = useState(0);
  const [score, setScore] = useState(0);
  const [startTime, setStartTime] = useState(0);
  const totalRounds = 6;

  const SCENARIOS = [
    { text: "A teammate makes a small mistake and looks down at their feet.", correct: "Seeking Support", options: ["Angry", "Seeking Support", "Arrogant", "Indifferent"] },
    { text: "The team captain is giving a pep talk with a loud, firm voice and wide-eyes.", correct: "Passionate", options: ["Bored", "Passionate", "Sad", "Afraid"] },
    { text: "A peer refuses to pass the ball and avoids eye contact with everyone.", correct: "Frustrated", options: ["Happy", "Frustrated", "Content", "Excited"] },
    { text: "A classmate cheers loudly when you succeed, with a genuine wide smile.", correct: "Empathetic", options: ["Envious", "Empathetic", "Confused", "Hostile"] },
    { text: "An opponent offers a high-five after a tough match despite losing.", correct: "Respectful", options: ["Respectful", "Sarcastic", "Jealous", "Deceptive"] },
    { text: "A teammate is sitting alone on the bench while others are celebrating.", correct: "Isolated", options: ["Confident", "Isolated", "Irritated", "Greedy"] },
  ];

  const handleChoice = (choice) => {
    const isCorrect = choice === SCENARIOS[round].correct;
    // Speed bonus calculation (within 3 seconds)
    const duration = Date.now() - startTime;
    const speedBonus = isCorrect ? Math.max(0, (5000 - duration) / 500) : 0;
    
    if (isCorrect) setScore(s => s + 10 + speedBonus);

    if (round + 1 < totalRounds) {
      setRound(round + 1);
      setStartTime(Date.now());
    } else {
      setPhase('done');
      onResult(Math.min(100, Math.round(((score + (isCorrect ? 10 + speedBonus : 0)) / 90) * 100)));
    }
  };

  const startTest = () => {
    setPhase('playing');
    setStartTime(Date.now());
  };

  if (phase === 'done') {
    const finalScore = Math.min(100, Math.round((score / 90) * 100));
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🤝 Emotion Recognition</p>
        <p className="hb-result">{Math.round(score)} pts</p>
        <p className="hb-result-label">Social Sensitivity: {finalScore}%</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span>🎭</span>
        <span style={{ fontWeight: 700 }}>Emotion Recognition</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{round + 1}/{totalRounds}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            Identify the underlying emotion or social cue in each scenario as quickly as possible.
          </p>
          <button className="btn btn-primary" onClick={startTest}>▶️ Start Test</button>
        </div>
      )}

      {phase === 'playing' && (
        <div style={{ padding: '0 12px 16px' }}>
          <div className="scenario-box" style={{ background: 'var(--bg-elevated)', padding: 20, borderRadius: 12, marginBottom: 20, border: '1px solid var(--border-color)', minHeight: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <p style={{ fontSize: '1.1rem', lineHeight: 1.5 }}>"{SCENARIOS[round].text}"</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {SCENARIOS[round].options.map(opt => (
              <button key={opt} className="btn btn-secondary" style={{ padding: '12px 8px' }} onClick={() => handleChoice(opt)}>
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TEST 4: TRUST SIMULATOR (Social)
// ═══════════════════════════════════════════════════════════
function TrustSimulatorTest({ onResult }) {
  const [phase, setPhase] = useState('ready');
  const [round, setRound] = useState(0);
  const [totalScore, setTotalScore] = useState(0);
  const rounds = 4;

  const handleContribute = (amount) => {
    // Simulated peer contributions (random but slightly biased towards user behavior)
    const peerContribution = Math.floor(Math.random() * 8) + (amount > 5 ? 2 : 0);
    const pool = (amount + peerContribution) * 2;
    const share = pool / 2;
    const roundGain = (10 - amount) + share;

    setTotalScore(s => s + roundGain);

    if (round + 1 < rounds) {
      setRound(round + 1);
    } else {
      setPhase('done');
      // Normalize: max score approx 60 pts total
      onResult(Math.min(100, Math.round(((totalScore + roundGain) / 60) * 100)));
    }
  };

  if (phase === 'done') {
    const finalScore = Math.min(100, Math.round((totalScore / 60) * 100));
    return (
      <div className="hb-test-done">
        <p className="hb-test-title">🪙 Trust Simulator</p>
        <p className="hb-result">Team Harmony: {finalScore}%</p>
        <p className="hb-result-label">Collaboration Score: {finalScore}/100</p>
      </div>
    );
  }

  return (
    <div className="hb-test-container">
      <div className="hb-test-header">
        <span>🪙</span>
        <span style={{ fontWeight: 700 }}>Trust Simulator</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Round {round + 1}/{rounds}</span>
      </div>

      {phase === 'ready' && (
        <div style={{ textAlign: 'center', padding: 16 }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
            You have 10 coins. Choose how many to contribute to the Team Pool. 
            The pool is doubled and shared equally!
          </p>
          <button className="btn btn-primary" onClick={() => setPhase('playing')}>▶️ Start Simulator</button>
        </div>
      )}

      {phase === 'playing' && (
        <div style={{ textAlign: 'center', padding: '0 12px 16px' }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 20 }}>
            How many coins will you contribute?
          </p>
          <div className="grid grid-cols-3 gap-2">
            {[0, 2, 5, 7, 10].map(amt => (
              <button key={amt} className="btn btn-secondary" onClick={() => handleContribute(amt)}>
                {amt} Coins
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN ORCHESTRATOR
// ═══════════════════════════════════════════════════════════
export default function HumanBenchmarkTests({ quizType, onComplete }) {
  const [currentTest, setCurrentTest] = useState(0);
  const [results, setResults] = useState({});

  const psychTests = ['🧠 Memory Sequence', '🔍 Pattern Recognition'];
  const socialTests = ['🎭 Emotion Recognition', '🪙 Trust Simulator'];
  const testNames = quizType === 'psychological' ? psychTests : socialTests;

  const handleTestDone = (testKey, value) => {
    const newResults = { ...results, [testKey]: value };
    setResults(newResults);

    if (currentTest < 1) {
      setTimeout(() => setCurrentTest(currentTest + 1), 1000);
    } else {
      setTimeout(() => {
        if (quizType === 'psychological') {
          onComplete({
            memory_score: newResults.memory || 50,
            pattern_score: newResults.pattern || 50,
          });
        } else {
          onComplete({
            emotion_score: newResults.emotion || 50,
            trust_score: newResults.trust || 50,
          });
        }
      }, 500);
    }
  };

  return (
    <div className="human-benchmark-root">
      <div className="hb-progress">
        {testNames.map((name, i) => (
          <div key={i} className={`hb-step ${i < currentTest ? 'done' : i === currentTest ? 'active' : ''}`}>
            <span className="hb-step-dot">{i < currentTest ? '✓' : i + 1}</span>
            <span className="hb-step-label">{name}</span>
          </div>
        ))}
      </div>

      <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', marginBottom: 12 }}>
        {quizType === 'psychological' ? '🧠 Psychological' : '🤝 Social'} Assessment — Tier 2 Games
      </p>

      {quizType === 'psychological' ? (
        <>
          {currentTest === 0 && <MemorySequenceTest onResult={(v) => handleTestDone('memory', v)} />}
          {currentTest === 1 && <PatternRecognitionTest onResult={(v) => handleTestDone('pattern', v)} />}
        </>
      ) : (
        <>
          {currentTest === 0 && <EmotionRecognitionTest onResult={(v) => handleTestDone('emotion', v)} />}
          {currentTest === 1 && <TrustSimulatorTest onResult={(v) => handleTestDone('trust', v)} />}
        </>
      )}
    </div>
  );
}

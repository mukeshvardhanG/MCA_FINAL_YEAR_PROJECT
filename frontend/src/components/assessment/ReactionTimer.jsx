import React, { useState, useRef, useEffect } from 'react';

export default function ReactionTimer({ value, onResult }) {
  const [phase, setPhase] = useState('ready'); // ready | waiting | go | done
  const [times, setTimes] = useState([]);
  const [current, setCurrent] = useState(null);
  const [tooEarly, setTooEarly] = useState(false);
  const timeoutRef = useRef(null);
  const startRef = useRef(null);
  const round = times.length + 1;
  const totalRounds = 3; // 3 rounds for a quick average

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  const startWaiting = () => {
    setPhase('waiting');
    setTooEarly(false);
    const delay = 1500 + Math.random() * 3000; // 1.5 - 4.5s
    timeoutRef.current = setTimeout(() => {
      setPhase('go');
      startRef.current = performance.now();
    }, delay);
  };

  const handleClick = (e) => {
    e.preventDefault();
    if (phase === 'ready') {
      startWaiting();
    } else if (phase === 'waiting') {
      clearTimeout(timeoutRef.current);
      setTooEarly(true);
      setPhase('ready');
    } else if (phase === 'go') {
      const elapsed = Math.round(performance.now() - startRef.current);
      setCurrent(elapsed);
      const newTimes = [...times, elapsed];
      setTimes(newTimes);
      if (newTimes.length >= totalRounds) {
        const avg = Math.round(newTimes.reduce((a, b) => a + b, 0) / newTimes.length);
        setPhase('done');
        onResult(avg);
      } else {
        setPhase('ready');
      }
    }
  };

  const reset = (e) => {
    e.preventDefault();
    setPhase('ready');
    setTimes([]);
    setCurrent(null);
    setTooEarly(false);
    onResult('');
  };

  const getColor = () => {
    if (phase === 'waiting') return 'var(--accent-danger, #ef4444)';
    if (phase === 'go') return 'var(--accent-success, #10b981)';
    return 'var(--bg-input)';
  };

  if (phase === 'done') {
    return (
      <div style={{ background: 'var(--bg-elevated)', padding: '16px', borderRadius: '8px', textAlign: 'center', border: '1px solid var(--accent-success, #10b981)' }}>
        <p style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--accent-success)' }}>⚡ {value}ms</p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average Reaction Time (Saved)</p>
        <button className="btn btn-secondary btn-sm" onClick={reset} style={{ marginTop: 8 }}>Retake Test</button>
      </div>
    );
  }

  return (
    <div 
      style={{ 
        background: getColor(), 
        cursor: 'pointer', 
        padding: '30px 16px', 
        borderRadius: '8px', 
        textAlign: 'center',
        border: `1px solid ${phase === 'waiting' || phase === 'go' ? 'transparent' : 'var(--border-color)'}`,
        transition: 'background-color 0.1s ease',
        minHeight: '120px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}
      onClick={handleClick}
    >
      {phase === 'ready' && (
        <>
          <p style={{ fontSize: '1.5rem', marginBottom: 4 }}>⚡</p>
          <p style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)' }}>Reaction Time Test</p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            {tooEarly ? '⚠️ Too early! Click to try again.' : `Click to start (Round ${round}/${totalRounds})`}
          </p>
          {current && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 8 }}>Last round: {current}ms</p>
          )}
        </>
      )}
      {phase === 'waiting' && (
        <p style={{ fontSize: '1.2rem', fontWeight: 700, color: 'white' }}>Wait for green...</p>
      )}
      {phase === 'go' && (
        <p style={{ fontSize: '1.5rem', fontWeight: 900, color: 'white' }}>CLICK NOW!</p>
      )}
    </div>
  );
}

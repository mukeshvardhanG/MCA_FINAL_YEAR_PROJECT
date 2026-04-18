import React, { useState, useRef, useCallback, useEffect } from 'react';

/**
 * InteractiveTimer — Reusable stopwatch for breath hold and plank hold tests.
 * Props:
 *   label: string (e.g. "Breath Hold" or "Plank Hold")
 *   icon: string emoji
 *   description: string
 *   onResult: (seconds: number) => void
 *   maxSeconds: number (safety limit)
 *   value: number (current value if already recorded)
 */
export default function InteractiveTimer({ label, icon, description, onResult, maxSeconds = 300, value }) {
  const [phase, setPhase] = useState(value ? 'done' : 'idle'); // idle | countdown | running | done
  const [elapsed, setElapsed] = useState(value || 0);
  const [countdown, setCountdown] = useState(3);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const startCountdown = () => {
    setPhase('countdown');
    setCountdown(3);
    let count = 3;
    intervalRef.current = setInterval(() => {
      count--;
      if (count <= 0) {
        cleanup();
        startTimer();
      } else {
        setCountdown(count);
      }
    }, 1000);
  };

  const startTimer = () => {
    setPhase('running');
    setElapsed(0);
    startTimeRef.current = Date.now();
    intervalRef.current = setInterval(() => {
      const secs = (Date.now() - startTimeRef.current) / 1000;
      if (secs >= maxSeconds) {
        stopTimer(maxSeconds);
      } else {
        setElapsed(parseFloat(secs.toFixed(1)));
      }
    }, 100);
  };

  const stopTimer = (overrideSecs) => {
    cleanup();
    const finalSecs = overrideSecs ?? parseFloat(((Date.now() - startTimeRef.current) / 1000).toFixed(1));
    setElapsed(finalSecs);
    setPhase('done');
    onResult(finalSecs);
  };

  const reset = () => {
    cleanup();
    setPhase('idle');
    setElapsed(0);
    onResult(0);
  };

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = Math.floor(s % 60);
    const tenths = Math.floor((s % 1) * 10);
    return mins > 0
      ? `${mins}:${secs.toString().padStart(2, '0')}.${tenths}`
      : `${secs}.${tenths}s`;
  };

  return (
    <div className={`timer-card ${phase}`}>
      <div className="timer-header">
        <span className="timer-icon">{icon}</span>
        <span className="timer-label">{label}</span>
      </div>

      <div className="timer-display">
        {phase === 'countdown' && (
          <div className="timer-countdown">{countdown}</div>
        )}
        {phase === 'idle' && (
          <div className="timer-value idle">0.0s</div>
        )}
        {phase === 'running' && (
          <div className="timer-value running">{formatTime(elapsed)}</div>
        )}
        {phase === 'done' && (
          <div className="timer-value done">{formatTime(elapsed)}</div>
        )}
      </div>

      <p className="timer-desc">{description}</p>

      <div className="timer-actions">
        {phase === 'idle' && (
          <button className="btn btn-primary timer-btn" onClick={startCountdown}>
            ▶️ Start Test
          </button>
        )}
        {phase === 'countdown' && (
          <button className="btn btn-secondary timer-btn" disabled>
            Get Ready...
          </button>
        )}
        {phase === 'running' && (
          <button className="btn btn-danger timer-btn pulse" onClick={() => stopTimer()}>
            ⏹️ Stop
          </button>
        )}
        {phase === 'done' && (
          <button className="btn btn-secondary timer-btn" onClick={reset}>
            🔄 Retry
          </button>
        )}
      </div>

      {/* Progress ring for running state */}
      {phase === 'running' && (
        <div className="timer-progress">
          <div className="timer-ring" style={{
            background: `conic-gradient(var(--accent-primary) ${(elapsed / maxSeconds) * 360}deg, transparent 0deg)`
          }} />
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import api from '../../services/api';
import { extractErrorMessage } from '../../services/errorUtils';
import InteractiveTimer from './InteractiveTimer';
import ReactionTimer from './ReactionTimer';

const EXERCISE_FIELDS = [
  { id: 'push_ups', label: '💪 Push-ups (count)', min: 0, max: 200, step: 1, placeholder: '25' },
  { id: 'squats', label: '🦵 Squats (count)', min: 0, max: 200, step: 1, placeholder: '30' },
  { id: 'sit_ups', label: '🏋️ Sit-ups (count)', min: 0, max: 200, step: 1, placeholder: '20' },
];

const BODY_FIELDS = [
  { id: 'height_cm', label: '📏 Height (cm)', min: 100, max: 250, step: 0.1, placeholder: '170' },
  { id: 'weight_kg', label: '⚖️ Weight (kg)', min: 20, max: 200, step: 0.1, placeholder: '65' },
];

const OTHER_FIELDS = [
  { id: 'running_speed_100m', label: '🏃 100m Sprint (seconds)', min: 9, max: 25, step: 0.1, placeholder: '13.5' },
  { id: 'endurance_1500m', label: '🏃‍♂️ 1500m Run (minutes)', min: 4, max: 15, step: 0.1, placeholder: '7.5' },
];

const ALL_INPUT_FIELDS = [...EXERCISE_FIELDS, ...BODY_FIELDS, ...OTHER_FIELDS];

function calcStrength(pushUps, squats, sitUps) {
  const p = Math.min(pushUps || 0, 100);
  const sq = Math.min(squats || 0, 100);
  const si = Math.min(sitUps || 0, 100);
  return Math.min(100, Math.round((p + sq + si) / 3));
}

function calcBMI(heightCm, weightKg) {
  if (!heightCm || !weightKg || heightCm <= 0) return 0;
  const heightM = heightCm / 100;
  return Math.round((weightKg / (heightM * heightM)) * 10) / 10;
}

export default function PhysicalMetricsForm({ onSubmit }) {
  const [form, setForm] = useState({});
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [plankHold, setPlankHold] = useState(0);
  const [breathHold, setBreathHold] = useState(0);
  const [hasExisting, setHasExisting] = useState(false);

  React.useEffect(() => {
    const loadExisting = async () => {
      try {
        const res = await api.get('/assessments/');
        if (res.data && res.data.length > 0) {
          const latest = res.data[0];
          setForm({
            push_ups: latest.push_ups,
            squats: latest.squats,
            sit_ups: latest.sit_ups,
            height_cm: latest.height_cm,
            weight_kg: latest.weight_kg,
            running_speed_100m: latest.running_speed_100m,
            endurance_1500m: latest.endurance_1500m,
            reaction_time_ms: latest.reaction_time_ms,
          });
          setPlankHold(latest.plank_hold_seconds || 0);
          setBreathHold(latest.breath_hold_seconds || 0);
          setHasExisting(true);
        }
      } catch (err) {
        console.error("Failed to load existing metrics", err);
      }
    };
    loadExisting();
  }, []);

  const strengthScore = calcStrength(
    parseInt(form.push_ups), parseInt(form.squats), parseInt(form.sit_ups)
  );
  const bmiValue = calcBMI(parseFloat(form.height_cm), parseFloat(form.weight_kg));

  const validate = () => {
    const errs = {};
    for (const field of ALL_INPUT_FIELDS) {
      const val = parseFloat(form[field.id]);
      if (isNaN(val)) { errs[field.id] = 'Required'; continue; }
      if (val < field.min || val > field.max) {
        errs[field.id] = `Range: ${field.min}–${field.max}`;
      }
    }
    if (bmiValue < 10 || bmiValue > 60) {
      errs['weight_kg'] = 'BMI out of range — check height/weight';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const payload = {
        running_speed_100m: parseFloat(form.running_speed_100m),
        endurance_1500m: parseFloat(form.endurance_1500m),
        push_ups: parseInt(form.push_ups),
        squats: parseInt(form.squats),
        sit_ups: parseInt(form.sit_ups),
        height_cm: parseFloat(form.height_cm),
        weight_kg: parseFloat(form.weight_kg),
        strength_score: strengthScore,
        bmi: bmiValue,
        reaction_time_ms: parseFloat(form.reaction_time_ms),
        plank_hold_seconds: plankHold,
        breath_hold_seconds: breathHold,
      };
      const res = await api.post('/assessments/', payload);
      onSubmit(res.data.assessment_id);
    } catch (err) {
      alert(extractErrorMessage(err, 'Failed to submit metrics'));
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (f) => (
    <div key={f.id} className="form-group">
      <label className="form-label">{f.label}</label>
      <input className="form-input" type="number" step={f.step} min={f.min} max={f.max}
        placeholder={f.placeholder}
        value={form[f.id] || ''}
        onChange={(e) => setForm({ ...form, [f.id]: e.target.value })} />
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4, marginBottom: 0 }}>
        Valid range: {f.min} – {f.max}
      </p>
      {errors[f.id] && <p className="form-error" style={{ marginTop: 2 }}>{errors[f.id]}</p>}
    </div>
  );

  return (
    <div className="card">
      <p className="card-title">📏 Physical Metrics — Tier 1</p>
      <form onSubmit={handleSubmit}>
        {/* Strength exercises */}
        <p style={{ color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 8, marginTop: 12 }}>💪 Strength Exercises</p>
        <div className="metrics-form-grid">
          {EXERCISE_FIELDS.map(renderField)}
        </div>
        {/* Computed strength */}
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', margin: '12px 0', padding: '10px 14px', background: 'var(--bg-elevated, rgba(99,102,241,0.08))', borderRadius: 8 }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Computed Strength Score:</span>
          <span style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-primary, #6366f1)' }}>{strengthScore}/100</span>
        </div>

        {/* Body metrics */}
        <p style={{ color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 8, marginTop: 16 }}>⚖️ Body Metrics</p>
        <div className="metrics-form-grid">
          {BODY_FIELDS.map(renderField)}
        </div>
        {/* Computed BMI */}
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', margin: '12px 0', padding: '10px 14px', background: 'var(--bg-elevated, rgba(99,102,241,0.08))', borderRadius: 8 }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Calculated BMI:</span>
          <span style={{ fontSize: '1.3rem', fontWeight: 700, color: bmiValue >= 18.5 && bmiValue <= 25 ? 'var(--accent-success, #10b981)' : 'var(--accent-warning, #f59e0b)' }}>
            {bmiValue > 0 ? bmiValue : '—'}
          </span>
          {bmiValue > 0 && (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {bmiValue < 18.5 ? '(Underweight)' : bmiValue <= 25 ? '(Normal)' : bmiValue <= 30 ? '(Overweight)' : '(Obese)'}
            </span>
          )}
        </div>

        {/* Other metrics */}
        <p style={{ color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 8, marginTop: 16 }}>🏃 Speed, Endurance & Reaction</p>
        <div className="metrics-form-grid">
          {OTHER_FIELDS.map(renderField)}
        </div>
        {/* Reaction time built-in test */}
        <div style={{ margin: '16px 0', padding: '16px', background: 'var(--bg-elevated, rgba(6,182,212,0.08))', borderRadius: 8 }}>
          <p style={{ color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 8 }}>⚡ Reaction Time</p>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 12 }}>
            Measure your reaction time directly within this form. The average of 3 rounds will be saved automatically.
          </p>
          <ReactionTimer 
            value={form.reaction_time_ms} 
            onResult={(val) => setForm({ ...form, reaction_time_ms: val })} 
          />
          {errors.reaction_time_ms && <p className="form-error" style={{ marginTop: 8 }}>{errors.reaction_time_ms}</p>}
        </div>

        {/* Integrated Physical Tests */}
        <p style={{ color: 'var(--text-secondary)', fontWeight: 600, marginBottom: 8, marginTop: 16 }}>🧪 Integrated Physical Tests (Optional)</p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: 12 }}>
          Use the built-in timers below to measure your breath hold and plank hold. Click Start, perform the test, then click Stop.
        </p>
        <div className="timer-grid">
          <InteractiveTimer
            label="Breath Hold"
            icon="🌬️"
            description="Take a deep breath, click Start, and hold as long as you can."
            maxSeconds={300}
            value={breathHold}
            onResult={setBreathHold}
          />
          <InteractiveTimer
            label="Plank Hold"
            icon="🧱"
            description="Get in plank position, click Start, and hold until you can't."
            maxSeconds={600}
            value={plankHold}
            onResult={setPlankHold}
          />
        </div>

        <button className="btn btn-primary" type="submit" disabled={submitting} style={{ marginTop: 16 }}>
          {submitting ? <span className="spinner" style={{ width: 16, height: 16 }}></span> : (hasExisting ? '💾 Update Metrics' : '💾 Save Metrics')}
        </button>
      </form>
    </div>
  );
}


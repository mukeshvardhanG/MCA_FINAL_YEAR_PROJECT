import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';

/**
 * Polls /predict/{assessmentId}/status every 3s until status = 'complete' or 'failed'
 */
export function usePrediction() {
  const [status, setStatus] = useState(null);
  const [predictionId, setPredictionId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const triggerPrediction = useCallback(async (assessmentId) => {
    setStatus('processing');
    setError(null);
    setResult(null);

    try {
      const res = await api.post(`/predict/${assessmentId}`);
      setPredictionId(res.data.prediction_id);

      // Start polling
      intervalRef.current = setInterval(async () => {
        try {
          const pollRes = await api.get(`/predict/${assessmentId}/status`);
          const data = pollRes.data;

          if (data.status === 'complete') {
            setStatus('complete');
            setResult(data);
            clearInterval(intervalRef.current);
          } else if (data.status === 'failed') {
            setStatus('failed');
            setError('Prediction failed');
            clearInterval(intervalRef.current);
          }
        } catch (e) {
          // Keep polling unless server is down
          console.error('Poll error:', e);
        }
      }, 3000);
    } catch (err) {
      setStatus('failed');
      setError(err.response?.data?.detail || 'Failed to trigger prediction');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { status, predictionId, result, error, triggerPrediction };
}

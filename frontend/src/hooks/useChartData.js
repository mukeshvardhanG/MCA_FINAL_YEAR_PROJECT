import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { transformRadarData, transformTrendData, transformPFIData } from '../services/chartTransforms';

/**
 * Fetches and transforms dashboard data for charts
 */
export function useChartData(studentId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    if (!studentId) return;
    setLoading(true);
    try {
      const res = await api.get(`/dashboard-data/${studentId}`);
      const raw = res.data;
      setData({
        current: raw.current,
        assessmentDate: raw.assessment_date,
        radar: transformRadarData(raw.radar),
        trend: transformTrendData(raw.trend),
        pfi: transformPFIData(raw.pfi),
        insight: raw.insight,
        rawRadar: raw.radar,
        classAvg: raw.class_avg_score,
        percentileRank: raw.percentile_rank,
      });
    } catch (err) {
      console.error('Dashboard data fetch/transform error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

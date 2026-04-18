/**
 * chartTransforms.js — Converts raw API response → Recharts-compatible format
 */

/**
 * Transform radar data for Recharts RadarChart (6 axes)
 * @param {Object} radar - { physical_avg, psychological_avg, social_avg, cognitive_avg, technical_avg, behavioral_avg }
 * @returns {Array} - Recharts-compatible data array
 */
export function transformRadarData(radar) {
  if (!radar) return [];
  return [
    { subject: 'Physical', value: radar.physical_avg || 0, fullMark: 10 },
    { subject: 'Psychological', value: radar.psychological_avg || 0, fullMark: 10 },
    { subject: 'Social', value: radar.social_avg || 0, fullMark: 10 },
    { subject: 'Cognitive', value: radar.cognitive_avg || 0, fullMark: 10 },
    { subject: 'Technical', value: radar.technical_avg || 0, fullMark: 10 },
    { subject: 'Behavioral', value: radar.behavioral_avg || 0, fullMark: 10 },
  ];
}

/**
 * Transform trend data for Recharts LineChart
 * @param {Array} trend - [{ semester, score }]
 * @returns {Array} - Recharts-compatible data array
 */
export function transformTrendData(trend) {
  if (!trend || !trend.length) return [];
  return trend.map((t) => ({
    name: t.semester,
    score: Number(t.score?.toFixed(1)),
  }));
}

/**
 * Transform PFI data for Recharts horizontal BarChart (with error bars)
 * @param {Array} pfi - [{ feature_name, importance_score, rank, std_dev }]
 * @returns {Array} - Recharts-compatible data array (top 10, reversed for horizontal)
 */
export function transformPFIData(pfi) {
  if (!pfi || !pfi.length) return [];
  return pfi
    .slice(0, 10)
    .reverse()
    .map((p) => ({
      name: p.feature_name,
      importance: Number(p.importance_score?.toFixed(4)),
      error: Number((p.std_dev || 0).toFixed(4)),
    }));
}


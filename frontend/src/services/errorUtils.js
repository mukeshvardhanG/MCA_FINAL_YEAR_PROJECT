/**
 * Extract a human-readable error message from an API error response.
 * Handles Pydantic validation errors (array of {loc, msg, type}),
 * plain string details, and fallback messages.
 */
export function extractErrorMessage(err, fallback = 'An error occurred') {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : '';
        return field ? `${field}: ${e.msg}` : e.msg;
      })
      .join('; ');
  }
  return String(detail);
}

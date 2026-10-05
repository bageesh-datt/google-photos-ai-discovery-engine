/**
 * Helper function to determine if an observation is relevant to photo retrieval.
 * Returns true if the observation represents a valid photo retrieval failure scenario.
 * Returns false if it is generic feedback, noise, or excluded non-retrieval feedback.
 */
export const isRelevantObservation = (obs) => {
  if (!obs) return false;
  if (obs.retrieval_outcome === 'Excluded from retrieval failure analysis.') return false;
  if (obs.problem_category === 'Other') return false;
  if (obs.evidence_strength === 'Low') return false;
  if (typeof obs.failure_point === 'string') {
    const fp = obs.failure_point.toLowerCase();
    if (fp.includes('lacks explicit evidence') || fp.includes('describes non-retrieval issue')) {
      return false;
    }
  }
  return true;
};

/**
 * Calculates raw feedback count, relevant retrieval count, and rejected count from an array of observations.
 */
export const getObservationCounts = (observations = []) => {
  const raw = observations.length;
  const relevant = observations.filter(isRelevantObservation).length;
  const rejected = raw - relevant;
  return { raw, relevant, rejected };
};

/**
 * Returns the label for the failure field ('Failure Point' or 'Relevance Reason').
 */
export const getFailurePointLabel = (obs) => {
  return isRelevantObservation(obs) ? 'Failure Point' : 'Relevance Reason';
};

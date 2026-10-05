import React, { useState } from 'react';
import { Layers, HelpCircle, ChevronDown, ChevronUp, Link as LinkIcon } from 'lucide-react';

export default function ClusterCard({ clusters, onSelectObservation }) {
  const [expandedInterviewQuestions, setExpandedInterviewQuestions] = useState({});

  const toggleQuestions = (clusterId) => {
    setExpandedInterviewQuestions(prev => ({
      ...prev,
      [clusterId]: !prev[clusterId]
    }));
  };

  return (
    <div className="cards-grid">
      {clusters.map((cluster) => {
        const showQuestions = expandedInterviewQuestions[cluster.cluster_id];
        return (
          <div key={cluster.cluster_id} className="info-card">
            <div>
              <div className="info-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="badge badge-purple">{cluster.cluster_id}</span>
                  <h3 style={{ fontSize: '1.1rem' }}>{cluster.cluster_name}</h3>
                </div>
                <span className="badge badge-blue">
                  {cluster.count} Evidence {cluster.count === 1 ? 'Record' : 'Records'}
                </span>
              </div>

              <div style={{
                background: 'var(--primary-light)',
                border: '1px solid var(--primary-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.85rem',
                fontSize: '0.875rem',
                marginBottom: '1rem'
              }}>
                <strong style={{ color: 'var(--primary)' }}>Core Retrieval Problem:</strong>
                <div style={{ marginTop: '0.25rem', color: 'var(--text-primary)' }}>
                  {cluster.core_problem}
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                <div>
                  <strong>What Users Remember:</strong> {cluster.what_users_remember}
                </div>
                <div>
                  <strong>Missing Information:</strong> {cluster.what_is_missing}
                </div>
                <div>
                  <strong>Typical Search Behavior:</strong> {cluster.typical_search_behavior}
                </div>
                <div>
                  <strong>Failure Point:</strong> <span style={{ color: '#dc2626' }}>{cluster.failure_point}</span>
                </div>
                <div>
                  <strong>Workarounds:</strong> {cluster.workarounds}
                </div>
              </div>

              {/* Supporting Observation Badges */}
              <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  SUPPORTING EVIDENCE OBSERVATION IDs:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {cluster.supporting_observation_ids.map((obsId) => (
                    <button
                      key={obsId}
                      className="badge-id"
                      onClick={() => onSelectObservation && onSelectObservation(obsId)}
                      title="Click to highlight observation"
                    >
                      {obsId}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Interview Validation Accordion */}
            <div style={{ marginTop: '1.25rem', paddingTop: '0.75rem', borderTop: '1px dashed var(--border-color)' }}>
              <button
                className="btn btn-outline"
                style={{ width: '100%', justifyContent: 'space-between', fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
                onClick={() => toggleQuestions(cluster.cluster_id)}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--purple)' }}>
                  <HelpCircle size={14} /> Open Questions for User Interviews ({cluster.open_questions_for_interviews?.length || 0})
                </span>
                {showQuestions ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {showQuestions && (
                <ul style={{
                  marginTop: '0.75rem',
                  paddingLeft: '1.25rem',
                  fontSize: '0.8rem',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem'
                }}>
                  {cluster.open_questions_for_interviews?.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

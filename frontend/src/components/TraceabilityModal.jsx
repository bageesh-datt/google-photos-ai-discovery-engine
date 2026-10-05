import React from 'react';
import { X, ExternalLink, GitBranch, ShieldCheck } from 'lucide-react';
import { isRelevantObservation, getFailurePointLabel } from '../utils/relevance';

export default function TraceabilityModal({ opportunityId, traceabilityData, onClose }) {
  if (!opportunityId || !traceabilityData) return null;

  const oppTrace = traceabilityData[opportunityId];
  if (!oppTrace) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="badge badge-purple">{opportunityId}</span>
              <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                <ShieldCheck size={12} /> Verified Evidence Chain
              </span>
            </div>
            <h2 style={{ fontSize: '1.25rem' }}>{oppTrace.opportunity_name}</h2>
          </div>
          <button
            className="btn btn-outline"
            style={{ padding: '0.35rem', borderRadius: '50%' }}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Traceability chain mapping from opportunity area down to underlying problem clusters, observation IDs, verbatim quotes, and verifiable source URLs.
        </div>

        {/* Visual Traceability Tree */}
        <div className="trace-tree">
          {/* Step 1: Opportunity Level */}
          <div className="trace-step">
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--purple)', textTransform: 'uppercase' }}>
              Level 1: Research Opportunity Area
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', marginTop: '0.15rem' }}>
              {opportunityId} — {oppTrace.opportunity_name}
            </div>
          </div>

          {/* Step 2: Linked Clusters */}
          <div className="trace-step">
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--primary)', textTransform: 'uppercase' }}>
              Level 2: Supporting Problem Clusters ({oppTrace.supporting_clusters?.length || 0})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.35rem' }}>
              {oppTrace.supporting_clusters?.map((cl) => (
                <div key={cl.cluster_id} style={{ background: 'var(--primary-light)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--primary-border)', fontSize: '0.85rem' }}>
                  <strong>{cl.cluster_id}:</strong> {cl.cluster_name} (Matched Observations: {cl.matched_observation_ids?.join(', ')})
                </div>
              ))}
            </div>
          </div>

          {/* Step 3: Individual Observation Evidence */}
          <div className="trace-step">
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)', textTransform: 'uppercase' }}>
              Level 3: Verbatim User Evidence & Source URLs ({oppTrace.supporting_observations?.length || 0})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
              {oppTrace.supporting_observations?.map((obs) => {
                const isRel = isRelevantObservation(obs);
                const label = getFailurePointLabel(obs);
                return (
                  <div key={obs.id} style={{ background: 'white', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="badge badge-blue">{obs.id}</span>
                        <span className="badge badge-purple">{obs.source}</span>
                        <span className="badge badge-green">{obs.problem_category}</span>
                      </div>
                      <a
                        href={obs.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-outline"
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', color: 'var(--primary)' }}
                      >
                        Source URL <ExternalLink size={12} />
                      </a>
                    </div>
                    <div style={{ fontStyle: 'italic', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                      Scenario: "{obs.retrieval_scenario}"
                    </div>
                    <div style={{ fontSize: '0.8rem', color: isRel ? '#dc2626' : 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      <strong>{label}:</strong> {obs.failure_point}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close Traceability Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

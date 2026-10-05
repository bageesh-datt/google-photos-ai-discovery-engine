import React from 'react';
import { Compass, ShieldCheck, ArrowUpRight, GitBranch } from 'lucide-react';

export default function OpportunityCard({ opportunities, onOpenTraceability }) {
  return (
    <div className="cards-grid">
      {opportunities.map((opp) => (
        <div key={opp.opportunity_id} className="info-card" style={{ borderLeft: '4px solid var(--purple)' }}>
          <div>
            <div className="info-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-purple">{opp.opportunity_id}</span>
                <span className="badge badge-blue">{opp.retrieval_stage}</span>
              </div>
            </div>

            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)', marginBottom: '0.75rem', lineHeight: 1.3 }}>
              {opp.opportunity_name}
            </h3>

            <div style={{
              background: 'var(--purple-light)',
              border: '1px solid var(--purple-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.85rem',
              fontSize: '0.875rem',
              marginBottom: '1rem'
            }}>
              <strong style={{ color: 'var(--purple)' }}>User Problem Space:</strong>
              <div style={{ marginTop: '0.25rem', color: 'var(--text-primary)' }}>
                {opp.user_problem}
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
              <strong style={{ color: 'var(--text-secondary)' }}>Why Workaround Fails:</strong>
              <div style={{ color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {opp.why_current_workaround_is_insufficient}
              </div>
            </div>

            {/* Supporting Evidence Badges */}
            <div style={{ paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                SUPPORTING EVIDENCE OBSERVATION IDs:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '1rem' }}>
                {opp.supporting_evidence_ids.map((obsId) => (
                  <span key={obsId} className="badge-id">{obsId}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Action Button: Traceability Tree */}
          <button
            className="btn btn-outline"
            style={{ width: '100%', fontSize: '0.85rem', color: 'var(--primary)', borderColor: 'var(--primary-border)' }}
            onClick={() => onOpenTraceability && onOpenTraceability(opp.opportunity_id)}
          >
            <GitBranch size={16} /> View Evidence Traceability Chain
          </button>
        </div>
      ))}
    </div>
  );
}

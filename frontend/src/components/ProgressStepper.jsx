import React from 'react';
import { Loader2, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

const STAGES = [
  { id: 1, name: 'Stage 1: Dataset Validation & Loading', pct: 10 },
  { id: 2, name: 'Stage 2: AI Relevance Filtering', pct: 30 },
  { id: 3, name: 'Stage 3: LLM Structured 14-Field Extraction', pct: 60 },
  { id: 4, name: 'Stage 4: Semantic Problem Clustering', pct: 80 },
  { id: 5, name: 'Stage 5: Opportunity Area Synthesis', pct: 100 },
];

export default function ProgressStepper({ statusData }) {
  const currentPct = statusData?.progress_pct || 0;
  const isFailed = statusData?.status === 'failed';
  const isCompleted = statusData?.status === 'completed';

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-lg)',
      padding: '2rem',
      maxWidth: '800px',
      margin: '0 auto',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem' }}>AI Discovery Engine Processing</h2>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Analysis ID: <code>{statusData?.analysis_id || 'Initializing...'}</code>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
          {isCompleted ? (
            <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <CheckCircle2 size={18} /> Complete (100%)
            </span>
          ) : isFailed ? (
            <span style={{ color: '#dc2626', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <AlertTriangle size={18} /> Processing Error
            </span>
          ) : (
            <span style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Loader2 size={18} className="spin-icon" style={{ animation: 'spin 1s linear infinite' }} /> Processing ({currentPct}%)
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{
        height: '8px',
        background: 'var(--bg-subtle)',
        borderRadius: '9999px',
        overflow: 'hidden',
        marginBottom: '2rem'
      }}>
        <div style={{
          height: '100%',
          width: `${currentPct}%`,
          background: isFailed ? '#dc2626' : isCompleted ? 'var(--success)' : 'var(--primary)',
          transition: 'width 0.4s ease'
        }} />
      </div>

      {/* Stage Stepper List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {STAGES.map((stg) => {
          const isDone = currentPct >= stg.pct || isCompleted;
          const isCurrent = !isDone && currentPct >= (stg.pct - 20);

          return (
            <div
              key={stg.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.75rem 1rem',
                background: isCurrent ? 'var(--primary-light)' : 'transparent',
                borderRadius: 'var(--radius-sm)',
                border: isCurrent ? '1px solid var(--primary-border)' : '1px solid transparent'
              }}
            >
              <div>
                {isDone ? (
                  <CheckCircle2 size={20} style={{ color: 'var(--success)' }} />
                ) : isCurrent ? (
                  <Loader2 size={20} style={{ color: 'var(--primary)', animation: 'spin 1s linear infinite' }} />
                ) : (
                  <Clock size={20} style={{ color: 'var(--text-muted)' }} />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontWeight: isCurrent || isDone ? 600 : 400,
                  color: isCurrent ? 'var(--primary)' : isDone ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: '0.9rem'
                }}>
                  {stg.name}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {isFailed && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#dc2626',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.875rem'
        }}>
          <strong>Pipeline Failed:</strong> {statusData?.error_message || 'An error occurred during analysis.'}
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

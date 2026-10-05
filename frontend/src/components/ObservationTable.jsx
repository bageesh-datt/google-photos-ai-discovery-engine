import React, { useState } from 'react';
import { ExternalLink, Filter, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { isRelevantObservation, getFailurePointLabel } from '../utils/relevance';

export default function ObservationTable({ observations }) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedRelevance, setSelectedRelevance] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  const categories = ['ALL', ...new Set(observations.map(o => o.problem_category))];

  const filteredObservations = observations.filter(obs => {
    const isRel = isRelevantObservation(obs);
    const matchesRelevance =
      selectedRelevance === 'ALL' ||
      (selectedRelevance === 'RELEVANT' && isRel) ||
      (selectedRelevance === 'NOT_RELEVANT' && !isRel);

    const matchesCategory = selectedCategory === 'ALL' || obs.problem_category === selectedCategory;

    const matchesSearch =
      (obs.id && obs.id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (obs.retrieval_scenario && obs.retrieval_scenario.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (obs.what_user_remembers && obs.what_user_remembers.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (obs.failure_point && obs.failure_point.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (obs.source && obs.source.toLowerCase().includes(searchTerm.toLowerCase()));

    return matchesRelevance && matchesCategory && matchesSearch;
  });

  return (
    <div>
      {/* Controls Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />

          {/* Problem Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '0.875rem',
              background: 'var(--bg-surface)'
            }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'ALL' ? 'All Problem Categories' : cat}
              </option>
            ))}
          </select>

          {/* Relevance Filter */}
          <select
            value={selectedRelevance}
            onChange={(e) => setSelectedRelevance(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '0.875rem',
              background: 'var(--bg-surface)'
            }}
          >
            <option value="ALL">All Relevance</option>
            <option value="RELEVANT">Relevant</option>
            <option value="NOT_RELEVANT">Not relevant</option>
          </select>
        </div>

        <div style={{ position: 'relative', minWidth: '260px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Filter observations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem 0.5rem 2.25rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '0.875rem',
              background: 'var(--bg-surface)'
            }}
          />
        </div>
      </div>

      {/* Observations Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Relevance</th>
              <th>Scenario</th>
              <th>What User Remembers</th>
              <th>Failure Point / Relevance Reason</th>
              <th>Problem Category</th>
              <th>Evidence Link</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredObservations.map((obs) => {
              const isExpanded = expandedId === obs.id;
              const isRel = isRelevantObservation(obs);

              return (
                <React.Fragment key={obs.id}>
                  <tr style={{ opacity: isRel ? 1 : 0.85 }}>
                    <td>
                      <span className="badge badge-blue">{obs.id}</span>
                    </td>
                    <td>{obs.source}</td>
                    <td>
                      {isRel ? (
                        <span className="badge badge-green">Relevant</span>
                      ) : (
                        <span className="badge badge-gray">Not relevant</span>
                      )}
                    </td>
                    <td style={{ fontWeight: 500 }}>{obs.retrieval_scenario}</td>
                    <td>{obs.what_user_remembers}</td>
                    <td style={{ color: isRel ? '#dc2626' : 'var(--text-secondary)' }}>
                      {obs.failure_point}
                    </td>
                    <td>
                      <span className={obs.problem_category === 'Other' ? 'badge badge-gray' : 'badge badge-purple'}>
                        {obs.problem_category}
                      </span>
                    </td>
                    <td>
                      <a
                        href={obs.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          color: 'var(--primary)',
                          fontWeight: 500,
                          fontSize: '0.8rem'
                        }}
                      >
                        URL <ExternalLink size={12} />
                      </a>
                    </td>
                    <td>
                      <button
                        className="btn btn-outline"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => setExpandedId(isExpanded ? null : obs.id)}
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />} 14 Fields
                      </button>
                    </td>
                  </tr>

                  {/* Expanded 14-Field Detail Drawer */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={9} style={{ background: 'var(--bg-subtle)', padding: '1.25rem' }}>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                          gap: '1rem',
                          fontSize: '0.85rem'
                        }}>
                          <div style={{ background: 'white', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                            <strong style={{ color: 'var(--primary)' }}>Memory & Forgotten:</strong>
                            <div style={{ marginTop: '0.25rem' }}><strong>Remembers:</strong> {obs.what_user_remembers}</div>
                            <div style={{ marginTop: '0.25rem' }}><strong>Forgot:</strong> {obs.what_user_forgot}</div>
                          </div>

                          <div style={{ background: 'white', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                            <strong style={{ color: 'var(--primary)' }}>Search Attempt & Behavior:</strong>
                            <div style={{ marginTop: '0.25rem' }}><strong>Attempt:</strong> {obs.search_attempt}</div>
                            <div style={{ marginTop: '0.25rem' }}><strong>Behavior:</strong> {obs.search_behavior}</div>
                          </div>

                          <div style={{ background: 'white', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                            <strong style={{ color: 'var(--primary)' }}>Outcome & Workaround:</strong>
                            <div style={{ marginTop: '0.25rem' }}><strong>Outcome:</strong> {obs.retrieval_outcome}</div>
                            <div style={{ marginTop: '0.25rem' }}><strong>Workaround:</strong> {obs.workaround}</div>
                            <div style={{ marginTop: '0.25rem' }}>
                              <strong>{getFailurePointLabel(obs)}:</strong> {obs.failure_point}
                            </div>
                          </div>

                          <div style={{ background: 'white', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                            <strong style={{ color: 'var(--purple)' }}>Analyst Note & Evidence Strength:</strong>
                            <div style={{ marginTop: '0.25rem' }}>
                              <strong>Relevance Status:</strong>{' '}
                              {isRel ? (
                                <span className="badge badge-green">Relevant</span>
                              ) : (
                                <span className="badge badge-gray">Not relevant</span>
                              )}
                            </div>
                            <div style={{ marginTop: '0.25rem' }}><strong>Strength:</strong> <span className={obs.evidence_strength === 'Low' ? 'badge badge-gray' : 'badge badge-green'}>{obs.evidence_strength}</span></div>
                            <div style={{ marginTop: '0.25rem', color: 'var(--text-secondary)' }}>{obs.analyst_note}</div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

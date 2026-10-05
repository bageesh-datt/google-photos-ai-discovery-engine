import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, Play, FileText, AlertCircle, ArrowRight } from 'lucide-react';
import { fetchPresetDataset, uploadDataset } from '../services/api';

export default function FileUpload({ onDatasetLoaded, onStartAnalysis }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dataset, setDataset] = useState(null);

  const handleLoadPreset = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPresetDataset();
      setDataset(data);
      if (onDatasetLoaded) onDatasetLoaded(data);
    } catch (err) {
      setError(err.message || 'Failed to load preset pilot dataset.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setError('Please select a valid CSV file (.csv).');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await uploadDataset(file);
      setDataset(data);
      if (onDatasetLoaded) onDatasetLoaded(data);
    } catch (err) {
      setError(err.message || 'Failed to upload CSV file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Reviewer Quick-Test Banner */}
      <div className="preset-banner">
        <div className="preset-banner-title">
          <CheckCircle2 size={20} /> 1-Click Reviewer Testing (Pre-Bundled Pilot Dataset)
        </div>
        <div className="preset-banner-text">
          Evaluate the end-to-end AI Discovery Engine immediately using 12 verified public user observations from Reddit and Google Support forums.
        </div>
        <button
          className="btn btn-preset"
          onClick={handleLoadPreset}
          disabled={loading}
        >
          {loading ? 'Loading Pilot Dataset...' : 'Load Preset Pilot Dataset (12 records)'} <ArrowRight size={16} />
        </button>
      </div>

      {/* Custom CSV Upload Section */}
      <div className="upload-card">
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Or Upload Custom Feedback CSV</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          CSV must contain headers: <code>id, source, url, user_statement, retrieval_scenario</code>
        </p>

        <label className="dropzone" style={{ display: 'block' }}>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={loading}
            style={{ display: 'none' }}
          />
          <UploadCloud size={36} style={{ color: 'var(--primary)', marginBottom: '0.75rem' }} />
          <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
            Click to browse or drag and drop CSV file
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Supports standard UTF-8 encoded .csv files
          </div>
        </label>

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#dc2626',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.875rem'
          }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {/* Dataset Preview */}
        {dataset && (
          <div style={{ marginTop: '2rem', textAlign: 'left' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.75rem 1rem',
              background: 'var(--primary-light)',
              border: '1px solid var(--primary-border)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--primary)' }}>
                  Dataset Ready: <code>{dataset.dataset_id}</code>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Total Rows: {dataset.total_rows} | Valid: {dataset.valid_rows_count} | Invalid: {dataset.invalid_rows_count}
                </div>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => onStartAnalysis(dataset.dataset_id)}
              >
                <Play size={16} /> Start AI Analysis
              </button>
            </div>

            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
              Data Preview (First 5 Rows):
            </h4>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Source</th>
                    <th>Scenario</th>
                    <th>User Statement</th>
                  </tr>
                </thead>
                <tbody>
                  {dataset.records.slice(0, 5).map((row) => (
                    <tr key={row.id}>
                      <td><span className="badge badge-blue">{row.id}</span></td>
                      <td>{row.source}</td>
                      <td>{row.retrieval_scenario}</td>
                      <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {row.user_statement}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

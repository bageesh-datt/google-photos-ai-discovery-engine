import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import ProgressStepper from './components/ProgressStepper';
import ObservationTable from './components/ObservationTable';
import ClusterCard from './components/ClusterCard';
import OpportunityCard from './components/OpportunityCard';
import TraceabilityModal from './components/TraceabilityModal';
import {
  startAnalysis,
  fetchAnalysisStatus,
  fetchObservations,
  fetchClusters,
  fetchOpportunities,
  fetchExportReport,
} from './services/api';
import { Download, RefreshCw, FileText, Layers, Compass, ListFilter } from 'lucide-react';

import { getObservationCounts } from './utils/relevance';

export default function App() {
  const [viewState, setViewState] = useState('UPLOAD'); // UPLOAD | PROCESSING | RESULTS
  const [activeTab, setActiveTab] = useState('observations'); // observations | clusters | opportunities
  
  const [datasetId, setDatasetId] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  
  const [observations, setObservations] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [exportReport, setExportReport] = useState(null);
  
  const [selectedTraceabilityOppId, setSelectedTraceabilityOppId] = useState(null);
  const [error, setError] = useState(null);

  // Poll status when in PROCESSING view
  useEffect(() => {
    let interval = null;
    if (viewState === 'PROCESSING' && analysisId) {
      interval = setInterval(async () => {
        try {
          const status = await fetchAnalysisStatus(analysisId);
          setStatusData(status);

          if (status.status === 'completed') {
            clearInterval(interval);
            await loadAnalysisResults(analysisId);
            setViewState('RESULTS');
          } else if (status.status === 'failed') {
            clearInterval(interval);
            setError(status.error_message || 'Analysis pipeline execution failed.');
          }
        } catch (err) {
          console.error('Polling error:', err);
          clearInterval(interval);
          setError(err.message || 'Analysis session expired or not found. Please select a dataset to try again.');
          setViewState('UPLOAD');
          setAnalysisId(null);
        }
      }, 600);

    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [viewState, analysisId]);

  const handleStartAnalysis = async (dId) => {
    setDatasetId(dId);
    setError(null);
    try {
      const res = await startAnalysis(dId);
      setAnalysisId(res.analysis_id);
      setViewState('PROCESSING');
    } catch (err) {
      setError(err.message || 'Failed to trigger AI analysis.');
    }
  };

  const loadAnalysisResults = async (aId) => {
    try {
      const [obsData, clData, oppData, expData] = await Promise.all([
        fetchObservations(aId),
        fetchClusters(aId),
        fetchOpportunities(aId),
        fetchExportReport(aId),
      ]);
      setObservations(obsData);
      setClusters(clData);
      setOpportunities(oppData);
      setExportReport(expData);
    } catch (err) {
      setError('Failed to load complete analysis results.');
    }
  };

  const handleReset = () => {
    setViewState('UPLOAD');
    setDatasetId(null);
    setAnalysisId(null);
    setStatusData(null);
    setObservations([]);
    setClusters([]);
    setOpportunities([]);
    setExportReport(null);
    setError(null);
  };

  const handleExportJSON = () => {
    if (!exportReport) return;
    const jsonStr = JSON.stringify(exportReport, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `google_photos_discovery_${analysisId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const { raw: rawCount, relevant: relevantCount, rejected: rejectedCount } = getObservationCounts(observations);

  return (
    <div className="app-container">
      <Navbar activeStep={viewState} onReset={handleReset} />

      <main className="main-content">
        {error && (
          <div style={{
            padding: '0.85rem 1.25rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#dc2626',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div><strong>Error:</strong> {error}</div>
            <button className="btn btn-outline" style={{ fontSize: '0.75rem' }} onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}

        {/* VIEW 1: UPLOAD & PRESET SELECTION */}
        {viewState === 'UPLOAD' && (
          <FileUpload
            onDatasetLoaded={(d) => setDatasetId(d.dataset_id)}
            onStartAnalysis={handleStartAnalysis}
          />
        )}

        {/* VIEW 2: PIPELINE PROCESSING PROGRESS */}
        {viewState === 'PROCESSING' && (
          <ProgressStepper statusData={statusData} />
        )}

        {/* VIEW 3: TABBED RESEARCH RESULTS DASHBOARD */}
        {viewState === 'RESULTS' && (
          <div>
            {/* Header Toolbar */}
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1.5rem'
            }}>
              <div>
                <h1 style={{ fontSize: '1.5rem' }}>Discovery Engine Findings</h1>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Analysis ID: <code>{analysisId}</code> | Dataset: <code>{datasetId}</code>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-outline" onClick={handleReset}>
                  <RefreshCw size={14} /> New Dataset
                </button>
                <button className="btn btn-primary" onClick={handleExportJSON}>
                  <Download size={14} /> Export Report (JSON)
                </button>
              </div>
            </div>

            {/* Metrics Banner */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Raw Feedback</div>
                <div className="stat-value">{rawCount}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Relevant Retrieval</div>
                <div className="stat-value">{relevantCount}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Rejected / Non-retrieval</div>
                <div className="stat-value">{rejectedCount}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Problem Clusters</div>
                <div className="stat-value">{clusters.length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Opportunity Areas</div>
                <div className="stat-value">{opportunities.length}</div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="tabs-container">
              <button
                className={`tab-button ${activeTab === 'observations' ? 'active' : ''}`}
                onClick={() => setActiveTab('observations')}
              >
                <FileText size={16} /> All Observations ({observations.length})
              </button>

              <button
                className={`tab-button ${activeTab === 'clusters' ? 'active' : ''}`}
                onClick={() => setActiveTab('clusters')}
              >
                <Layers size={16} /> Problem Clusters ({clusters.length})
              </button>

              <button
                className={`tab-button ${activeTab === 'opportunities' ? 'active' : ''}`}
                onClick={() => setActiveTab('opportunities')}
              >
                <Compass size={16} /> Opportunity Areas ({opportunities.length})
              </button>
            </div>

            {/* TAB CONTENT 1: OBSERVATIONS */}
            {activeTab === 'observations' && (
              <ObservationTable observations={observations} />
            )}

            {/* TAB CONTENT 2: CLUSTERS */}
            {activeTab === 'clusters' && (
              <ClusterCard
                clusters={clusters}
                onSelectObservation={() => setActiveTab('observations')}
              />
            )}

            {/* TAB CONTENT 3: OPPORTUNITIES */}
            {activeTab === 'opportunities' && (
              <OpportunityCard
                opportunities={opportunities}
                onOpenTraceability={(oppId) => setSelectedTraceabilityOppId(oppId)}
              />
            )}
          </div>
        )}

        {/* TRACEABILITY MODAL */}
        {selectedTraceabilityOppId && exportReport && (
          <TraceabilityModal
            opportunityId={selectedTraceabilityOppId}
            traceabilityData={exportReport.traceability_map}
            onClose={() => setSelectedTraceabilityOppId(null)}
          />
        )}
      </main>
    </div>
  );
}

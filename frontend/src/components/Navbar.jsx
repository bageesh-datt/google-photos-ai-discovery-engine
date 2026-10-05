import React from 'react';
import { Sparkles, Database, ExternalLink } from 'lucide-react';

export default function Navbar({ activeStep, onReset }) {
  return (
    <header className="navbar">
      <div className="navbar-content">
        <div className="brand-group" onClick={onReset} style={{ cursor: 'pointer' }}>
          <div className="brand-logo">
            <Sparkles size={20} />
          </div>
          <div>
            <div className="brand-title">Google Photos AI Discovery Engine</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Core Experience Team — Problem Discovery (Part 1)
            </div>
          </div>
          <span className="brand-badge">NextLeap PM Graduation Project</span>
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button className="btn btn-outline" onClick={onReset} style={{ fontSize: '0.8rem' }}>
            <Database size={14} /> Dataset Upload
          </button>
        </div>
      </div>
    </header>
  );
}

// src/components/CrossModalSearch.js
import React from 'react';

const CrossModalSearch = ({ crossModalResults, loading }) => {
  if (!crossModalResults) {
    return null;
  }

  const { target_bird_id, cross_modal_results } = crossModalResults;

  const renderModalityResults = (modalityName, results) => {
    if (!results || results.length === 0) {
      return (
        <div className="modality-section empty">
          <h4>{modalityName.charAt(0).toUpperCase() + modalityName.slice(1)} Search</h4>
          <p>No similar birds found in {modalityName} data</p>
        </div>
      );
    }

    return (
      <div className="modality-section">
        <h4>{modalityName.charAt(0).toUpperCase() + modalityName.slice(1)} Search</h4>
        <div className="cross-modal-results">
          {results.slice(0, 3).map((bird, index) => (
            <div key={bird.bird_id || index} className="cross-modal-card">
              <div className="cross-modal-rank">#{index + 1}</div>
              
              {/* Modality-specific preview */}
              <div className="cross-modal-preview">
                {modalityName === 'image' && bird.source_url && (
                  <img 
                    src={bird.source_url} 
                    alt={bird.species_name}
                    className="cross-modal-image"
                    onError={(e) => e.target.style.display = 'none'}
                  />
                )}
                
                {modalityName === 'audio' && (
                  <div className="cross-modal-audio-icon">
                    <span>🎵</span>
                    {bird.clip_duration && (
                      <span className="duration">{bird.clip_duration}s</span>
                    )}
                  </div>
                )}
                
                {modalityName === 'text' && (
                  <div className="cross-modal-text-icon">
                    <span>📄</span>
                    {bird.data_completeness && (
                      <span className="data-size">{bird.data_completeness} chars</span>
                    )}
                  </div>
                )}
              </div>

              <div className="cross-modal-info">
                <h5 className="cross-modal-name">{bird.species_name}</h5>
                {bird.scientific_name && bird.scientific_name !== 'Unknown' && (
                  <p className="cross-modal-scientific">{bird.scientific_name}</p>
                )}
                <div className="cross-modal-score">
                  Similarity: {(bird.confidence_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="cross-modal-container">
      <div className="cross-modal-header">
        <h3>Cross-Modal Search Results</h3>
        <p>Similar birds across all search types for Bird ID: {target_bird_id}</p>
      </div>

      {loading && (
        <div className="cross-modal-loading">
          <div className="loading-spinner"></div>
          <p>Searching across all modalities...</p>
        </div>
      )}

      <div className="cross-modal-sections">
        {cross_modal_results.text && renderModalityResults('text', cross_modal_results.text)}
        {cross_modal_results.image && renderModalityResults('image', cross_modal_results.image)}
        {cross_modal_results.audio && renderModalityResults('audio', cross_modal_results.audio)}
      </div>

      {/* Summary Statistics */}
      <div className="cross-modal-summary">
        <h4>Search Summary</h4>
        <div className="summary-stats">
          <div className="stat-item">
            <span className="stat-label">Text Results:</span>
            <span className="stat-value">
              {cross_modal_results.text ? cross_modal_results.text.length : 0}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Image Results:</span>
            <span className="stat-value">
              {cross_modal_results.image ? cross_modal_results.image.length : 0}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Audio Results:</span>
            <span className="stat-value">
              {cross_modal_results.audio ? cross_modal_results.audio.length : 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CrossModalSearch;
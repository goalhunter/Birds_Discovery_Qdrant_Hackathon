// src/components/ResultsDisplay.js
import React, { useState } from 'react';

const ResultsDisplay = ({ results, searchType, onCrossModalSearch, loading }) => {
  const [selectedBird, setSelectedBird] = useState(null);

  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <div className="no-results-icon">🔍</div>
        <p>No birds found. Try a different search term or upload a different file.</p>
      </div>
    );
  }

  const handleBirdSelect = (bird) => {
    setSelectedBird(bird);
    if (onCrossModalSearch) {
      onCrossModalSearch(bird.bird_id);
    }
  };

  const formatConfidenceScore = (score) => {
    return (score * 100).toFixed(1);
  };

  const renderResultCard = (bird, index) => {
    const isSelected = selectedBird?.bird_id === bird.bird_id;
    
    return (
      <div
        key={bird.bird_id || index}
        className={`result-card ${isSelected ? 'selected' : ''}`}
        onClick={() => handleBirdSelect(bird)}
      >
        {/* Confidence Score Badge */}
        <div className="confidence-badge">
          {formatConfidenceScore(bird.confidence_score)}%
        </div>

        {/* Bird Image/Audio Preview */}
        <div className="result-media">
          {searchType === 'image' && bird.source_url && (
            <img
              src={bird.source_url}
              alt={bird.species_name}
              className="result-image"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          )}
          
          {searchType === 'audio' && bird.clip_path && (
            <div className="result-audio">
              <div className="audio-icon">🎵</div>
              <span className="audio-duration">
                {bird.clip_duration ? `${bird.clip_duration}s` : 'Audio'}
              </span>
            </div>
          )}
          
          {searchType === 'text' && (
            <div className="result-text">
              <div className="text-icon">📄</div>
              <div className="text-snippet">
                {bird.searchable_text && bird.searchable_text.length > 100
                  ? bird.searchable_text.substring(0, 100) + '...'
                  : bird.searchable_text || 'Text data available'}
              </div>
            </div>
          )}
        </div>

        {/* Bird Information */}
        <div className="result-info">
          <h3 className="bird-name">{bird.species_name}</h3>
          
          {bird.scientific_name && bird.scientific_name !== 'Unknown' && (
            <p className="scientific-name">{bird.scientific_name}</p>
          )}
          
          {bird.family && bird.family !== 'Unknown' && (
            <p className="bird-family">Family: {bird.family}</p>
          )}

          {/* Additional metadata based on search type */}
          <div className="additional-info">
            {searchType === 'image' && (
              <>
                {bird.width && bird.height && (
                  <span className="info-tag">
                    {bird.width} × {bird.height}
                  </span>
                )}
                {bird.quality_score && (
                  <span className="info-tag">
                    Quality: {bird.quality_score}/10
                  </span>
                )}
              </>
            )}
            
            {searchType === 'audio' && (
              <>
                {bird.feature_type && (
                  <span className="info-tag">
                    {bird.feature_type}
                  </span>
                )}
                {bird.audio_quality && (
                  <span className="info-tag">
                    Quality: {bird.audio_quality}
                  </span>
                )}
              </>
            )}
            
            {searchType === 'text' && (
              <>
                {bird.data_completeness && (
                  <span className="info-tag">
                    Data: {bird.data_completeness} chars
                  </span>
                )}
              </>
            )}
          </div>

          {/* Cross-modal search button */}
          <button
            className="cross-modal-button"
            onClick={(e) => {
              e.stopPropagation();
              handleBirdSelect(bird);
            }}
            disabled={loading}
          >
            View Similar Across All Types
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Search Results</h2>
        <span className="results-count">
          Found {results.length} bird{results.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="results-grid">
        {results.map((bird, index) => renderResultCard(bird, index))}
      </div>

      {/* Load More Button (if needed) */}
      {results.length >= 10 && (
        <div className="load-more-container">
          <button className="load-more-button" disabled={loading}>
            Load More Results
          </button>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
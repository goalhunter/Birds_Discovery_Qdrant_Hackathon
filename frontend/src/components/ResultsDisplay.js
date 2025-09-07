// src/components/ResultsDisplay.js
import React, { useState } from 'react';

const ResultsDisplay = ({ results, searchType, onCrossModalSearch, loading }) => {
  const [selectedBird, setSelectedBird] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());

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

  const toggleCardExpansion = (birdId) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(birdId)) {
      newExpanded.delete(birdId);
    } else {
      newExpanded.add(birdId);
    }
    setExpandedCards(newExpanded);
  };

  const formatConfidenceScore = (score) => {
    return (score * 100).toFixed(1);
  };

  const getBestImage = (bird) => {
    if (bird.primary_image) return bird.primary_image;
    if (bird.images && bird.images.length > 0) {
      return bird.images.sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0))[0];
    }
    return null;
  };

  const getBestAudio = (bird) => {
    if (bird.primary_audio) return bird.primary_audio;
    if (bird.audio_clips && bird.audio_clips.length > 0) {
      return bird.audio_clips[0];
    }
    return null;
  };

  const getImageSrc = (image) => {
    if (!image) return null;
    return image.image_url || image.source_url || image.image_path;
  };

  const getAudioSrc = (audio) => {
    if (!audio) return null;
    return audio.audio_url || audio.clip_path;
  };

  const getMatchTypeIcon = (searchMatchType) => {
    switch (searchMatchType) {
      case 'text': return '📄';
      case 'image': return '🖼️';
      case 'audio': return '🎵';
      default: return '🔍';
    }
  };

  const renderResultCard = (bird, index) => {
    const isSelected = selectedBird?.bird_id === bird.bird_id;
    const isExpanded = expandedCards.has(bird.bird_id);
    const bestImage = getBestImage(bird);
    const bestAudio = getBestAudio(bird);
    
    return (
      <div
        key={bird.bird_id || index}
        className={`result-card comprehensive ${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
      >
        {/* Header with confidence and match type */}
        <div className="card-header">
          <div className="match-info">
            <span className="match-type-icon" title={`Matched via ${bird.search_match_type}`}>
              {getMatchTypeIcon(bird.search_match_type)}
            </span>
            <span className="confidence-badge">
              {formatConfidenceScore(bird.confidence_score)}%
            </span>
          </div>
          
          <button
            className="expand-button"
            onClick={(e) => {
              e.stopPropagation();
              toggleCardExpansion(bird.bird_id);
            }}
            title={isExpanded ? 'Collapse' : 'Expand details'}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>

        {/* Main content area */}
        <div className="card-content" onClick={() => handleBirdSelect(bird)}>
          
          {/* Bird Image */}
          <div className="result-media">
            {bestImage ? (
              <div className="image-container">
                <img
                  src={getImageSrc(bestImage)}
                  alt={bird.species_name}
                  className="result-image"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div className="image-placeholder" style={{ display: 'none' }}>
                  <span>🐦</span>
                  <small>Image unavailable</small>
                </div>
                {bird.images && bird.images.length > 1 && (
                  <div className="image-count-badge">
                    +{bird.images.length - 1} more
                  </div>
                )}
              </div>
            ) : (
              <div className="image-placeholder">
                <span>🐦</span>
                <small>No image available</small>
              </div>
            )}
          </div>

          {/* Bird Information */}
          <div className="result-info">
            <div className="bird-header">
              <h3 className="bird-name">{bird.species_name}</h3>
              {bird.scientific_name && bird.scientific_name !== 'Unknown' && (
                <p className="scientific-name">({bird.scientific_name})</p>
              )}
            </div>
            
            {bird.family && bird.family !== 'Unknown' && (
              <p className="bird-family">Family: {bird.family}</p>
            )}

            {/* Quick info tags */}
            <div className="quick-info">
              {bird.size && (
                <span className="info-tag size">Size: {bird.size}</span>
              )}
              {bird.ecology && (
                <span className="info-tag ecology">{bird.ecology}</span>
              )}
              {bird.group_dynamics && (
                <span className="info-tag group">{bird.group_dynamics}</span>
              )}
            </div>

            {/* Habitat and geography (always visible) */}
            {(bird.habitats || bird.geographic_regions) && (
              <div className="habitat-info">
                {bird.habitats && (
                  <p><strong>Habitat:</strong> {bird.habitats}</p>
                )}
                {bird.geographic_regions && (
                  <p><strong>Region:</strong> {bird.geographic_regions}</p>
                )}
              </div>
            )}

            {/* Audio player if available */}
            {bestAudio && (
              <div className="audio-section">
                <div className="audio-header">
                  <span className="audio-icon">🎵</span>
                  <span>Bird Call</span>
                  {bird.audio_clips && bird.audio_clips.length > 1 && (
                    <span className="audio-count">+{bird.audio_clips.length - 1} more</span>
                  )}
                </div>
                {getAudioSrc(bestAudio) && (
                  <audio controls className="audio-player">
                    <source src={getAudioSrc(bestAudio)} type="audio/wav" />
                    Your browser does not support audio playback.
                  </audio>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Expanded details */}
        {isExpanded && (
          <div className="expanded-details">
            
            {/* Full description */}
            {bird.extract && (
              <div className="description-section">
                <h4>Description</h4>
                <p className="full-description">{bird.extract}</p>
                {bird.url && (
                  <a href={bird.url} target="_blank" rel="noopener noreferrer" className="source-link">
                    Learn more →
                  </a>
                )}
              </div>
            )}

            {/* All images gallery */}
            {bird.images && bird.images.length > 1 && (
              <div className="images-gallery">
                <h4>All Images ({bird.images.length})</h4>
                <div className="image-grid">
                  {bird.images.slice(0, 6).map((img, idx) => (
                    <div key={idx} className="gallery-image">
                      <img
                        src={getImageSrc(img)}
                        alt={`${bird.species_name} ${idx + 1}`}
                        onError={(e) => e.target.style.display = 'none'}
                      />
                      {img.quality_score && (
                        <div className="quality-badge">Q: {img.quality_score}</div>
                      )}
                    </div>
                  ))}
                  {bird.images.length > 6 && (
                    <div className="more-images">+{bird.images.length - 6} more</div>
                  )}
                </div>
              </div>
            )}

            {/* All audio clips */}
            {bird.audio_clips && bird.audio_clips.length > 1 && (
              <div className="audio-gallery">
                <h4>All Audio Clips ({bird.audio_clips.length})</h4>
                <div className="audio-list">
                  {bird.audio_clips.slice(0, 3).map((audio, idx) => (
                    <div key={idx} className="audio-item">
                      <span>Clip {idx + 1}</span>
                      {audio.clip_duration && <span>({audio.clip_duration}s)</span>}
                      {getAudioSrc(audio) && (
                        <audio controls>
                          <source src={getAudioSrc(audio)} type="audio/wav" />
                        </audio>
                      )}
                    </div>
                  ))}
                  {bird.audio_clips.length > 3 && (
                    <div className="more-audio">+{bird.audio_clips.length - 3} more clips</div>
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="metadata-section">
              <h4>Search Details</h4>
              <div className="metadata-grid">
                <div className="metadata-item">
                  <strong>Bird ID:</strong> {bird.bird_id}
                </div>
                <div className="metadata-item">
                  <strong>Match Type:</strong> {bird.search_match_type}
                </div>
                <div className="metadata-item">
                  <strong>Confidence:</strong> {formatConfidenceScore(bird.confidence_score)}%
                </div>
                {bird.images && (
                  <div className="metadata-item">
                    <strong>Images:</strong> {bird.images.length}
                  </div>
                )}
                {bird.audio_clips && (
                  <div className="metadata-item">
                    <strong>Audio Clips:</strong> {bird.audio_clips.length}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="card-actions">
          <button
            className="cross-modal-button"
            onClick={(e) => {
              e.stopPropagation();
              handleBirdSelect(bird);
            }}
            disabled={loading}
          >
            🔍 Find Similar Birds
          </button>
          
          <button
            className="details-button"
            onClick={(e) => {
              e.stopPropagation();
              toggleCardExpansion(bird.bird_id);
            }}
          >
            {isExpanded ? 'Less Details' : 'More Details'}
          </button>
        </div>
      </div>
    );
  };

  const getSearchTypeSummary = () => {
    const withImages = results.filter(r => r.images && r.images.length > 0).length;
    const withAudio = results.filter(r => r.audio_clips && r.audio_clips.length > 0).length;
    const withComplete = results.filter(r => 
      r.images?.length > 0 && 
      r.audio_clips?.length > 0 && 
      r.text_description?.length > 0
    ).length;

    return { withImages, withAudio, withComplete };
  };

  const summary = getSearchTypeSummary();

  return (
    <div className="results-container comprehensive">
      <div className="results-header">
        <div className="header-main">
          <h2>Search Results</h2>
          <span className="search-type-badge">
            {getMatchTypeIcon(searchType)} {searchType.toUpperCase()} Search
          </span>
        </div>
        
        <div className="results-summary">
          <span className="results-count">
            Found {results.length} bird{results.length !== 1 ? 's' : ''}
          </span>
          <div className="content-summary">
            <span className="summary-item">📸 {summary.withImages} with images</span>
            <span className="summary-item">🎵 {summary.withAudio} with audio</span>
            <span className="summary-item">✨ {summary.withComplete} complete profiles</span>
          </div>
        </div>
      </div>

      <div className="results-grid comprehensive">
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
// src/components/BirdDetailPanel.js
import React, { useState, useEffect } from 'react';
import ApiService from '../services/api';

const BirdDetailPanel = ({ bird, isOpen, onClose }) => {
  const [enhancedDescription, setEnhancedDescription] = useState('');
  const [isEnhancing, setIsEnhancing] = useState(false);

  const handleEnhanceDescription = async () => {
    if (!bird) return;
    
    setIsEnhancing(true);
    setEnhancedDescription('');
    
    try {
      const response = await ApiService.enhanceDescription(bird);
      setEnhancedDescription(response.enhanced_description);
    } catch (error) {
      console.error('Failed to enhance description:', error);
      setEnhancedDescription('Unable to generate enhanced description at this time.');
    } finally {
      setIsEnhancing(false);
    }
  };

  // Auto-call enhance API when bird changes
  useEffect(() => {
    if (bird && isOpen) {
      handleEnhanceDescription();
    }
  }, [bird?.bird_id, isOpen]);

  const getImageSrc = (image) => {
    if (!image) return null;
    return image.image_url || image.source_url || image.image_path;
  };

  const getAudioSrc = (audio) => {
    if (!audio) return null;
    return audio.audio_url || audio.clip_path;
  };

  if (!bird) return null;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div className="detail-panel-backdrop" onClick={onClose} />
      )}
      
      {/* Detail Panel */}
      <div className={`bird-detail-panel ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="detail-panel-header">
          <div className="detail-header-content">
            <h2>{bird.species_name}</h2>
            {bird.scientific_name && bird.scientific_name !== 'Unknown' && (
              <p className="detail-scientific-name">({bird.scientific_name})</p>
            )}
          </div>
          <button className="detail-close-button" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Content */}
        <div className="detail-panel-content">
          
          {/* Quick Info */}
          <div className="detail-quick-info">
            {bird.family && bird.family !== 'Unknown' && (
              <span className="detail-info-tag family">Family: {bird.family}</span>
            )}
            {bird.size && (
              <span className="detail-info-tag size">Size: {bird.size}</span>
            )}
          </div>

          {/* Images Gallery */}
          {bird.images && bird.images.length > 0 && (
            <div className="detail-section">
              <h3>Images ({bird.images.length})</h3>
              <div className="detail-images-grid">
                {bird.images.map((img, idx) => (
                  <div key={idx} className="detail-image-container">
                    <img
                      src={getImageSrc(img)}
                      alt={`${bird.species_name} ${idx + 1}`}
                      className="detail-image"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="detail-image-placeholder" style={{ display: 'none' }}>
                      <span>🐦</span>
                      <small>Image unavailable</small>
                    </div>
                    {img.quality_score && (
                      <div className="detail-quality-badge">Q: {img.quality_score}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audio Section */}
          {bird.audio_clips && bird.audio_clips.length > 0 && (
            <div className="detail-section">
              <h3>Audio Clips ({bird.audio_clips.length})</h3>
              <div className="detail-audio-list">
                {bird.audio_clips.map((audio, idx) => (
                  <div key={idx} className="detail-audio-item">
                    <div className="detail-audio-header">
                      <span className="audio-clip-title">Clip {idx + 1}</span>
                      {audio.clip_duration && (
                        <span className="audio-duration">({audio.clip_duration}s)</span>
                      )}
                    </div>
                    {getAudioSrc(audio) && (
                      <audio controls className="detail-audio-player">
                        <source src={getAudioSrc(audio)} type="audio/wav" />
                        Your browser does not support audio playbook.
                      </audio>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        
        {/* Enhanced Description Section */}
          <div className="detail-section">
            <h3>Description</h3>
            <div className="description-content">
              {isEnhancing ? (
                <div className="enhancing-state">
                  <div className="loading-spinner"></div>
                  <p>Generating detailed description...</p>
                </div>
              ) : (
                <div className="enhanced-description">
                  {enhancedDescription ? (
                    <div className="enhanced-text">
                      {enhancedDescription.split('\n\n').map((paragraph, index) => (
                        <p key={index}>{paragraph}</p>
                      ))}
                    </div>
                  ) : (
                    <p className="fallback-description">
                      {bird.text_description || 'No description available.'}
                    </p>
                  )}
                </div>
              )}
            </div>
            
            {bird.url && (
              <a href={bird.url} target="_blank" rel="noopener noreferrer" className="detail-source-link">
                Learn more on Wikipedia →
              </a>
            )}
        </div>


          {/* Metadata */}
          <div className="detail-section">
            <h3>Search Details</h3>
            <div className="detail-metadata">
              <div className="metadata-row">
                <span>Bird ID:</span>
                <span>{bird.bird_id}</span>
              </div>
              <div className="metadata-row">
                <span>Match Type:</span>
                <span>{bird.search_match_type}</span>
              </div>
              <div className="metadata-row">
                <span>Confidence:</span>
                <span>{(bird.confidence_score * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default BirdDetailPanel;
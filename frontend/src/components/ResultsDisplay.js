// src/components/ResultsDisplay.js
import React, { useState, useEffect } from 'react';
import BirdDetailPanel from './BirdDetailPanel';
import BirdThumbnailGallery from './BirdThumbnailGallery';
import ApiService from '../services/api';

const ResultsDisplay = ({ results, searchType, onCrossModalSearch, loading, isInitialView = false }) => {
  const [selectedBird, setSelectedBird] = useState(null);
  const [detailPanelBird, setDetailPanelBird] = useState(null);
  const [randomBirds, setRandomBirds] = useState([]);
  const [randomBirdsLoading, setRandomBirdsLoading] = useState(false);
  const [hasSearchResults, setHasSearchResults] = useState(false);

  // Track when we have actual search results
  useEffect(() => {
    if (results && results.length > 0 && !isInitialView) {
      setHasSearchResults(true);
      console.log('Search results received:', results.length, 'birds');
    } else if (isInitialView) {
      setHasSearchResults(false);
      console.log('Back to initial view, clearing search results flag');
    }
  }, [results, isInitialView]);

  // Fetch random birds when on initial view with no results
  useEffect(() => {
    const fetchRandomBirds = async () => {
      console.log('useEffect triggered:', { isInitialView, hasResults: !!(results && results.length > 0), randomBirdsLength: randomBirds.length });
      
      if (isInitialView && !hasSearchResults && randomBirds.length === 0) {
        console.log('Fetching random birds...');
        try {
          setRandomBirdsLoading(true);
          const response = await ApiService.getAllBirds();
          
          let birdsData;
          if (Array.isArray(response)) {
            birdsData = response;
          } else if (response.birds && Array.isArray(response.birds)) {
            birdsData = response.birds;
          } else if (response.data && Array.isArray(response.data)) {
            birdsData = response.data;
          } else {
            birdsData = Object.values(response).find(val => Array.isArray(val)) || [];
          }
          
          // Create a truly random shuffle with current timestamp as seed
          const shuffledBirds = [...birdsData]
            .map(bird => ({ bird, sort: Math.random() + Date.now() }))
            .sort((a, b) => a.sort - b.sort)
            .map(({ bird }) => bird);
            
          console.log('Random birds selected:', shuffledBirds.slice(0, 5).map(b => b.species_name));
          setRandomBirds(shuffledBirds.slice(0, 12));
        } catch (error) {
          console.error('Failed to fetch random birds:', error);
        } finally {
          setRandomBirdsLoading(false);
        }
      }
    };

    fetchRandomBirds();
  }, [isInitialView, hasSearchResults]); // Only depend on these key flags

  // Determine which birds to display
  const birdsToDisplay = (() => {
    console.log('Determining birds to display:', { 
      isInitialView, 
      hasSearchResults, 
      resultsLength: results ? results.length : 0, 
      randomBirdsLength: randomBirds.length 
    });
    
    if (isInitialView && !hasSearchResults) {
      console.log('Using random birds:', randomBirds.length);
      return randomBirds;
    } else {
      console.log('Using search results:', results ? results.length : 0);
      return results || [];
    }
  })();

  const currentLoading = loading || randomBirdsLoading;

  if (currentLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading birds...</p>
      </div>
    );
  }

  if (!birdsToDisplay || birdsToDisplay.length === 0) {
    return (
      <div className="no-results">
        <div className="no-results-icon">🔍</div>
        <p>No birds found. Try a different search term or upload a different file.</p>
      </div>
    );
  }

  const handleBirdClick = (bird, e) => {
    e.stopPropagation();
    setDetailPanelBird(bird);
  };

  const handleCrossModalClick = (bird, e) => {
    e.stopPropagation();
    setSelectedBird(bird);
    if (onCrossModalSearch) {
      onCrossModalSearch(bird.bird_id);
    }
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

  const renderBirdCard = (bird, index) => {
    const isSelected = selectedBird?.bird_id === bird.bird_id;
    const bestImage = getBestImage(bird);
    const bestAudio = getBestAudio(bird);
    
    return (
      <div
        key={bird.bird_id || index}
        className={`modern-bird-card ${isSelected ? 'selected' : ''}`}
        onClick={(e) => handleBirdClick(bird, e)}
      >
        {/* Image Section */}
        <div className="bird-card-image">
          {bestImage ? (
            <img
              src={getImageSrc(bestImage)}
              alt={bird.species_name}
              className="card-image"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : (
            <div className="image-placeholder">
              <span className="placeholder-icon">🐦</span>
            </div>
          )}
          
          {/* Confidence Badge - only show for search results */}
          {bird.confidence_score && !isInitialView && (
            <div className="confidence-badge">
              {formatConfidenceScore(bird.confidence_score)}%
            </div>
          )}

          {/* Media Count Indicators */}
          <div className="media-indicators">
            {bird.images && bird.images.length > 1 && (
              <span className="media-count">📸 {bird.images.length}</span>
            )}
            {bird.audio_clips && bird.audio_clips.length > 0 && (
              <span className="media-count">🎵 {bird.audio_clips.length}</span>
            )}
          </div>
        </div>

        {/* Content Section */}
        <div className="bird-card-content">
          <div className="bird-header">
            <h3 className="bird-name">{bird.species_name}</h3>
            {bird.scientific_name && bird.scientific_name !== 'Unknown' && (
              <p className="scientific-name">{bird.scientific_name}</p>
            )}
          </div>

          {/* Quick Info */}
          <div className="quick-info">
            {bird.family && bird.family !== 'Unknown' && (
              <span className="info-chip family">{bird.family}</span>
            )}
            {bird.size && (
              <span className="info-chip size">{bird.size}</span>
            )}
            {bird.ecology && (
              <span className="info-chip ecology">{bird.ecology}</span>
            )}
          </div>

          {/* Habitat Preview */}
          {bird.habitats && (
            <div className="habitat-preview">
              <span className="habitat-icon">🌍</span>
              <span className="habitat-text">{bird.habitats}</span>
            </div>
          )}

          {/* Audio Preview */}
          {bestAudio && (
            <div className="audio-preview">
              <audio controls className="mini-audio-player">
                <source src={getAudioSrc(bestAudio)} type="audio/wav" />
              </audio>
            </div>
          )}
        </div>

        {/* Hover Action */}
        <div className="card-hover-action">
          <span>Click to view details</span>
        </div>

        {/* Cross Modal Button (appears on hover) */}
        <button
          className="cross-modal-quick-button"
          onClick={(e) => handleCrossModalClick(bird, e)}
          title="Find similar birds"
        >
          🔍
        </button>
      </div>
    );
  };

  return (
    <div className="modern-results-container">
      {/* Birds Grid */}
      <div className="modern-birds-grid">
        {birdsToDisplay.map((bird, index) => renderBirdCard(bird, index))}
      </div>

      {/* Thumbnail Gallery for additional navigation */}
      <BirdThumbnailGallery />

      {/* Detail Panel */}
      <BirdDetailPanel
        bird={detailPanelBird}
        isOpen={!!detailPanelBird}
        onClose={() => setDetailPanelBird(null)}
      />
    </div>
  );
};

export default ResultsDisplay;
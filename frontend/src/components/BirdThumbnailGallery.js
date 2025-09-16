import React, { useState, useEffect } from 'react';
import ApiService from '../services/api';

const BirdThumbnailGallery = () => {
  const [birds, setBirds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlay, setIsAutoPlay] = useState(true);

  const BIRDS_TO_SHOW = 8; // Show 8 birds at a time

  useEffect(() => {
    const fetchBirds = async () => {
      try {
        setLoading(true);
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
        
        setBirds(birdsData);
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch birds:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBirds();
  }, []);

  // Auto-advance slider
  useEffect(() => {
    if (!isAutoPlay || birds.length === 0) return;

    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % birds.length);
    }, 3000); // Move every 3 seconds

    return () => clearInterval(interval);
  }, [isAutoPlay, birds.length]);

  const getImageSrc = (bird) => {
    const image = bird.primary_image || (bird.images && bird.images[0]);
    if (!image) return null;
    return image.image_url || image.source_url || image.image_path;
  };

  const getVisibleBirds = () => {
    if (birds.length === 0) return [];
    
    const visible = [];
    for (let i = 0; i < BIRDS_TO_SHOW; i++) {
      const index = (currentIndex + i) % birds.length;
      visible.push(birds[index]);
    }
    return visible;
  };

  const nextSlide = () => {
    setCurrentIndex(prev => (prev + 1) % birds.length);
  };

  const prevSlide = () => {
    setCurrentIndex(prev => (prev - 1 + birds.length) % birds.length);
  };

  if (loading) {
    return (
      <div className="simple-bird-gallery">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading bird species...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="simple-bird-gallery">
        <div className="error-state">
          <p>Error loading birds: {error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="simple-bird-gallery">
      <div className="gallery-header">
        <h3>All Available Species in Database</h3>
      </div>
      
      <div className="birds-display">
        {getVisibleBirds().map((bird, index) => (
          <div key={`${bird.bird_id}-${currentIndex}-${index}`} className="bird-card">
            <div className="bird-image">
              {getImageSrc(bird) ? (
                <img 
                  src={getImageSrc(bird)} 
                  alt={bird.species_name}
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div className="bird-placeholder" style={{ display: getImageSrc(bird) ? 'none' : 'flex' }}>
                🐦
              </div>
            </div>
            <div className="bird-name">{bird.species_name}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BirdThumbnailGallery;
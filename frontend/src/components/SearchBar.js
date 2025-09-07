// src/components/SearchBar.js
import React, { useState } from 'react';

const SearchBar = ({ onSearch, loading, searchType, onSearchTypeChange }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && searchType === 'text') {
      onSearch(query);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  const searchTypes = [
    { value: 'text', label: 'Text Search', icon: '🔍' },
    { value: 'image', label: 'Image Search', icon: '🖼️' },
    { value: 'audio', label: 'Audio Search', icon: '🎵' }
  ];

  const placeholderText = {
    text: 'Search for birds by description (e.g., "small red bird that sings")',
    image: 'Upload an image to find similar birds',
    audio: 'Upload an audio file to find similar bird sounds'
  };

  return (
    <div className="search-bar-container">
      {/* Search Type Tabs */}
      <div className="search-type-tabs">
        {searchTypes.map((type) => (
          <button
            key={type.value}
            className={`search-type-tab ${searchType === type.value ? 'active' : ''}`}
            onClick={() => onSearchTypeChange(type.value)}
            disabled={loading}
          >
            <span className="tab-icon">{type.icon}</span>
            <span className="tab-label">{type.label}</span>
          </button>
        ))}
      </div>

      {/* Text Search Bar */}
      {searchType === 'text' && (
        <form onSubmit={handleSubmit} className="text-search-form">
          <div className="search-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholderText[searchType]}
              className="search-input"
              disabled={loading}
              onKeyPress={handleKeyPress}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="search-button"
            >
              {loading ? (
                <div className="loading-spinner"></div>
              ) : (
                <>
                  <span>Search</span>
                  <span className="search-icon">🔍</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* File Upload Instructions */}
      {searchType !== 'text' && (
        <div className="file-upload-instructions">
          <p>{placeholderText[searchType]}</p>
          <div className="supported-formats">
            {searchType === 'image' && (
              <span>Supported formats: JPEG, PNG, WebP</span>
            )}
            {searchType === 'audio' && (
              <span>Supported formats: WAV, MP3, M4A</span>
            )}
          </div>
        </div>
      )}

      {/* Search Examples */}
      {searchType === 'text' && (
        <div className="search-examples">
          <span className="examples-label">Try searching for:</span>
          <div className="example-chips">
            <button
              className="example-chip"
              onClick={() => setQuery('red bird with black wings')}
              disabled={loading}
            >
              red bird with black wings
            </button>
            <button
              className="example-chip"
              onClick={() => setQuery('small songbird in forest')}
              disabled={loading}
            >
              small songbird in forest
            </button>
            <button
              className="example-chip"
              onClick={() => setQuery('migratory waterfowl')}
              disabled={loading}
            >
              migratory waterfowl
            </button>
            <button
              className="example-chip"
              onClick={() => setQuery('crow family scavenger')}
              disabled={loading}
            >
              crow family scavenger
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBar;
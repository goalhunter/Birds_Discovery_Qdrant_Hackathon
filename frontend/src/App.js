// src/App.js
import React, { useState, useEffect } from 'react';
import SearchBar from './components/SearchBar';
import FileUpload from './components/FileUpload';
import ResultsDisplay from './components/ResultsDisplay';
import CrossModalSearch from './components/CrossModalSearch';
import ApiService from './services/api';
import './styles/App.css';

function App() {
  const [searchType, setSearchType] = useState('text');
  const [searchResults, setSearchResults] = useState([]);
  const [crossModalResults, setCrossModalResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState(null);

  // Check API connection on component mount
  useEffect(() => {
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      const status = await ApiService.getCollectionsStatus();
      setApiStatus(status);
    } catch (error) {
      console.error('API connection failed:', error);
      setError('Failed to connect to backend API. Please ensure the server is running.');
    }
  };

  const handleTextSearch = async (query) => {
    setLoading(true);
    setError('');
    setCrossModalResults(null);

    try {
      const response = await ApiService.searchByText(query);
      setSearchResults(response.results || []);
    } catch (error) {
      setError(`Text search failed: ${error.message}`);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError('');
    setCrossModalResults(null);

    try {
      let response;
      if (searchType === 'image') {
        response = await ApiService.searchByImage(file);
      } else if (searchType === 'audio') {
        response = await ApiService.searchByAudio(file);
      }
      
      setSearchResults(response.results || []);
    } catch (error) {
      setError(`${searchType} search failed: ${error.message}`);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCrossModalSearch = async (birdId) => {
    setLoading(true);
    setError('');

    try {
      const response = await ApiService.crossModalSearch(birdId);
      setCrossModalResults(response);
    } catch (error) {
      setError(`Cross-modal search failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setSearchResults([]);
    setCrossModalResults(null);
    setError('');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Multi-Modal Bird Search</h1>
        <p>Discover birds through text, images, or audio using AI-powered vector search</p>
      </header>

      <main className="main-content">

        {/* Search Interface */}
        <SearchBar
          searchType={searchType}
          onSearchTypeChange={setSearchType}
          onSearch={handleTextSearch}
          loading={loading}
        />

        {/* File Upload for Image/Audio Search */}
        {searchType !== 'text' && (
          <FileUpload
            searchType={searchType}
            onFileUpload={handleFileUpload}
            loading={loading}
          />
        )}

        {/* Error Display */}
        {error && (
          <div className="error-container">
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
              <button onClick={() => setError('')} className="error-close">
                ×
              </button>
            </div>
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <ResultsDisplay
            results={searchResults}
            searchType={searchType}
            onCrossModalSearch={handleCrossModalSearch}
            loading={loading}
          />
        )}

        {/* Cross-Modal Results */}
        {crossModalResults && (
          <CrossModalSearch
            crossModalResults={crossModalResults}
            loading={loading}
          />
        )}

        {/* Clear Results Button */}
        {(searchResults.length > 0 || crossModalResults) && (
          <div className="clear-results-container">
            <button
              onClick={clearResults}
              className="clear-results-button"
              disabled={loading}
            >
              Clear All Results
            </button>
          </div>
        )}

        {/* Instructions */}
        <div className="instructions-container">
          <h3>How to Use</h3>
          <div className="instruction-grid">
            <div className="instruction-item">
              <div className="instruction-icon">🔍</div>
              <h4>Text Search</h4>
              <p>Describe the bird you're looking for using natural language. Try "small red bird" or "migratory waterfowl".</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">📷</div>
              <h4>Image Search</h4>
              <p>Upload a photo of a bird to find visually similar species using computer vision.</p>
            </div>
            <div className="instruction-item">
              <div className="instruction-icon">🎵</div>
              <h4>Audio Search</h4>
              <p>Upload a bird sound recording to find species with similar vocalizations.</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by Qdrant Vector Database • Built for Qdrant Hackathon 2024</p>
      </footer>
    </div>
  );
}

export default App;
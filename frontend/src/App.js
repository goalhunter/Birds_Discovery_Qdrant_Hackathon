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
  const [allBirds, setAllBirds] = useState([]); // New: for initial display
  const [crossModalResults, setCrossModalResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState(null);
  const [hasSearched, setHasSearched] = useState(false); // New: track if user searched

  // Check API connection and load initial birds
  useEffect(() => {
    checkApiConnection();
    loadInitialBirds(); // New: load birds on startup
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

  // New: Load initial birds to display
  const loadInitialBirds = async () => {
    try {
      const response = await ApiService.searchByText('bird'); // Generic search to get birds
      setAllBirds(response.results || []);
    } catch (error) {
      console.error('Failed to load initial birds:', error);
    }
  };

  const handleTextSearch = async (query) => {
    setLoading(true);
    setError('');
    setCrossModalResults(null);
    setHasSearched(true); // New: mark that user has searched

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
    setHasSearched(true); // New: mark that user has searched

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
    setHasSearched(false); // New: reset search state
  };

  // New: determine what birds to display
  const displayBirds = hasSearched ? searchResults : allBirds;

  return (
    <div className="app">
      {/* Compact Header */}
      <header className="app-header compact">
        <div className="header-content">
          <div className="header-branding">
            <div className="header-text">
              <h1>
                <img 
                  src="/icons8-bird.gif" 
                  alt="Animated bird icon" 
                  className="app-logo inline"
                  width="32" 
                  height="32"
                />
                Bird Discovery
              </h1>
              <p>Explore the world of birds through multi-modal search engine</p>
            </div>
          </div>
        </div>
        
        {/* Stats in top-right corner */}
        <div className="header-stats-corner">
          <div className="stat-item">
            <span className="stat-number">88</span>
            <span className="stat-label">Species</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">3</span>
            <span className="stat-label">Modalities</span>
          </div>
        </div>
      </header>

      {/* New Layout: Sidebar + Main Content */}
      <div className="app-layout">
        {/* Search Sidebar */}
        <aside className="search-sidebar">
          <SearchBar
            searchType={searchType}
            onSearchTypeChange={setSearchType}
            onSearch={handleTextSearch}
            loading={loading}
          />

          {searchType !== 'text' && (
            <FileUpload
              searchType={searchType}
              onFileUpload={handleFileUpload}
              loading={loading}
            />
          )}

          {/* Error Display in Sidebar */}
          {error && (
            <div className="error-container">
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
                <button onClick={() => setError('')} className="error-close">×</button>
              </div>
            </div>
          )}

          {/* Clear Results in Sidebar */}
          {(searchResults.length > 0 || crossModalResults) && (
            <div className="clear-results-container">
              <button onClick={clearResults} className="clear-results-button" disabled={loading}>
                Clear Results
              </button>
            </div>
          )}
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          {/* Results Display - shows all birds initially, search results after search */}
          <ResultsDisplay
            results={displayBirds}
            searchType={hasSearched ? searchType : 'browse'}
            onCrossModalSearch={handleCrossModalSearch}
            loading={loading}
            isInitialView={!hasSearched}
          />

          {/* Cross-Modal Results */}
          {crossModalResults && (
            <CrossModalSearch
              crossModalResults={crossModalResults}
              loading={loading}
            />
          )}
        </main>
      </div>

      <footer className="app-footer">
        <p>Powered by Qdrant Vector Database • Built for Qdrant Hackathon 2025</p>
      </footer>
    </div>
  );
}

export default App;
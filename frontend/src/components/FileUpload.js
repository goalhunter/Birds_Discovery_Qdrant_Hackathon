// src/components/FileUpload.js
import React, { useState, useRef } from 'react';

const FileUpload = ({ onFileUpload, searchType, loading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const acceptedTypes = {
    image: {
      accept: 'image/*',
      types: ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'],
      maxSize: 10 * 1024 * 1024, // 10MB
    },
    audio: {
      accept: 'audio/*',
      types: ['audio/wav', 'audio/mp3', 'audio/m4a', 'audio/ogg'],
      maxSize: 50 * 1024 * 1024, // 50MB
    }
  };

  const validateFile = (file) => {
    const config = acceptedTypes[searchType];
    
    if (!config.types.includes(file.type)) {
      throw new Error(`Invalid file type. Please upload a ${searchType} file.`);
    }
    
    if (file.size > config.maxSize) {
      const maxSizeMB = config.maxSize / (1024 * 1024);
      throw new Error(`File too large. Maximum size is ${maxSizeMB}MB.`);
    }
    
    return true;
  };

  const handleFile = async (file) => {
    try {
      validateFile(file);
      setSelectedFile(file);
      
      // Create preview for images
      if (searchType === 'image') {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      }
      
      // Auto-upload after file selection
      onFileUpload(file);
      
    } catch (error) {
      alert(error.message);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="file-upload-container">
      {!selectedFile ? (
        <div
          className={`file-drop-zone ${dragActive ? 'drag-active' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptedTypes[searchType].accept}
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            disabled={loading}
          />
          
          <div className="drop-zone-content">
            <div className="drop-zone-icon">
              {searchType === 'image' ? '📷' : '🎵'}
            </div>
            <div className="drop-zone-text">
              <p className="primary-text">
                Drop your {searchType} file here or click to browse
              </p>
              <p className="secondary-text">
                {searchType === 'image' 
                  ? 'JPEG, PNG, WebP (max 10MB)'
                  : 'WAV, MP3, M4A (max 50MB)'
                }
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="file-selected-container">
          {/* File Preview */}
          <div className="file-preview">
            {searchType === 'image' && previewUrl && (
              <div className="image-preview">
                <img src={previewUrl} alt="Preview" className="preview-image" />
              </div>
            )}
            
            {searchType === 'audio' && (
              <div className="audio-preview">
                <div className="audio-icon">🎵</div>
                <audio controls className="audio-player">
                  <source src={URL.createObjectURL(selectedFile)} type={selectedFile.type} />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
          </div>

          {/* File Info */}
          <div className="file-info">
            <div className="file-details">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">{formatFileSize(selectedFile.size)}</span>
            </div>
            
            <div className="file-actions">
              <button
                onClick={clearFile}
                className="clear-file-button"
                disabled={loading}
              >
                Remove
              </button>
              
              <button
                onClick={() => onFileUpload(selectedFile)}
                className="search-file-button"
                disabled={loading}
              >
                {loading ? (
                  <div className="loading-spinner-small"></div>
                ) : (
                  `Search by ${searchType}`
                )}
              </button>
            </div>
          </div>

          {loading && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div className="progress-fill"></div>
              </div>
              <span className="progress-text">
                Processing {searchType}...
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
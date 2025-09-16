// src/services/api.js
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  // Test API connection
  static async testConnection() {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      if (!response.ok) throw new Error('Connection failed');
      return await response.json();
    } catch (error) {
      console.error('API connection test failed:', error);
      throw error;
    }
  }

  // Get collections status
  static async getCollectionsStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/collections/status`);
      if (!response.ok) throw new Error('Failed to get collections status');
      return await response.json();
    } catch (error) {
      console.error('Collections status check failed:', error);
      throw error;
    }
  }

  // Text search
  static async searchByText(query, limit = 12) {
    try {
      const response = await fetch(`${API_BASE_URL}/search/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, limit }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Text search failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Text search failed:', error);
      throw error;
    }
  }

  // Image search
  static async searchByImage(file, limit = 12) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('limit', limit.toString());

      const response = await fetch(`${API_BASE_URL}/search/image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Image search failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Image search failed:', error);
      throw error;
    }
  }

  // Audio search
  static async searchByAudio(file, limit = 12) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('limit', limit.toString());

      const response = await fetch(`${API_BASE_URL}/search/audio`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Audio search failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Audio search failed:', error);
      throw error;
    }
  }

  // Cross-modal search
  static async crossModalSearch(birdId, limit = 5) {
    try {
      const response = await fetch(`${API_BASE_URL}/search/cross-modal/${birdId}?limit=${limit}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Cross-modal search failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Cross-modal search failed:', error);
      throw error;
    }
  }

  // Get bird information
  static async getBirdInfo(birdId) {
    try {
      const response = await fetch(`${API_BASE_URL}/bird/${birdId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get bird info');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get bird info failed:', error);
      throw error;
    }
  }

  // Get database statistics
  static async getDatabaseStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get database stats');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get database stats failed:', error);
      throw error;
    }
  }

  // Enhance bird description using AI
  static async enhanceDescription(bird) {
    try {
      // Use the searchable_text from raw_text_data which contains all the structured info
      const searchableText = bird.raw_text_data?.searchable_text || bird.text_description || '';
      
      console.log('Sending to enhance-description:', { searchableText }); // Debug log
      
      const response = await fetch(`${API_BASE_URL}/enhance-description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          raw_text_data: {
            searchable_text: searchableText
          }
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to enhance description');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Enhance description failed:', error);
      throw error;
    }
  }

  // Get all birds
  static async getAllBirds() {
    try {
      const response = await fetch(`${API_BASE_URL}/birds/all`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get all birds');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get all birds failed:', error);
      throw error;
    }
  }
}

export default ApiService;
/**
 * API client for communicating with the FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add request interceptor for session handling
apiClient.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem('pi_strategist_session_id');
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId;
  }
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Store session ID from response headers if present
    const sessionId = response.headers['x-session-id'];
    if (sessionId) {
      localStorage.setItem('pi_strategist_session_id', sessionId);
    }
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      localStorage.removeItem('pi_strategist_session_id');
    }
    // Extract detail message from FastAPI error responses
    const detail = error.response?.data?.detail;
    if (detail) {
      const enriched = new Error(detail);
      (enriched as any).status = error.response?.status;
      return Promise.reject(enriched);
    }
    return Promise.reject(error);
  }
);

export default apiClient;

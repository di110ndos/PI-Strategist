/**
 * API client for communicating with the FastAPI backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const SESSION_ID_KEY = 'pi_strategist_session_id';
const SESSION_TOKEN_KEY = 'pi_strategist_session_token';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add request interceptor for session handling
apiClient.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem(SESSION_ID_KEY);
  const sessionToken = localStorage.getItem(SESSION_TOKEN_KEY);
  if (sessionId && sessionToken) {
    config.headers['X-Session-ID'] = sessionId;
    config.headers['X-Session-Token'] = sessionToken;
  }
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Store session credentials from response headers if present
    const sessionId = response.headers['x-session-id'];
    const sessionToken = response.headers['x-session-token'];
    if (sessionId) {
      localStorage.setItem(SESSION_ID_KEY, sessionId);
    }
    if (sessionToken) {
      localStorage.setItem(SESSION_TOKEN_KEY, sessionToken);
    }
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      localStorage.removeItem(SESSION_ID_KEY);
      localStorage.removeItem(SESSION_TOKEN_KEY);
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

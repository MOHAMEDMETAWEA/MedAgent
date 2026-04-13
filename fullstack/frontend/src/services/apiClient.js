import axios from 'axios';
import { config } from '../config/env';

/**
 * Centrialized axios instance for API calls.
 * Implements security headers and Bearer token injection.
 */
const apiClient = axios.create({
  baseURL: config.api.baseUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor to inject Token
apiClient.interceptors.request.use(
  (reqConfig) => {
    const token = localStorage.getItem('medagent_token');
    if (token) {
      reqConfig.headers.Authorization = `Bearer ${token}`;
    }
    return reqConfig;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor for Global 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      console.warn("Unauthorized access detected. Logging out...");
      localStorage.removeItem('medagent_token');
      window.location.href = '/'; // Fallback to clear state
    }
    return Promise.reject(error);
  }
);

export default apiClient;

/**
 * Centralized Environment Configuration Injector
 * 
 * Ensures all environment variables are loaded and validated correctly.
 * Prevents magic strings and undefined errors across the application.
 */

const getEnvVar = (key, fallback = '') => {
  const value = import.meta.env[key];
  if (value === undefined || value === null) {
    console.warn(`[Config Warning]: Environment variable ${key} is missing.`);
    return fallback;
  }
  return value;
};

export const config = {
  api: {
    baseUrl: getEnvVar('VITE_API_BASE_URL', '/api'),
  },
  ai: {
    baseUrl: getEnvVar('VITE_AI_ENGINE_BASE_URL', 'http://localhost:8000'),
  },
  llm: {
    apiKey: getEnvVar('VITE_LLM_API_KEY'),
  },
  project: {
    stitchId: getEnvVar('VITE_STITCH_PROJECT_ID'),
  },
  auth: {
    domain: getEnvVar('VITE_AUTH_DOMAIN'),
  },
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.MODE === 'production',
};

export default config;

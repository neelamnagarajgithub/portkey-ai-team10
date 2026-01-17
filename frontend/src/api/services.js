import apiClient from './client';

/**
 * Health check endpoint
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

/**
 * Get supported models
 */
export const getSupportedModels = async () => {
  const response = await apiClient.get('/api/models');
  return response.data;
};

/**
 * Replay prompts across models and get analysis
 */
export const replayAndAnalyze = async (request) => {
  const response = await apiClient.post('/api/replay', request);
  return response.data;
};

/**
 * Quick test endpoint
 */
export const quickTest = async (models) => {
  // FastAPI expects query parameters as models=model1&models=model2
  const params = new URLSearchParams();
  models.forEach(model => params.append('models', model));
  const response = await apiClient.post(`/api/quick-test?${params.toString()}`);
  return response.data;
};

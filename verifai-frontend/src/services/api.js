import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const ANALYTICS_API_KEY = process.env.REACT_APP_ANALYTICS_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (ANALYTICS_API_KEY) {
      config.headers = config.headers ?? {};
      config.headers['x-api-key'] = ANALYTICS_API_KEY;
    }
    const token = localStorage.getItem('verifai_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('verifai_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const analyticsAPI = {
  getDashboardData: (days = 30) => api.get(`/analytics/dashboard?days=${days}`),
  getROI: (params) => api.post('/analytics/roi', params),
  getQualityMetrics: (days = 30) => api.get(`/analytics/quality?days=${days}`),
  getCostBreakdown: (days = 30) => api.get(`/analytics/cost?days=${days}`),
  getBenchmarks: (industry) => api.get(`/analytics/benchmarks/${industry}`),
};

export const costAPI = {
  getDashboard: (days = 30) => api.get(`/cost/dashboard?days=${days}`),
  getOptimizations: () => api.get('/cost/optimizations'),
  applyOptimization: (suggestionId) => api.post(`/cost/optimizations/${suggestionId}/apply`),
  setBudget: (config) => api.post('/cost/budget', config),
};

export const agentAPI = {
  review: (payload) => api.post('/panel/review', payload),
};

export default api;

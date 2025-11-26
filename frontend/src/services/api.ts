import axios from 'axios';
import type { ChatRequest, ChatResponse, StatsResponse, SearchResponse } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat', request);
  return response.data;
}

// Search API
export async function search(query: string, limit = 10): Promise<SearchResponse> {
  const response = await api.get<SearchResponse>('/search', {
    params: { q: query, limit },
  });
  return response.data;
}

// Stats API
export async function getStats(): Promise<StatsResponse> {
  const response = await api.get<StatsResponse>('/stats');
  return response.data;
}

// Health check
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await api.get('/health');
    return response.status === 200;
  } catch {
    return false;
  }
}

export default api;

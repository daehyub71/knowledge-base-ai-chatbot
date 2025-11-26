// Chat message types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  doc_id: string;
  doc_type: 'jira' | 'confluence';
  title: string;
  url?: string;
  score: number;
}

// API types
export interface ChatRequest {
  query: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  sources: Source[];
  metadata?: {
    query_time_ms: number;
    model: string;
  };
}

export interface StatsResponse {
  total_documents: number;
  total_chunks: number;
  by_type: {
    jira: number;
    confluence: number;
  };
  last_sync?: string;
}

export interface SearchResult {
  doc_id: string;
  doc_type: string;
  title: string;
  content: string;
  score: number;
  url?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

// Chat session
export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Analysis API endpoints.
 */

import apiClient from '../client';
import type { AnalysisResponse, AIInsightsResponse, ChatMessage } from '../../types';

export interface AnalysisRequest {
  ded_file_id?: string | null;
  excel_file_id?: string | null;
  buffer_percentage?: number;
  cd_target_percentage?: number;
}

export interface SavedAnalysis {
  id: string;
  name: string;
  year: string;
  quarter: string;
  created_at: string;
  summary: {
    risk: { total: number; critical: number };
    capacity: { total_sprints: number; passing: number };
  };
}

export const analysisApi = {
  /**
   * Run full analysis on uploaded files.
   */
  runAnalysis: async (request: AnalysisRequest): Promise<AnalysisResponse> => {
    const response = await apiClient.post<AnalysisResponse>('/analysis/full', request);
    return response.data;
  },

  /**
   * Save analysis results.
   */
  saveAnalysis: async (analysisId: string, metadata: { name: string; year: string; quarter: string }): Promise<SavedAnalysis> => {
    const response = await apiClient.post<SavedAnalysis>(`/analyses/${analysisId}/save`, metadata);
    return response.data;
  },

  /**
   * List saved analyses.
   */
  listSaved: async (): Promise<{ analyses: SavedAnalysis[] }> => {
    const response = await apiClient.get<{ analyses: SavedAnalysis[] }>('/analyses');
    return response.data;
  },

  /**
   * Get a saved analysis by ID.
   */
  getSaved: async (id: string): Promise<AnalysisResponse> => {
    const response = await apiClient.get<AnalysisResponse>(`/analyses/${id}`);
    return response.data;
  },

  /**
   * Delete a saved analysis.
   */
  deleteSaved: async (id: string): Promise<void> => {
    await apiClient.delete(`/analyses/${id}`);
  },
};

export default analysisApi;

// ─── AI Insights API ──────────────────────────────────────────

export interface InsightsRequest {
  pi_analysis: Record<string, unknown>;
  capacity_plan?: Record<string, unknown> | null;
  red_flags?: unknown[] | null;
  insight_type?: string;
}

export interface ChatRequest {
  question: string;
  pi_analysis: Record<string, unknown>;
  capacity_plan?: Record<string, unknown> | null;
  previous_insights?: AIInsightsResponse | null;
  conversation_history: ChatMessage[];
}

export const aiInsightsApi = {
  generateInsights: async (request: InsightsRequest): Promise<AIInsightsResponse> => {
    const response = await apiClient.post<AIInsightsResponse>('/ai/insights', request);
    return response.data;
  },

  chat: async (request: ChatRequest): Promise<{ answer: string }> => {
    const response = await apiClient.post<{ answer: string }>('/ai/chat', request);
    return response.data;
  },
};

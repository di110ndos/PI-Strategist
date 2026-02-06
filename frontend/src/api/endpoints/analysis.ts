/**
 * Analysis API endpoints.
 */

import apiClient from '../client';
import type { AnalysisResponse } from '../../types';

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

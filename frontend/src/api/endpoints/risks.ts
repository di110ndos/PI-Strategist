/**
 * Risk Register API endpoints.
 */

import apiClient from '../client';
import type { Risk, RiskSummary } from '../../types';

export interface CreateRiskRequest {
  title: string;
  description: string;
  category: 'technical' | 'resource' | 'schedule' | 'scope' | 'external' | 'general';
  probability: number;
  impact: number;
  owner: string;
  mitigation_plan: string;
}

export interface UpdateRiskRequest extends Partial<CreateRiskRequest> {
  status?: 'open' | 'mitigating' | 'mitigated' | 'accepted' | 'closed';
}

export const risksApi = {
  /**
   * List all risks, optionally filtered by status.
   */
  list: async (status?: string): Promise<Risk[]> => {
    const params = status ? { status } : {};
    const response = await apiClient.get<{ risks: Risk[] }>('/risks', { params });
    return response.data.risks;
  },

  /**
   * Get risk summary with heat map data.
   */
  summary: async (): Promise<RiskSummary> => {
    const response = await apiClient.get<RiskSummary>('/risks/summary');
    return response.data;
  },

  /**
   * Create a new risk.
   */
  create: async (request: CreateRiskRequest): Promise<Risk> => {
    const response = await apiClient.post<Risk>('/risks', request);
    return response.data;
  },

  /**
   * Update an existing risk.
   */
  update: async (id: string, request: UpdateRiskRequest): Promise<Risk> => {
    const response = await apiClient.put<Risk>(`/risks/${id}`, request);
    return response.data;
  },

  /**
   * Delete a risk.
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/risks/${id}`);
  },
};

export default risksApi;

/**
 * PI Objectives API endpoints.
 */

import apiClient from '../client';
import type { PIObjective } from '../../types';

export interface CreateObjectiveRequest {
  name: string;
  description: string;
  objective_type: 'committed' | 'stretch';
  business_value: number;
  acceptance_criteria: string;
}

export interface UpdateObjectiveRequest extends Partial<CreateObjectiveRequest> {
  status?: 'planned' | 'in_progress' | 'completed' | 'at_risk';
  linked_stories?: string[];
}

export const objectivesApi = {
  /**
   * List all PI objectives.
   */
  list: async (): Promise<PIObjective[]> => {
    const response = await apiClient.get<{ objectives: PIObjective[] }>('/objectives');
    return response.data.objectives;
  },

  /**
   * Create a new PI objective.
   */
  create: async (request: CreateObjectiveRequest): Promise<PIObjective> => {
    const response = await apiClient.post<PIObjective>('/objectives', request);
    return response.data;
  },

  /**
   * Update an existing PI objective.
   */
  update: async (id: string, request: UpdateObjectiveRequest): Promise<PIObjective> => {
    const response = await apiClient.put<PIObjective>(`/objectives/${id}`, request);
    return response.data;
  },

  /**
   * Delete a PI objective.
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/objectives/${id}`);
  },
};

export default objectivesApi;

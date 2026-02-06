/**
 * Quick check API endpoints.
 */

import apiClient from '../client';
import type { QuickCheckResponse } from '../../types';

export interface QuickCheckRequest {
  text: string;
}

export const quickCheckApi = {
  /**
   * Analyze text for red flags, obligations, and SLA metrics.
   */
  analyze: async (request: QuickCheckRequest): Promise<QuickCheckResponse> => {
    const response = await apiClient.post<QuickCheckResponse>('/quick-check', request);
    return response.data;
  },
};

export default quickCheckApi;

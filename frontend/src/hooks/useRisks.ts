/**
 * React Query hooks for Risk Register operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { risksApi, type CreateRiskRequest, type UpdateRiskRequest } from '../api/endpoints/risks';
import type { Risk, RiskSummary } from '../types';

/**
 * Hook to list all risks, optionally filtered by status.
 */
export function useRisks(status?: string) {
  return useQuery({
    queryKey: ['risks', status],
    queryFn: () => risksApi.list(status),
  });
}

/**
 * Hook to get risk summary with heat map data.
 */
export function useRiskSummary() {
  return useQuery<RiskSummary>({
    queryKey: ['risks', 'summary'],
    queryFn: risksApi.summary,
  });
}

/**
 * Hook to create a new risk.
 */
export function useCreateRisk() {
  const queryClient = useQueryClient();

  return useMutation<Risk, Error, CreateRiskRequest>({
    mutationFn: risksApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}

/**
 * Hook to update an existing risk.
 */
export function useUpdateRisk() {
  const queryClient = useQueryClient();

  return useMutation<Risk, Error, { id: string; data: UpdateRiskRequest }>({
    mutationFn: ({ id, data }) => risksApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}

/**
 * Hook to delete a risk.
 */
export function useDeleteRisk() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: risksApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}

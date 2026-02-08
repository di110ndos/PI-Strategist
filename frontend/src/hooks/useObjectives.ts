/**
 * React Query hooks for PI Objectives operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { objectivesApi, type CreateObjectiveRequest, type UpdateObjectiveRequest } from '../api/endpoints/objectives';
import type { PIObjective } from '../types';

/**
 * Hook to list all PI objectives.
 */
export function useObjectives() {
  return useQuery({
    queryKey: ['objectives'],
    queryFn: objectivesApi.list,
  });
}

/**
 * Hook to create a new PI objective.
 */
export function useCreateObjective() {
  const queryClient = useQueryClient();

  return useMutation<PIObjective, Error, CreateObjectiveRequest>({
    mutationFn: objectivesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['objectives'] });
    },
  });
}

/**
 * Hook to update an existing PI objective.
 */
export function useUpdateObjective() {
  const queryClient = useQueryClient();

  return useMutation<PIObjective, Error, { id: string; data: UpdateObjectiveRequest }>({
    mutationFn: ({ id, data }) => objectivesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['objectives'] });
    },
  });
}

/**
 * Hook to delete a PI objective.
 */
export function useDeleteObjective() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: objectivesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['objectives'] });
    },
  });
}

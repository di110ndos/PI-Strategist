/**
 * React Query hooks for analysis operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analysisApi, aiInsightsApi, type AnalysisRequest, type InsightsRequest, type ChatRequest } from '../api/endpoints/analysis';
import { filesApi } from '../api/endpoints/files';
import type { AnalysisResponse, AIInsightsResponse } from '../types';

/**
 * Hook to upload a file.
 */
export function useFileUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, fileType }: { file: File; fileType: 'ded' | 'excel' }) =>
      filesApi.upload(file, fileType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
    },
  });
}

/**
 * Hook to list uploaded files.
 */
export function useFiles() {
  return useQuery({
    queryKey: ['files'],
    queryFn: filesApi.list,
  });
}

/**
 * Hook to run full analysis.
 */
export function useRunAnalysis() {
  return useMutation<AnalysisResponse, Error, AnalysisRequest>({
    mutationFn: analysisApi.runAnalysis,
  });
}

/**
 * Hook to list saved analyses.
 */
export function useSavedAnalyses() {
  return useQuery({
    queryKey: ['savedAnalyses'],
    queryFn: analysisApi.listSaved,
  });
}

/**
 * Hook to get a saved analysis.
 */
export function useSavedAnalysis(id: string | undefined) {
  return useQuery({
    queryKey: ['savedAnalysis', id],
    queryFn: () => analysisApi.getSaved(id!),
    enabled: !!id,
  });
}

/**
 * Hook to save analysis.
 */
export function useSaveAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ analysisId, metadata }: { analysisId: string; metadata: { name: string; year: string; quarter: string } }) =>
      analysisApi.saveAnalysis(analysisId, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedAnalyses'] });
    },
  });
}

/**
 * Hook to delete a saved analysis.
 */
export function useDeleteAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: analysisApi.deleteSaved,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedAnalyses'] });
    },
  });
}

/**
 * Hook to generate AI insights.
 */
export function useAIInsights() {
  return useMutation<AIInsightsResponse, Error, InsightsRequest>({
    mutationFn: aiInsightsApi.generateInsights,
  });
}

/**
 * Hook to generate rebalancing suggestions.
 */
export function useRebalancing() {
  return useMutation<AIInsightsResponse, Error, InsightsRequest>({
    mutationFn: aiInsightsApi.generateInsights,
  });
}

/**
 * Hook for AI follow-up chat.
 */
export function useAIChat() {
  return useMutation<{ answer: string }, Error, ChatRequest>({
    mutationFn: aiInsightsApi.chat,
  });
}

export default useRunAnalysis;

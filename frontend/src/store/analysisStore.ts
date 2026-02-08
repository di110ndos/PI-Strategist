/**
 * Zustand store for persisting analysis results across pages (sessionStorage).
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AnalysisResponse } from '../types';

interface AnalysisStore {
  /** Last completed analysis result. */
  latestAnalysis: AnalysisResponse | null;
  /** Save an analysis result. */
  setLatestAnalysis: (result: AnalysisResponse) => void;
  /** Clear stored analysis. */
  clearAnalysis: () => void;
}

export const useAnalysisStore = create<AnalysisStore>()(
  persist(
    (set) => ({
      latestAnalysis: null,
      setLatestAnalysis: (result) => set({ latestAnalysis: result }),
      clearAnalysis: () => set({ latestAnalysis: null }),
    }),
    {
      name: 'pi-strategist-analysis',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);

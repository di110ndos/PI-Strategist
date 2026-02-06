/**
 * Zustand store for application settings.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // Analysis defaults
  defaultBuffer: number;
  defaultCDTarget: number;

  // API settings
  apiKey: string | null;

  // Actions
  setDefaultBuffer: (value: number) => void;
  setDefaultCDTarget: (value: number) => void;
  setApiKey: (key: string | null) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      defaultBuffer: 20,
      defaultCDTarget: 30,
      apiKey: null,

      setDefaultBuffer: (value) => set({ defaultBuffer: value }),
      setDefaultCDTarget: (value) => set({ defaultCDTarget: value }),
      setApiKey: (key) => set({ apiKey: key }),
    }),
    {
      name: 'pi-strategist-settings',
    }
  )
);

export default useSettingsStore;

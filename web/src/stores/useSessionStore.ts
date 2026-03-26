import { create } from 'zustand';

/**
 * Tracks the current loaded video source — either local file or GCS.
 * Used by save/autosave to determine where to write annotations.
 */
interface SessionState {
  sourceType: 'local' | 'gcs' | null;
  gameFolder: string | null;
  videoFile: string | null;

  setGCSSource: (gameFolder: string, videoFile: string) => void;
  setLocalSource: () => void;
  clearSource: () => void;
}

export const useSessionStore = create<SessionState>()((set) => ({
  sourceType: null,
  gameFolder: null,
  videoFile: null,

  setGCSSource: (gameFolder, videoFile) =>
    set({ sourceType: 'gcs', gameFolder, videoFile }),

  setLocalSource: () =>
    set({ sourceType: 'local', gameFolder: null, videoFile: null }),

  clearSource: () =>
    set({ sourceType: null, gameFolder: null, videoFile: null }),
}));

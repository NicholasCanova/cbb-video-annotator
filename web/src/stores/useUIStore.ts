import { create } from 'zustand';

interface UIState {
  theme: 'light' | 'dark';
  showAnnotationEditor: boolean;
  editorPreselect: string | null; // label from hotkey combo
  pauseAtEvents: boolean;
  pauseAtFilter: string[];
  displayEvents: boolean;
  displayFilter: string[];

  setTheme: (t: 'light' | 'dark') => void;
  toggleTheme: () => void;
  openEditor: (preselect?: string) => void;
  closeEditor: () => void;
  setPauseAtEvents: (v: boolean) => void;
  setPauseAtFilter: (f: string[]) => void;
  setDisplayEvents: (v: boolean) => void;
  setDisplayFilter: (f: string[]) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  theme: 'light',
  showAnnotationEditor: false,
  editorPreselect: null,
  pauseAtEvents: false,
  pauseAtFilter: [],
  displayEvents: false,
  displayFilter: [],

  setTheme: (t) => set({ theme: t }),
  toggleTheme: () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
  openEditor: (preselect) => set({ showAnnotationEditor: true, editorPreselect: preselect ?? null }),
  closeEditor: () => set({ showAnnotationEditor: false, editorPreselect: null }),
  setPauseAtEvents: (v) => set({ pauseAtEvents: v }),
  setPauseAtFilter: (f) => set({ pauseAtFilter: f }),
  setDisplayEvents: (v) => set({ displayEvents: v }),
  setDisplayFilter: (f) => set({ displayFilter: f }),
}));

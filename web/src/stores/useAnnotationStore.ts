import { create } from 'zustand';
import type { Annotation, VideoMeta, AnnotationFile, AnnotationJSON } from '../types/annotation';
import { generateAnnotationId } from '../types/annotation';

interface AnnotationState {
  annotations: Annotation[];
  selectedId: string | null;
  editingId: string | null;
  editingOriginalFrame: number | null;
  isDirty: boolean;
  filter: string;
  videoMeta: VideoMeta;

  addAnnotation: (a: Annotation) => void;
  updateAnnotation: (id: string, patch: Partial<Annotation>) => void;
  deleteAnnotation: (id: string) => void;
  setSelectedId: (id: string | null) => void;
  enterEditMode: (id: string) => void;
  exitEditMode: (save: boolean) => void;
  setFilter: (f: string) => void;
  loadFromJSON: (json: string) => void;
  exportToJSON: () => string;
  setVideoMeta: (meta: Partial<VideoMeta>) => void;
  reset: () => void;

  // Helpers
  findById: (id: string) => Annotation | undefined;
  findIndexById: (id: string) => number;
}

const defaultMeta: VideoMeta = {
  UrlLocal: '',
  UrlYoutube: '',
  gameHomeTeam: '',
  gameAwayTeam: '',
  gameDate: '',
  gameScore: '',
};

function sortByFrame(a: Annotation, b: Annotation) {
  return a.frame - b.frame;
}

export const useAnnotationStore = create<AnnotationState>()((set, get) => ({
  annotations: [],
  selectedId: null,
  editingId: null,
  editingOriginalFrame: null,
  isDirty: false,
  filter: '',
  videoMeta: { ...defaultMeta },

  findById: (id) => get().annotations.find((a) => a.id === id),
  findIndexById: (id) => get().annotations.findIndex((a) => a.id === id),

  addAnnotation: (a) =>
    set((s) => ({
      annotations: [...s.annotations, a].sort(sortByFrame),
      isDirty: true,
    })),

  updateAnnotation: (id, patch) =>
    set((s) => {
      const updated = s.annotations.map((a) => (a.id === id ? { ...a, ...patch } : a));
      return { annotations: updated.sort(sortByFrame), isDirty: true };
    }),

  deleteAnnotation: (id) =>
    set((s) => ({
      annotations: s.annotations.filter((a) => a.id !== id),
      selectedId: s.selectedId === id ? null : s.selectedId,
      editingId: s.editingId === id ? null : s.editingId,
      editingOriginalFrame: s.editingId === id ? null : s.editingOriginalFrame,
      isDirty: true,
    })),

  setSelectedId: (id) => set({ selectedId: id }),

  enterEditMode: (id) =>
    set((s) => {
      const ann = s.annotations.find((a) => a.id === id);
      return {
        editingId: id,
        editingOriginalFrame: ann?.frame ?? null,
        selectedId: id,
      };
    }),

  exitEditMode: (save) =>
    set((s) => {
      if (!save && s.editingId !== null && s.editingOriginalFrame !== null) {
        const fps = 30; // fallback fps for revert position calc
        const orig = s.editingOriginalFrame;
        const updated = s.annotations.map((a) =>
          a.id === s.editingId
            ? { ...a, frame: orig, position: Math.round((orig / fps) * 1000) }
            : a
        );
        return {
          annotations: updated.sort(sortByFrame),
          editingId: null,
          editingOriginalFrame: null,
        };
      }
      return { editingId: null, editingOriginalFrame: null };
    }),

  setFilter: (f) => set({ filter: f }),

  loadFromJSON: (json) => {
    try {
      const data: AnnotationFile = JSON.parse(json);
      const annotations: Annotation[] = (data.annotations || []).map((a: AnnotationJSON) => ({
        id: generateAnnotationId(),
        frame: parseInt(a.frame, 10) || 0,
        gameTime: a.gameTime || '',
        label: a.label || '',
        subType: a.subType || 'None',
        visibility: a.visibility || 'visible',
        position: parseInt(a.position, 10) || 0,
        note: a.note || 'None',
      }));
      set({
        annotations: annotations.sort(sortByFrame),
        videoMeta: {
          UrlLocal: data.UrlLocal || '',
          UrlYoutube: data.UrlYoutube || '',
          gameHomeTeam: data.gameHomeTeam || '',
          gameAwayTeam: data.gameAwayTeam || '',
          gameDate: data.gameDate || '',
          gameScore: data.gameScore || '',
        },
        isDirty: false,
        selectedId: null,
        editingId: null,
      });
    } catch {
      console.error('Failed to parse annotation JSON');
    }
  },

  exportToJSON: () => {
    const { annotations, videoMeta } = get();
    const out: AnnotationFile = {
      ...videoMeta,
      annotations: annotations.map((a) => ({
        frame: String(a.frame),
        gameTime: a.gameTime,
        label: a.label,
        subType: a.subType,
        visibility: a.visibility,
        position: String(a.position),
        note: a.note,
      })),
    };
    return JSON.stringify(out, null, 4);
  },

  setVideoMeta: (meta) =>
    set((s) => ({ videoMeta: { ...s.videoMeta, ...meta } })),

  reset: () =>
    set({
      annotations: [],
      selectedId: null,
      editingId: null,
      editingOriginalFrame: null,
      isDirty: false,
      filter: '',
      videoMeta: { ...defaultMeta },
    }),
}));

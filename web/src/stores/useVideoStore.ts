import { create } from 'zustand';

interface VideoState {
  videoSrc: string | null;
  fileName: string | null;
  duration: number; // seconds
  currentTime: number; // seconds
  currentFrame: number;
  fps: number;
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  playbackSpeed: number;
  half: 1 | 2;

  setVideoSrc: (src: string | null, name?: string) => void;
  setDuration: (d: number) => void;
  setCurrentTime: (t: number) => void;
  setCurrentFrame: (f: number) => void;
  setFps: (fps: number) => void;
  setIsPlaying: (p: boolean) => void;
  setPlaybackSpeed: (s: number) => void;
  setIsMuted: (m: boolean) => void;
  setVolume: (v: number) => void;
  setHalf: (h: 1 | 2) => void;
  reset: () => void;
}

const initialState = {
  videoSrc: null as string | null,
  fileName: null as string | null,
  duration: 0,
  currentTime: 0,
  currentFrame: 0,
  fps: 30,
  isPlaying: false,
  isMuted: false,
  volume: 1,
  playbackSpeed: 1,
  half: 1 as 1 | 2,
};

export const useVideoStore = create<VideoState>()((set) => ({
  ...initialState,

  setVideoSrc: (src, name) => set({ videoSrc: src, fileName: name ?? null }),
  setDuration: (d) => set({ duration: d }),
  setCurrentTime: (t) => set((s) => ({ currentTime: t, currentFrame: Math.round(t * s.fps) })),
  setCurrentFrame: (f) => set({ currentFrame: f }),
  setFps: (fps) => set({ fps }),
  setIsPlaying: (p) => set({ isPlaying: p }),
  setPlaybackSpeed: (s) => set({ playbackSpeed: s }),
  setIsMuted: (m) => set({ isMuted: m }),
  setVolume: (v) => set({ volume: v }),
  setHalf: (h) => set({ half: h }),
  reset: () => set(initialState),
}));

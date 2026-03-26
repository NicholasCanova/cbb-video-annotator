import { useCallback, type RefObject } from 'react';
import { useVideoStore } from '../stores/useVideoStore';

/**
 * Imperative control over the HTML5 video element.
 */
export function useVideoControl(videoRef: RefObject<HTMLVideoElement | null>) {
  const { fps, setIsPlaying, setPlaybackSpeed } = useVideoStore();

  const play = useCallback(() => {
    const v = videoRef.current;
    if (!v || !v.src) return;
    v.play().catch(() => {
      // Codec not supported or no source — ignore
    });
    setIsPlaying(true);
  }, [videoRef, setIsPlaying]);

  const pause = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    v.pause();
    setIsPlaying(false);
  }, [videoRef, setIsPlaying]);

  const togglePlay = useCallback(() => {
    const v = videoRef.current;
    if (!v || !v.src) return;
    if (v.paused) {
      play();
    } else {
      pause();
    }
  }, [videoRef, play, pause]);

  const seekTo = useCallback((timeSeconds: number) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Math.max(0, Math.min(timeSeconds, v.duration || 0));
  }, [videoRef]);

  const stepFrames = useCallback((count: number) => {
    const v = videoRef.current;
    if (!v) return;
    // Pause first for frame stepping
    if (!v.paused) {
      v.pause();
      setIsPlaying(false);
    }
    const frameDuration = 1 / fps;
    v.currentTime = Math.max(0, Math.min(v.currentTime + count * frameDuration, v.duration || 0));
  }, [videoRef, fps, setIsPlaying]);

  const setSpeed = useCallback((speed: number) => {
    const v = videoRef.current;
    if (v) {
      v.playbackRate = speed;
    }
    setPlaybackSpeed(speed);
  }, [videoRef, setPlaybackSpeed]);

  const rewind = useCallback((seconds: number) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Math.max(0, v.currentTime - seconds);
  }, [videoRef]);

  const jumpForward = useCallback((seconds: number) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Math.min(v.duration || 0, v.currentTime + seconds);
  }, [videoRef]);

  return { play, pause, togglePlay, seekTo, stepFrames, setSpeed, rewind, jumpForward };
}

import { useEffect, useRef, type RefObject } from 'react';
import { useVideoStore } from '../stores/useVideoStore';
import { useAnnotationStore } from '../stores/useAnnotationStore';
import { useUIStore } from '../stores/useUIStore';

/**
 * Auto-pauses video when playback reaches an annotated timestamp.
 * After pausing, the user must play past the annotation before it can trigger again.
 */
export function usePauseAtEvents(videoRef: RefObject<HTMLVideoElement | null>) {
  // Track which annotation positions we've already paused at
  const pausedPositions = useRef<Set<number>>(new Set());
  const videoSrc = useVideoStore((s) => s.videoSrc);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    // Reset when video source changes
    pausedPositions.current.clear();

    const check = () => {
      const { pauseAtEvents, pauseAtFilter } = useUIStore.getState();
      if (!pauseAtEvents) return;
      if (v.paused) return;

      const currentMs = v.currentTime * 1000;
      const { annotations } = useAnnotationStore.getState();
      const speed = v.playbackRate || 1;

      // Window scales with speed so we don't skip events
      const windowMs = Math.max(400, 250 * speed);

      const hit = annotations.find((a) => {
        // Only trigger if we've reached or just passed the annotation
        const delta = currentMs - a.position;
        if (delta < -50 || delta > windowMs) return false;
        // Skip if we already paused at this position
        if (pausedPositions.current.has(a.position)) return false;
        if (pauseAtFilter.length > 0 && !pauseAtFilter.includes(a.label)) return false;
        return true;
      });

      if (hit) {
        v.pause();
        // Mark this position as paused — don't pause here again
        pausedPositions.current.add(hit.position);
        // Do NOT seek back — just pause where we are
      }

      // Clean up: remove positions we've moved well past (> 2 seconds)
      // so rewinding back will re-trigger them
      for (const pos of pausedPositions.current) {
        if (currentMs - pos > 2000 || currentMs < pos - 1000) {
          pausedPositions.current.delete(pos);
        }
      }
    };

    v.addEventListener('timeupdate', check);

    return () => {
      v.removeEventListener('timeupdate', check);
    };
  }, [videoRef, videoSrc]);
}

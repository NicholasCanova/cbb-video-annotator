import { useEffect, useRef, type RefObject } from 'react';
import { useVideoStore } from '../stores/useVideoStore';

/**
 * Syncs the video element's time/duration/frame to the Zustand store.
 * Uses requestVideoFrameCallback (Chrome/Edge) for frame-accurate counting,
 * falls back to timeupdate for other browsers.
 */
export function useFrameSync(videoRef: RefObject<HTMLVideoElement | null>) {
  const { setCurrentTime, setCurrentFrame, setDuration, setIsPlaying, setFps } = useVideoStore();
  const videoSrc = useVideoStore((s) => s.videoSrc);
  const fpsRef = useRef(useVideoStore.getState().fps);

  // Keep fpsRef in sync
  useEffect(() => {
    return useVideoStore.subscribe((s) => {
      fpsRef.current = s.fps;
    });
  }, []);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    let rvfcHandle: number | undefined;

    const syncTime = () => {
      setCurrentTime(v.currentTime);
      setCurrentFrame(Math.round(v.currentTime * fpsRef.current));
    };

    const onLoadedMetadata = () => {
      setDuration(v.duration);
      // Try to detect fps: estimate from first few frames using rvfc
      detectFps(v, setFps);
    };

    const onSeeked = () => syncTime();
    const onPlay = () => setIsPlaying(true);
    const onPause = () => {
      setIsPlaying(false);
      syncTime(); // ensure frame is accurate when paused
    };

    const onError = () => {
      const err = v.error;
      if (err) console.warn(`Video error (code ${err.code}): ${err.message}`);
    };

    // Use requestVideoFrameCallback for frame-accurate updates if available
    const hasRvfc = typeof v.requestVideoFrameCallback === 'function';
    if (hasRvfc) {
      const onFrame = () => {
        syncTime();
        rvfcHandle = v.requestVideoFrameCallback(onFrame);
      };
      rvfcHandle = v.requestVideoFrameCallback(onFrame);
    }
    // Always add timeupdate as well (fallback + backup)
    v.addEventListener('timeupdate', syncTime);

    v.addEventListener('loadedmetadata', onLoadedMetadata);
    v.addEventListener('seeked', onSeeked);
    v.addEventListener('play', onPlay);
    v.addEventListener('pause', onPause);
    v.addEventListener('error', onError);

    if (v.duration && !isNaN(v.duration)) {
      setDuration(v.duration);
    }

    return () => {
      if (rvfcHandle !== undefined && 'cancelVideoFrameCallback' in v) {
        v.cancelVideoFrameCallback(rvfcHandle);
      }
      v.removeEventListener('timeupdate', syncTime);
      v.removeEventListener('loadedmetadata', onLoadedMetadata);
      v.removeEventListener('seeked', onSeeked);
      v.removeEventListener('play', onPlay);
      v.removeEventListener('pause', onPause);
      v.removeEventListener('error', onError);
    };
  }, [videoRef, videoSrc, setCurrentTime, setCurrentFrame, setDuration, setIsPlaying, setFps]);
}

/**
 * Detect video FPS by timing two consecutive frames via requestVideoFrameCallback.
 */
function detectFps(
  video: HTMLVideoElement,
  setFps: (fps: number) => void
) {
  if (!('requestVideoFrameCallback' in video)) return;

  let firstTime: number | null = null;
  let sampleCount = 0;
  let totalDelta = 0;

  const sampleFrame = (_now: number, metadata: VideoFrameCallbackMetadata) => {
    if (firstTime === null) {
      firstTime = metadata.mediaTime;
      video.requestVideoFrameCallback(sampleFrame);
      return;
    }

    const delta = metadata.mediaTime - firstTime;
    if (delta > 0) {
      totalDelta += delta;
      sampleCount++;
      firstTime = metadata.mediaTime;
    }

    if (sampleCount < 5) {
      video.requestVideoFrameCallback(sampleFrame);
    } else {
      const avgDelta = totalDelta / sampleCount;
      const detectedFps = Math.round(1 / avgDelta);
      // Only accept reasonable fps values
      if (detectedFps >= 10 && detectedFps <= 120) {
        setFps(detectedFps);
      }
    }
  };

  // Need video to be playing to sample frames
  const wasPlaying = !video.paused;
  if (!wasPlaying) {
    // We'll detect on next play
    const onPlay = () => {
      video.removeEventListener('play', onPlay);
      video.requestVideoFrameCallback(sampleFrame);
    };
    video.addEventListener('play', onPlay);
  } else {
    video.requestVideoFrameCallback(sampleFrame);
  }
}

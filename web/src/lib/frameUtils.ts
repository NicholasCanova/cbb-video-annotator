/**
 * Convert milliseconds to frame number.
 */
export function msToFrame(ms: number, fps: number): number {
  return Math.round((ms / 1000) * fps);
}

/**
 * Convert frame number to milliseconds.
 */
export function frameToMs(frame: number, fps: number): number {
  return Math.round((frame / fps) * 1000);
}

/**
 * Duration of a single frame in seconds.
 */
export function frameDurationSec(fps: number): number {
  return 1 / fps;
}

/**
 * Format milliseconds to "H - MM:SS" game time string.
 */
export function msToGameTime(ms: number, half: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const mm = String(minutes).padStart(2, '0');
  const ss = String(seconds).padStart(2, '0');
  return `${half} - ${mm}:${ss}`;
}

/**
 * Format seconds to MM:SS display string.
 */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

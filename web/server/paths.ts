/**
 * Centralized GCS path logic.
 * All path building goes through here so it's easy to change the layout later.
 */

const BASE_PREFIX = process.env.GCS_PREFIX || 'video/video-annotation-tasks';

export function gamesPrefix(): string {
  return `${BASE_PREFIX}/`;
}

export function gamePrefix(gameId: string): string {
  return `${BASE_PREFIX}/${gameId}/`;
}

export function metaPath(gameId: string): string {
  return `${BASE_PREFIX}/${gameId}/meta.json`;
}

export function annotationsDir(gameId: string): string {
  return `${BASE_PREFIX}/${gameId}/annotations`;
}

export function userAnnotationPath(
  gameId: string,
  videoFilename: string,
  username: string
): string {
  const stem = videoFilename.replace(/\.[^.]+$/, '');
  return `${annotationsDir(gameId)}/${stem}_${username}.json`;
}

export function labelsV2Path(gameId: string): string {
  return `${annotationsDir(gameId)}/Labels-v2.json`;
}

export function legacyLabelsPath(gameId: string): string {
  return `${BASE_PREFIX}/${gameId}/Labels-v2.json`;
}

export interface Annotation {
  id: string; // stable unique ID (not persisted to JSON, generated at runtime)
  frame: number;
  gameTime: string; // "1 - 00:06"
  label: string;
  subType: string;
  visibility: string;
  position: number; // milliseconds
  note: string;
}

let _nextId = 1;
export function generateAnnotationId(): string {
  return `ann_${_nextId++}_${Date.now()}`;
}

export interface VideoMeta {
  UrlLocal: string;
  UrlYoutube: string;
  gameHomeTeam: string;
  gameAwayTeam: string;
  gameDate: string;
  gameScore: string;
}

export interface AnnotationFile {
  UrlLocal: string;
  UrlYoutube: string;
  gameHomeTeam: string;
  gameAwayTeam: string;
  gameDate: string;
  gameScore: string;
  annotations: AnnotationJSON[];
}

/** Raw JSON shape (position/frame are strings in the file) */
export interface AnnotationJSON {
  frame: string;
  gameTime: string;
  label: string;
  subType: string;
  visibility: string;
  position: string;
  note: string;
}

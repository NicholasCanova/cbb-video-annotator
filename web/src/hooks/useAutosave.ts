import { useEffect, useRef } from 'react';
import { useAnnotationStore } from '../stores/useAnnotationStore';
import { useSessionStore } from '../stores/useSessionStore';
import { saveAnnotations } from '../lib/api';

const AUTOSAVE_KEY = 'cbb-annotator-autosave';
const AUTOSAVE_INTERVAL_MS = 30_000;

/**
 * Autosaves to localStorage always, and to GCS if a GCS session is active.
 */
export function useAutosave() {
  const isDirty = useAnnotationStore((s) => s.isDirty);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      if (!useAnnotationStore.getState().isDirty) return;
      const json = useAnnotationStore.getState().exportToJSON();
      localStorage.setItem(AUTOSAVE_KEY, json);

      const { sourceType, gameFolder, videoFile } = useSessionStore.getState();
      if (sourceType === 'gcs' && gameFolder && videoFile) {
        const data = JSON.parse(json);
        saveAnnotations(gameFolder, videoFile, data)
          .then(() => useAnnotationStore.setState({ isDirty: false }))
          .catch((err) => console.warn('GCS autosave failed:', err));
      }
    }, AUTOSAVE_INTERVAL_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Immediate localStorage save when dirty
  useEffect(() => {
    if (isDirty) {
      const json = useAnnotationStore.getState().exportToJSON();
      localStorage.setItem(AUTOSAVE_KEY, json);
    }
  }, [isDirty]);
}

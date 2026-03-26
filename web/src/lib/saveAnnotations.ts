import { useAnnotationStore } from '../stores/useAnnotationStore';
import { useSessionStore } from '../stores/useSessionStore';
import { saveAnnotations as saveToGCS } from './api';

/**
 * Single save entry point for the entire app.
 * Used by: Save button, Ctrl+S hotkey, autosave timer.
 *
 * If a GCS session is active, saves to GCS.
 * Otherwise, downloads JSON locally.
 */
export async function saveCurrentAnnotations() {
  const json = useAnnotationStore.getState().exportToJSON();
  const { sourceType, gameFolder, videoFile } = useSessionStore.getState();

  if (sourceType === 'gcs' && gameFolder && videoFile) {
    try {
      const data = JSON.parse(json);
      await saveToGCS(gameFolder, videoFile, data);
      useAnnotationStore.setState({ isDirty: false });
    } catch (err: any) {
      console.error('GCS save failed, falling back to download:', err);
      downloadJSON(json);
    }
  } else {
    downloadJSON(json);
  }
}

function downloadJSON(json: string) {
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Labels-v2.json';
  a.click();
  URL.revokeObjectURL(url);
}

import { notifications } from '@mantine/notifications';
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
      notifications.show({
        title: '✓ Saved',
        message: 'Annotations saved successfully.',
        color: 'green',
        withBorder: true,
        autoClose: 3000,
        styles: {
          root: { backgroundColor: 'var(--mantine-color-green-7)', border: '2px solid var(--mantine-color-green-5)' },
          title: { color: 'white', fontWeight: 700, fontSize: '1rem' },
          description: { color: 'rgba(255,255,255,0.9)' },
          closeButton: { color: 'white' },
        },
      });
    } catch (err: any) {
      console.error('GCS save failed, falling back to download:', err);
      notifications.show({
        title: '✕ Save failed — downloading instead',
        message: err?.message ?? 'Could not reach server.',
        color: 'red',
        withBorder: true,
        autoClose: 5000,
        styles: {
          root: { backgroundColor: 'var(--mantine-color-red-7)', border: '2px solid var(--mantine-color-red-5)' },
          title: { color: 'white', fontWeight: 700, fontSize: '1rem' },
          description: { color: 'rgba(255,255,255,0.9)' },
          closeButton: { color: 'white' },
        },
      });
      downloadJSON(json);
    }
  } else {
    downloadJSON(json);
    notifications.show({
      title: '↓ Downloaded',
      message: 'Annotations downloaded as Labels-v2.json.',
      color: 'blue',
      withBorder: true,
      autoClose: 3000,
      styles: {
        root: { backgroundColor: 'var(--mantine-color-blue-7)', border: '2px solid var(--mantine-color-blue-5)' },
        title: { color: 'white', fontWeight: 700, fontSize: '1rem' },
        description: { color: 'rgba(255,255,255,0.9)' },
        closeButton: { color: 'white' },
      },
    });
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

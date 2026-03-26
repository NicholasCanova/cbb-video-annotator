import { useAnnotationStore } from '../stores/useAnnotationStore';

/**
 * Trigger a JSON file download of current annotations.
 */
export function downloadAnnotations(filename = 'Labels-v2.json') {
  const json = useAnnotationStore.getState().exportToJSON();
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

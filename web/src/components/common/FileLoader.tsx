import { useRef } from 'react';
import { Group, Button } from '@mantine/core';
import { IconFolderOpen, IconFileImport } from '@tabler/icons-react';
import { useVideoStore } from '../../stores/useVideoStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useSessionStore } from '../../stores/useSessionStore';

export function FileLoader() {
  const videoInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const setVideoSrc = useVideoStore((s) => s.setVideoSrc);
  const loadFromJSON = useAnnotationStore((s) => s.loadFromJSON);

  const handleVideoFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Revoke previous object URL if any
    const prev = useVideoStore.getState().videoSrc;
    if (prev?.startsWith('blob:')) URL.revokeObjectURL(prev);
    const url = URL.createObjectURL(file);
    setVideoSrc(url, file.name);
    // Mark as local source so autosave doesn't write to a previous GCS target
    useSessionStore.getState().setLocalSource();
    // Reset annotations when loading new video
    useAnnotationStore.getState().reset();
  };

  const handleJSONFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result;
      if (typeof text === 'string') {
        loadFromJSON(text);
      }
    };
    reader.readAsText(file);
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  return (
    <Group gap="xs">
      <input
        ref={videoInputRef}
        type="file"
        accept="video/*"
        style={{ display: 'none' }}
        onChange={handleVideoFile}
      />
      <input
        ref={jsonInputRef}
        type="file"
        accept=".json"
        style={{ display: 'none' }}
        onChange={handleJSONFile}
      />
      <Button
        variant="subtle"
        size="compact-sm"
        leftSection={<IconFolderOpen size={16} />}
        onClick={() => videoInputRef.current?.click()}
      >
        Open Video
      </Button>
      <Button
        variant="subtle"
        size="compact-sm"
        leftSection={<IconFileImport size={16} />}
        onClick={() => jsonInputRef.current?.click()}
      >
        Load JSON
      </Button>
    </Group>
  );
}

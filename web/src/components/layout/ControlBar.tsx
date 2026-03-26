import { useRef, useState } from 'react';
import { Group, Button, ActionIcon, Text, Tooltip, Divider, Stack } from '@mantine/core';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconArrowLeft,
  IconArrowRight,
  IconDeviceFloppy,
  IconDownload,
  IconVolume,
  IconVolumeOff,
  IconMaximize,
  IconHelp,
  IconPlayerPauseFilled,
  IconEye,
} from '@tabler/icons-react';
import { useVideoStore } from '../../stores/useVideoStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useUIStore } from '../../stores/useUIStore';
import { HelpModal } from '../common/HelpModal';
import { saveCurrentAnnotations } from '../../lib/saveAnnotations';

interface ControlBarProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  videoContainerRef: React.RefObject<HTMLDivElement | null>;
  onTogglePlay: () => void;
  onStepFrames: (count: number) => void;
  onSetSpeed: (speed: number) => void;
  onRewind: (seconds: number) => void;
  onJumpForward: (seconds: number) => void;
}

const SPEEDS = [0.5, 1, 2, 4, 8];
const SKIP_SECS = [5, 10, 20, 30];

export function ControlBar({ videoRef, videoContainerRef, onTogglePlay, onStepFrames, onSetSpeed, onRewind, onJumpForward }: ControlBarProps) {
  const isPlaying = useVideoStore((s) => s.isPlaying);
  const playbackSpeed = useVideoStore((s) => s.playbackSpeed);
  const videoSrc = useVideoStore((s) => s.videoSrc);
  const fileName = useVideoStore((s) => s.fileName);
  const isDirty = useAnnotationStore((s) => s.isDirty);
  const pauseAtEvents = useUIStore((s) => s.pauseAtEvents);
  const setPauseAtEvents = useUIStore((s) => s.setPauseAtEvents);
  const displayEvents = useUIStore((s) => s.displayEvents);
  const setDisplayEvents = useUIStore((s) => s.setDisplayEvents);
  const volumeRef = useRef<HTMLInputElement>(null);
  const [helpOpen, setHelpOpen] = useState(false);

  const isMuted = useVideoStore((s) => s.isMuted);
  const setIsMuted = useVideoStore((s) => s.setIsMuted);
  const setStoreVolume = useVideoStore((s) => s.setVolume);

  const handleMuteToggle = () => {
    const v = videoRef.current;
    if (!v) return;
    const newMuted = !v.muted;
    v.muted = newMuted;
    setIsMuted(newMuted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    const val = parseFloat(e.target.value);
    v.volume = val;
    v.muted = val === 0;
    setStoreVolume(val);
    setIsMuted(val === 0);
  };

  const handleSave = () => saveCurrentAnnotations();

  const handleFullscreen = () => {
    const el = videoContainerRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      el.requestFullscreen();
    }
  };

  const d = !videoSrc;

  return (
    <>
      <Stack gap={0} style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
        {/* Row 1: Playback controls */}
        <Group gap="xs" px="sm" py={5} wrap="nowrap">
          {/* Play/Pause */}
          <Tooltip label={isPlaying ? 'Pause (Space)' : 'Play (Space)'}>
            <ActionIcon variant="subtle" onClick={onTogglePlay} disabled={d} size="lg">
              {isPlaying ? <IconPlayerPause size={20} /> : <IconPlayerPlay size={20} />}
            </ActionIcon>
          </Tooltip>

          {/* Frame step */}
          <Tooltip label="Step back 1 frame (Left arrow)">
            <ActionIcon variant="subtle" onClick={() => onStepFrames(-1)} disabled={d}>
              <IconArrowLeft size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Step forward 1 frame (Right arrow)">
            <ActionIcon variant="subtle" onClick={() => onStepFrames(1)} disabled={d}>
              <IconArrowRight size={16} />
            </ActionIcon>
          </Tooltip>

          <Divider orientation="vertical" />

          {/* Speed */}
          <Text size="xs" c="dimmed" fw={600}>Speed:</Text>
          {SPEEDS.map((s) => (
            <Button
              key={s}
              variant={playbackSpeed === s ? 'filled' : 'subtle'}
              size="compact-sm"
              onClick={() => onSetSpeed(s)}
              disabled={d}
            >
              {s}x
            </Button>
          ))}

          <Divider orientation="vertical" />

          {/* Rewind */}
          <Text size="xs" c="dimmed" fw={600}>Rewind:</Text>
          {SKIP_SECS.map((sec) => (
            <Button key={`rw-${sec}`} variant="subtle" size="compact-sm" onClick={() => onRewind(sec)} disabled={d}>
              -{sec}s
            </Button>
          ))}

          <Divider orientation="vertical" />

          {/* Jump */}
          <Text size="xs" c="dimmed" fw={600}>Jump:</Text>
          {SKIP_SECS.map((sec) => (
            <Button key={`jmp-${sec}`} variant="subtle" size="compact-sm" onClick={() => onJumpForward(sec)} disabled={d}>
              +{sec}s
            </Button>
          ))}

          <div style={{ flex: 1 }} />

          {/* Fullscreen - right-aligned in row 1 */}
          <Tooltip label="Fullscreen">
            <ActionIcon variant="subtle" onClick={handleFullscreen} disabled={d}>
              <IconMaximize size={18} />
            </ActionIcon>
          </Tooltip>
        </Group>

        {/* Row 2: Features + save */}
        <Group gap="xs" px="sm" py={4} wrap="nowrap" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
          {/* Pause At Tags */}
          <Tooltip label="Auto-pause at annotated frames during playback">
            <Button
              variant={pauseAtEvents ? 'filled' : 'subtle'}
              size="compact-sm"
              leftSection={<IconPlayerPauseFilled size={14} />}
              onClick={() => setPauseAtEvents(!pauseAtEvents)}
            >
              Pause At Tags
            </Button>
          </Tooltip>

          {/* Display Events */}
          <Tooltip label="Show event badges on video during playback">
            <Button
              variant={displayEvents ? 'filled' : 'subtle'}
              size="compact-sm"
              leftSection={<IconEye size={14} />}
              onClick={() => setDisplayEvents(!displayEvents)}
            >
              Display Events
            </Button>
          </Tooltip>

          <Divider orientation="vertical" />

          {/* Volume */}
          <Tooltip label="Mute/Unmute">
            <ActionIcon variant="subtle" size="sm" onClick={handleMuteToggle} disabled={d}>
              {isMuted ? <IconVolumeOff size={16} /> : <IconVolume size={16} />}
            </ActionIcon>
          </Tooltip>
          <input
            ref={volumeRef}
            type="range"
            min="0"
            max="1"
            step="0.05"
            defaultValue="1"
            onChange={handleVolumeChange}
            style={{ width: 70, accentColor: 'var(--mantine-color-blue-6)' }}
          />

          {/* Help */}
          <Tooltip label="Help & Keyboard Shortcuts">
            <Button
              variant="subtle"
              size="compact-sm"
              leftSection={<IconHelp size={14} />}
              onClick={() => setHelpOpen(true)}
            >
              Help
            </Button>
          </Tooltip>

          <div style={{ flex: 1 }} />

          {/* Save */}
          <Tooltip label="Save annotations (Ctrl+S)">
            <Button
              variant="subtle"
              size="compact-sm"
              leftSection={isDirty ? <IconDeviceFloppy size={16} /> : <IconDownload size={16} />}
              onClick={handleSave}
              color={isDirty ? 'yellow' : undefined}
            >
              {isDirty ? 'Save*' : 'Save'}
            </Button>
          </Tooltip>

          {fileName && (
            <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {fileName}
            </Text>
          )}
        </Group>
      </Stack>

      <HelpModal opened={helpOpen} onClose={() => setHelpOpen(false)} />
    </>
  );
}

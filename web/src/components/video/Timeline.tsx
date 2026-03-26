import { Slider, Group, Text } from '@mantine/core';
import { useVideoStore } from '../../stores/useVideoStore';
import { formatTime } from '../../lib/frameUtils';

interface TimelineProps {
  onSeek: (timeSeconds: number) => void;
}

export function Timeline({ onSeek }: TimelineProps) {
  const currentTime = useVideoStore((s) => s.currentTime);
  const duration = useVideoStore((s) => s.duration);

  return (
    <div style={{ padding: '4px 12px' }}>
      <Slider
        value={duration > 0 ? (currentTime / duration) * 1000 : 0}
        onChange={(val) => {
          if (duration > 0) {
            onSeek((val / 1000) * duration);
          }
        }}
        min={0}
        max={1000}
        step={0.1}
        label={null}
        size="sm"
        styles={{
          root: { padding: '4px 0' },
          track: { height: 6 },
          thumb: { width: 14, height: 14 },
        }}
      />
      <Group justify="space-between" mt={2}>
        <Text size="xs" c="dimmed">
          {formatTime(currentTime)}
        </Text>
        <Text size="xs" c="dimmed">
          {formatTime(duration)}
        </Text>
      </Group>
    </div>
  );
}

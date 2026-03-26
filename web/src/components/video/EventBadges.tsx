import { useMemo } from 'react';
import { Box, Text } from '@mantine/core';
import { useVideoStore } from '../../stores/useVideoStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useUIStore } from '../../stores/useUIStore';

// Show badge starting at the annotation's time, lasting for this duration
const DISPLAY_DURATION_MS = 2000;

export function EventBadges() {
  const currentTime = useVideoStore((s) => s.currentTime);
  const annotations = useAnnotationStore((s) => s.annotations);
  const displayEvents = useUIStore((s) => s.displayEvents);
  const displayFilter = useUIStore((s) => s.displayFilter);

  const currentMs = currentTime * 1000;

  const visible = useMemo(() => {
    if (!displayEvents) return [];
    return annotations.filter((a) => {
      if (a.visibility === 'not shown') return false;
      if (displayFilter.length > 0 && !displayFilter.includes(a.label)) return false;
      // Show badge from the annotation's position for DISPLAY_DURATION_MS after
      return currentMs >= a.position && currentMs <= a.position + DISPLAY_DURATION_MS;
    });
  }, [annotations, currentMs, displayEvents, displayFilter]);

  if (visible.length === 0) return null;

  return (
    <Box
      pos="absolute"
      top={5}
      left="50%"
      style={{
        transform: 'translateX(-50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 3,
        pointerEvents: 'none',
      }}
    >
      {visible.map((a, i) => (
        <Box
          key={`${a.frame}-${i}`}
          px={16}
          py={4}
          style={{
            background: 'rgba(220, 38, 38, 0.85)',
            borderRadius: 4,
            minWidth: 190,
            textAlign: 'center',
          }}
        >
          <Text size="md" c="white" fw={700}>
            {a.label}
            {a.subType && a.subType !== 'None' ? ` (${a.subType})` : ''}
          </Text>
        </Box>
      ))}
    </Box>
  );
}

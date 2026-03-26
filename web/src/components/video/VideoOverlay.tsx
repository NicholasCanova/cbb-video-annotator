import { Box, Text } from '@mantine/core';
import { useVideoStore } from '../../stores/useVideoStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';

export function VideoOverlay() {
  const currentFrame = useVideoStore((s) => s.currentFrame);
  const editingId = useAnnotationStore((s) => s.editingId);
  const annotations = useAnnotationStore((s) => s.annotations);

  const isEditing = editingId !== null;
  const editingAnnotation = isEditing ? annotations.find((a) => a.id === editingId) : null;

  return (
    <>
      <Box
        pos="absolute"
        top={8}
        left={8}
        px={8}
        py={4}
        style={{
          background: isEditing ? 'rgba(220, 38, 38, 0.85)' : 'rgba(0, 0, 0, 0.6)',
          borderRadius: 4,
          pointerEvents: 'none',
        }}
      >
        {isEditing && editingAnnotation ? (
          <>
            <Text size="xs" c="white" fw={700}>
              EDITING: {editingAnnotation.label}
            </Text>
            <Text size="xs" c="white">
              Frame: {currentFrame}
            </Text>
          </>
        ) : (
          <Text size="xs" c="white" fw={500}>
            Frame: {currentFrame}
          </Text>
        )}
      </Box>
    </>
  );
}

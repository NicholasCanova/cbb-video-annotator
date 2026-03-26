import { useMemo } from 'react';
import { Stack, Table, Text, ScrollArea } from '@mantine/core';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { FilterBar } from './FilterBar';

interface Props {
  videoRef: React.RefObject<HTMLVideoElement | null>;
}

export function AnnotationList({ videoRef }: Props) {
  const annotations = useAnnotationStore((s) => s.annotations);
  const selectedId = useAnnotationStore((s) => s.selectedId);
  const editingId = useAnnotationStore((s) => s.editingId);
  const filter = useAnnotationStore((s) => s.filter);
  const setSelectedId = useAnnotationStore((s) => s.setSelectedId);
  const enterEditMode = useAnnotationStore((s) => s.enterEditMode);

  const filtered = useMemo(() => {
    if (!filter) return annotations;
    const lc = filter.toLowerCase();
    return annotations.filter((a) => a.label.toLowerCase().includes(lc));
  }, [annotations, filter]);

  const handleClick = (ann: typeof annotations[0]) => {
    setSelectedId(ann.id);
    enterEditMode(ann.id);
    if (videoRef.current) {
      videoRef.current.currentTime = ann.position / 1000;
    }
  };

  return (
    <Stack gap="xs" h="100%">
      <FilterBar />
      <Text size="xs" c="dimmed">
        {filtered.length} event{filtered.length !== 1 ? 's' : ''}
        {filter ? ` (filtered)` : ''}
      </Text>
      <ScrollArea style={{ flex: 1 }}>
        <Table
          highlightOnHover
          verticalSpacing={4}
          horizontalSpacing="xs"
          style={{ fontSize: '0.8rem' }}
        >
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={60} style={{ textAlign: 'center' }}>Frame</Table.Th>
              <Table.Th>Action</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {filtered.map((ann) => {
              const isSelected = ann.id === selectedId;
              const isEditing = ann.id === editingId;
              return (
                <Table.Tr
                  key={ann.id}
                  onClick={() => handleClick(ann)}
                  style={{
                    cursor: 'pointer',
                    backgroundColor: isEditing
                      ? 'var(--mantine-color-red-light)'
                      : isSelected
                        ? 'var(--mantine-color-blue-light)'
                        : undefined,
                  }}
                >
                  <Table.Td style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
                    {ann.frame}
                  </Table.Td>
                  <Table.Td>
                    {ann.label}
                    {ann.subType && ann.subType !== 'None' ? ` (${ann.subType})` : ''}
                  </Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Stack>
  );
}

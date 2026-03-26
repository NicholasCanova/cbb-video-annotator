import { useMemo, useState } from 'react';
import { Stack, Table, Text, ScrollArea, Tooltip, ActionIcon, Textarea } from '@mantine/core';
import { IconNote } from '@tabler/icons-react';
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
  const updateAnnotation = useAnnotationStore((s) => s.updateAnnotation);

  const [noteEditId, setNoteEditId] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');

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

  const openNoteEditor = (e: React.MouseEvent, ann: typeof annotations[0]) => {
    e.stopPropagation();
    setNoteEditId(ann.id);
    setNoteText(ann.note !== 'None' ? ann.note : '');
  };

  const saveNote = () => {
    if (noteEditId) {
      updateAnnotation(noteEditId, { note: noteText || 'None' });
      setNoteEditId(null);
    }
  };

  const hasNote = (ann: typeof annotations[0]) =>
    ann.note && ann.note !== 'None' && ann.note.trim() !== '';

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
              <Table.Th w={50} style={{ textAlign: 'center' }}>Frame</Table.Th>
              <Table.Th>Action</Table.Th>
              <Table.Th w={30}></Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {filtered.map((ann) => {
              const isSelected = ann.id === selectedId;
              const isEditing = ann.id === editingId;
              const isNoteOpen = ann.id === noteEditId;
              const noted = hasNote(ann);
              return (
                <>
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
                    <Table.Td style={{ textAlign: 'center', padding: '0 4px' }}>
                      {noted ? (
                        <Tooltip label={ann.note} multiline w={220} position="left">
                          <ActionIcon
                            variant="subtle"
                            size="sm"
                            color="blue"
                            onClick={(e) => openNoteEditor(e, ann)}
                          >
                            <IconNote size={16} />
                          </ActionIcon>
                        </Tooltip>
                      ) : (
                        <ActionIcon
                          variant="transparent"
                          size="sm"
                          color="gray"
                          opacity={0}
                          onClick={(e) => openNoteEditor(e, ann)}
                          style={{ transition: 'opacity 0.15s' }}
                          className="note-add-btn"
                        >
                          <IconNote size={16} />
                        </ActionIcon>
                      )}
                    </Table.Td>
                  </Table.Tr>
                  {isNoteOpen && (
                    <Table.Tr key={`${ann.id}-note`}>
                      <Table.Td colSpan={3} style={{ padding: '4px 8px' }}>
                        <Textarea
                          size="xs"
                          placeholder="Add a note or question..."
                          value={noteText}
                          onChange={(e) => setNoteText(e.currentTarget.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); saveNote(); }
                            if (e.key === 'Escape') setNoteEditId(null);
                          }}
                          minRows={2}
                          maxRows={5}
                          autosize
                          autoFocus
                        />
                      </Table.Td>
                    </Table.Tr>
                  )}
                </>
              );
            })}
          </Table.Tbody>
        </Table>
        {/* Show the add-note button on row hover */}
        <style>{`
          tr:hover .note-add-btn { opacity: 0.4 !important; }
          tr:hover .note-add-btn:hover { opacity: 1 !important; }
        `}</style>
      </ScrollArea>
    </Stack>
  );
}

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Modal, TextInput, Text, UnstyledButton, ScrollArea, Group, Button, Box } from '@mantine/core';
import { useUIStore } from '../../stores/useUIStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useVideoStore } from '../../stores/useVideoStore';
import { getSubtypes, getThirdLevel } from '../../lib/configLoader';
import { useClassesConfig } from '../../hooks/useClassesConfig';
import { msToGameTime, msToFrame } from '../../lib/frameUtils';
import { generateAnnotationId } from '../../types/annotation';

interface Props {
  videoRef: React.RefObject<HTMLVideoElement | null>;
}

// Which column has focus: 0=label, 1=subtype, 2=visibility
type ActiveColumn = 0 | 1 | 2;

export function AnnotationEditor({ videoRef: _videoRef }: Props) {
  const show = useUIStore((s) => s.showAnnotationEditor);
  const preselect = useUIStore((s) => s.editorPreselect);
  const closeEditor = useUIStore((s) => s.closeEditor);

  const addAnnotation = useAnnotationStore((s) => s.addAnnotation);
  const annotations = useAnnotationStore((s) => s.annotations);
  const editingId = useAnnotationStore((s) => s.editingId);
  const updateAnnotation = useAnnotationStore((s) => s.updateAnnotation);

  const currentTime = useVideoStore((s) => s.currentTime);
  const fps = useVideoStore((s) => s.fps);
  const half = useVideoStore((s) => s.half);

  const config = useClassesConfig();
  const [selectedLabel, setSelectedLabel] = useState('');
  const [selectedSubtype, setSelectedSubtype] = useState('');
  const [selectedVisibility, setSelectedVisibility] = useState('');
  const [note, setNote] = useState('');

  // Keyboard navigation state
  const [activeColumn, setActiveColumn] = useState<ActiveColumn>(0);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const noteInputRef = useRef<HTMLInputElement>(null);
  const noteIsFocused = useRef(false);

  // Reset on open
  useEffect(() => {
    if (show) {
      setSelectedSubtype('');
      setSelectedVisibility('');
      setNote('');
      setActiveColumn(0);
      setHighlightedIndex(0);

      if (editingId !== null) {
        const ann = annotations.find((a) => a.id === editingId);
        if (ann) {
          setSelectedLabel(ann.label);
          setSelectedSubtype(ann.subType !== 'None' ? ann.subType : '');
          setSelectedVisibility(ann.visibility || '');
          setNote(ann.note !== 'None' ? ann.note : '');
        }
      } else if (preselect) {
        setSelectedLabel(preselect);
        // Move to next column
        const subs = config ? getSubtypes(config, preselect) : [];
        if (subs.length > 0) {
          setActiveColumn(1);
        } else {
          setActiveColumn(2);
        }
        setHighlightedIndex(0);
      } else {
        setSelectedLabel('');
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps — intentionally only on modal open
  }, [show]);

  const subtypes = useMemo(
    () => (config && selectedLabel ? getSubtypes(config, selectedLabel) : []),
    [config, selectedLabel]
  );
  const thirdLevel = useMemo(
    () => (config && selectedLabel ? getThirdLevel(config, selectedLabel) : []),
    [config, selectedLabel]
  );

  // Get items for the currently active column
  const getColumnItems = useCallback((col: ActiveColumn): string[] => {
    if (!config) return [];
    if (col === 0) return config.labels;
    if (col === 1) return subtypes.length > 0 ? subtypes : thirdLevel;
    if (col === 2) return config.visibility;
    return [];
  }, [config, subtypes, thirdLevel]);

  // --- Click handlers: move highlight only, stay in column. Enter confirms. ---
  const handleLabelClick = (_label: string, index: number) => {
    setActiveColumn(0);
    setHighlightedIndex(index);
  };

  const handleSubtypeClick = (_sub: string, index: number) => {
    setActiveColumn(1);
    setHighlightedIndex(index);
  };

  const handleVisibilityClick = (_vis: string, index: number) => {
    setActiveColumn(2);
    setHighlightedIndex(index);
  };

  // --- Enter handler: confirm current column selection and advance ---
  const advanceFromColumn = useCallback((col: ActiveColumn, itemText: string) => {
    if (col === 0) {
      // Confirm label, advance
      setSelectedLabel(itemText);
      setSelectedSubtype('');
      setSelectedVisibility('');
      const subs = config ? getSubtypes(config, itemText) : [];
      const third = config ? getThirdLevel(config, itemText) : [];
      if (subs.length > 0 || third.length > 0) {
        setActiveColumn(1);
      } else {
        setActiveColumn(2);
      }
      setHighlightedIndex(0);
    } else if (col === 1) {
      setSelectedSubtype(itemText);
      setSelectedVisibility('');
      setActiveColumn(2);
      setHighlightedIndex(0);
    } else if (col === 2) {
      // Final step — save
      setSelectedVisibility(itemText);
      saveAndClose(selectedLabel, selectedSubtype, itemText, note);
    }
  }, [config, selectedLabel, selectedSubtype, note]);

  const saveAndClose = (label: string, subType: string, visibility: string, noteVal: string) => {
    const positionMs = Math.round(currentTime * 1000);
    const frame = msToFrame(positionMs, fps);

    let finalFrame = frame;
    let finalPosition = positionMs;
    const existingFrames = new Set(annotations.map((a) => a.frame));
    const editingAnn = editingId ? annotations.find((a) => a.id === editingId) : null;
    if (editingAnn) {
      existingFrames.delete(editingAnn.frame);
    }
    while (existingFrames.has(finalFrame)) {
      finalFrame += 1;
      finalPosition = Math.round((finalFrame / fps) * 1000);
    }

    if (editingId && editingAnn) {
      updateAnnotation(editingId, {
        frame: finalFrame,
        gameTime: msToGameTime(finalPosition, half),
        label,
        subType: subType || 'None',
        visibility,
        position: finalPosition,
        note: noteVal || 'None',
      });
      useAnnotationStore.getState().exitEditMode(true);
    } else {
      addAnnotation({
        id: generateAnnotationId(),
        frame: finalFrame,
        gameTime: msToGameTime(finalPosition, half),
        label,
        subType: subType || 'None',
        visibility,
        position: finalPosition,
        note: noteVal || 'None',
      });
    }
    closeEditor();
  };

  // Keyboard handler for the modal
  useEffect(() => {
    if (!show || !config) return;

    const handler = (e: KeyboardEvent) => {
      // If note input is focused, only handle Escape
      if (noteIsFocused.current) {
        if (e.key === 'Escape') {
          (document.activeElement as HTMLElement)?.blur();
          e.preventDefault();
        }
        return;
      }

      const items = getColumnItems(activeColumn);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex((prev) => Math.min(prev + 1, items.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const item = items[highlightedIndex];
        if (!item) return;
        advanceFromColumn(activeColumn, item);
      } else if (e.key === 'Backspace' || e.key === 'ArrowLeft') {
        // Go back a column
        if (activeColumn > 0) {
          e.preventDefault();
          setActiveColumn((prev) => (prev - 1) as ActiveColumn);
          setHighlightedIndex(0);
        }
      } else if (e.key === 'Escape') {
        closeEditor();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [show, config, activeColumn, highlightedIndex, getColumnItems, advanceFromColumn, closeEditor]);

  if (!config) return null;

  const showSubtypes = selectedLabel && (subtypes.length > 0 || thirdLevel.length > 0);
  const showVisibility =
    selectedLabel &&
    (subtypes.length === 0 || selectedSubtype) &&
    (thirdLevel.length === 0 || selectedSubtype);

  const col1Items = config.labels;
  const col2Items = subtypes.length > 0 ? subtypes : thirdLevel;
  const col3Items = config.visibility;

  return (
    <Modal
      opened={show}
      onClose={closeEditor}
      title={selectedLabel ? `Event Selection — ${selectedLabel}` : 'Event Selection'}
      size={900}
      centered
      overlayProps={{ backgroundOpacity: 0.3 }}
      styles={{
        body: { padding: '8px 16px 16px' },
      }}
    >
      {/* Multi-column layout */}
      <Group align="stretch" gap="xs" wrap="nowrap" style={{ minHeight: 400 }}>
        {/* Column 1: Labels */}
        <Box style={{ flex: 1, minWidth: 0 }}>
          <Text size="xs" fw={600} mb={4} c={activeColumn === 0 ? 'blue' : 'dimmed'}>
            Action {activeColumn === 0 && '\u25B6'}
          </Text>
          <ScrollArea h={380} style={{ border: `1px solid ${activeColumn === 0 ? 'var(--mantine-color-blue-4)' : 'var(--mantine-color-default-border)'}`, borderRadius: 4 }}>
            {col1Items.map((label, i) => (
              <ColumnItem
                key={label}
                text={label}
                selected={label === selectedLabel}
                highlighted={activeColumn === 0 && i === highlightedIndex}
                onClick={() => handleLabelClick(label, i)}
              />
            ))}
          </ScrollArea>
        </Box>

        {/* Column 2: Subtypes */}
        <Box style={{ flex: 1, minWidth: 0 }}>
          <Text size="xs" fw={600} mb={4} c={activeColumn === 1 ? 'blue' : 'dimmed'}>
            Subtype {activeColumn === 1 && '\u25B6'}
          </Text>
          <ScrollArea h={380} style={{ border: `1px solid ${activeColumn === 1 ? 'var(--mantine-color-blue-4)' : 'var(--mantine-color-default-border)'}`, borderRadius: 4 }}>
            {showSubtypes &&
              col2Items.map((sub, i) => (
                <ColumnItem
                  key={sub}
                  text={sub}
                  selected={sub === selectedSubtype}
                  highlighted={activeColumn === 1 && i === highlightedIndex}
                  onClick={() => handleSubtypeClick(sub, i)}
                />
              ))}
          </ScrollArea>
        </Box>

        {/* Column 3: Visibility */}
        <Box style={{ flex: 1, minWidth: 0 }}>
          <Text size="xs" fw={600} mb={4} c={activeColumn === 2 ? 'blue' : 'dimmed'}>
            Visibility {activeColumn === 2 && '\u25B6'}
          </Text>
          <ScrollArea h={380} style={{ border: `1px solid ${activeColumn === 2 ? 'var(--mantine-color-blue-4)' : 'var(--mantine-color-default-border)'}`, borderRadius: 4 }}>
            {showVisibility &&
              col3Items.map((vis, i) => (
                <ColumnItem
                  key={vis}
                  text={vis}
                  selected={vis === selectedVisibility}
                  highlighted={activeColumn === 2 && i === highlightedIndex}
                  onClick={() => handleVisibilityClick(vis, i)}
                />
              ))}
          </ScrollArea>
        </Box>
      </Group>

      {/* Note field */}
      <TextInput
        ref={noteInputRef}
        placeholder="Note (optional)"
        size="sm"
        mt="sm"
        value={note}
        onChange={(e) => setNote(e.currentTarget.value)}
        onFocus={() => { noteIsFocused.current = true; }}
        onBlur={() => { noteIsFocused.current = false; }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && selectedLabel && selectedVisibility) {
            saveAndClose(selectedLabel, selectedSubtype, selectedVisibility, note);
          }
        }}
      />

      {/* Footer */}
      <Group justify="space-between" mt="sm">
        <Text size="xs" c="dimmed">
          Use <b>Arrow keys</b> to navigate, <b>Enter</b> to select, <b>Esc</b> to cancel
        </Text>
        <Button variant="subtle" size="compact-sm" onClick={closeEditor}>
          Cancel
        </Button>
      </Group>
    </Modal>
  );
}

function ColumnItem({
  text,
  selected,
  highlighted,
  onClick,
}: {
  text: string;
  selected: boolean;
  highlighted: boolean;
  onClick: () => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);

  // Auto-scroll highlighted item into view
  useEffect(() => {
    if (highlighted && ref.current) {
      ref.current.scrollIntoView({ block: 'nearest' });
    }
  }, [highlighted]);

  return (
    <UnstyledButton
      ref={ref}
      onClick={onClick}
      w="100%"
      px="sm"
      py={3}
      style={{
        backgroundColor: selected
          ? 'var(--mantine-color-blue-filled)'
          : highlighted
            ? 'var(--mantine-color-blue-light)'
            : undefined,
        color: selected ? '#fff' : undefined,
      }}
    >
      <Text size="sm" truncate>{text}</Text>
    </UnstyledButton>
  );
}

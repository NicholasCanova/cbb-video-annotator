import { useEffect, useRef } from 'react';
import { HOTKEY_COMBOS, COMBO_FIRST_KEYS } from '../lib/hotkeyMap';
import { useUIStore } from '../stores/useUIStore';
import { useAnnotationStore } from '../stores/useAnnotationStore';
import { useVideoStore } from '../stores/useVideoStore';
import { saveCurrentAnnotations } from '../lib/saveAnnotations';

interface HotkeyActions {
  togglePlay: () => void;
  stepFrames: (count: number) => void;
  setSpeed: (speed: number) => void;
  seekTo: (time: number) => void;
  pause: () => void;
}

export function useHotkeys(actions: HotkeyActions) {
  const actionsRef = useRef(actions);
  actionsRef.current = actions; // always up to date
  const pendingCombo = useRef<string | null>(null);
  const comboTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      // Skip if focus is in an input/textarea
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Skip if annotation editor modal is open
      if (useUIStore.getState().showAnnotationEditor) return;

      // Skip if no video loaded
      if (!useVideoStore.getState().videoSrc) return;

      const { editingId } = useAnnotationStore.getState();
      const isEditing = editingId !== null;

      // --- Shift + key combos for quick annotation ---
      if (e.shiftKey && !e.ctrlKey && !e.metaKey) {
        const key = e.key.toUpperCase();

        // Check if this is the second key of a pending combo
        if (pendingCombo.current !== null) {
          const firstKey = pendingCombo.current;
          const comboMap = HOTKEY_COMBOS[firstKey];
          // Try the raw key first, then the shifted symbol
          const label = comboMap?.[key] ?? comboMap?.[e.key];
          if (label) {
            e.preventDefault();
            clearCombo();
            // Pause video and open editor with preselected label
            actionsRef.current.pause();
            useUIStore.getState().openEditor(label);
            return;
          }
          // No match for second key — clear and fall through
          clearCombo();
        }

        // Check if this is a valid first key
        if (COMBO_FIRST_KEYS.has(key) || COMBO_FIRST_KEYS.has(e.key)) {
          e.preventDefault();
          pendingCombo.current = COMBO_FIRST_KEYS.has(key) ? key : e.key;
          comboTimer.current = setTimeout(() => {
            pendingCombo.current = null;
          }, 1000);
          return;
        }
      }

      // --- Frame stepping (with modifiers for multiplier) ---
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        e.preventDefault();
        let multiplier = 1;
        if (e.shiftKey && (e.ctrlKey || e.metaKey)) multiplier = 50;
        else if (e.ctrlKey || e.metaKey) multiplier = 10;
        else if (e.shiftKey) multiplier = 5;

        const direction = e.key === 'ArrowLeft' ? -1 : 1;

        if (isEditing) {
          const store = useAnnotationStore.getState();
          const ann = store.findById(editingId!);
          if (!ann) return;
          const fps = useVideoStore.getState().fps;
          const newFrame = Math.max(0, ann.frame + direction * multiplier);
          const newPosition = Math.round((newFrame / fps) * 1000);
          store.updateAnnotation(editingId!, { frame: newFrame, position: newPosition });
          actionsRef.current.seekTo(newPosition / 1000);
        } else {
          actionsRef.current.stepFrames(direction * multiplier);
        }
        return;
      }

      // --- Space: play/pause ---
      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        actionsRef.current.togglePlay();
        return;
      }

      // --- Speed controls ---
      if (!e.shiftKey && !e.ctrlKey && !e.metaKey) {
        if (e.key === 'a' || e.key === '1') { actionsRef.current.setSpeed(1); e.preventDefault(); return; }
        if (e.key === 'z' || e.key === '2') { actionsRef.current.setSpeed(2); e.preventDefault(); return; }
        if (e.key === 'e' || e.key === '3') { actionsRef.current.setSpeed(4); e.preventDefault(); return; }
        if (e.key === 's' || e.key === '4') { actionsRef.current.setSpeed(0.5); e.preventDefault(); return; }
      }

      // --- Enter: create annotation or save edit ---
      if (e.key === 'Enter') {
        e.preventDefault();
        if (isEditing) {
          if (e.ctrlKey || e.metaKey) {
            // Ctrl+Enter: reopen editor for the editing annotation
            const ann = useAnnotationStore.getState().findById(editingId!);
            if (ann) useUIStore.getState().openEditor(ann.label);
          } else {
            // Save edit
            useAnnotationStore.getState().exitEditMode(true);
          }
        } else {
          // Create new annotation
          actionsRef.current.pause();
          useUIStore.getState().openEditor();
        }
        return;
      }

      // --- Escape: cancel edit ---
      if (e.key === 'Escape') {
        if (isEditing) {
          e.preventDefault();
          useAnnotationStore.getState().exitEditMode(false);
          return;
        }
      }

      // --- Delete/Backspace: delete selected ---
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const { selectedId, deleteAnnotation } = useAnnotationStore.getState();
        if (selectedId !== null) {
          e.preventDefault();
          deleteAnnotation(selectedId);
        }
        return;
      }

      // --- Ctrl/Cmd+S: save ---
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveCurrentAnnotations();
        return;
      }
    };

    function clearCombo() {
      pendingCombo.current = null;
      if (comboTimer.current) {
        clearTimeout(comboTimer.current);
        comboTimer.current = null;
      }
    }

    window.addEventListener('keydown', handler);
    return () => {
      window.removeEventListener('keydown', handler);
      if (comboTimer.current) clearTimeout(comboTimer.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps — stable via actionsRef
  }, []);
}

import { useRef, useEffect } from 'react';
import { AppShell, Group, Text, Button, Loader, Center } from '@mantine/core';
import { VideoPlayer } from './components/video/VideoPlayer';
import { Timeline } from './components/video/Timeline';
import { ControlBar } from './components/layout/ControlBar';
import { FileLoader } from './components/common/FileLoader';
import { AnnotationList } from './components/annotations/AnnotationList';
import { AnnotationEditor } from './components/annotations/AnnotationEditor';
import { useVideoControl } from './hooks/useVideoControl';
import { useFrameSync } from './hooks/useFrameSync';
import { useHotkeys } from './hooks/useHotkeys';
import { usePauseAtEvents } from './hooks/usePauseAtEvents';
import { ThemeToggle } from './components/common/ThemeToggle';
import { GameBrowser } from './components/common/GameBrowser';
import { useSessionStore } from './stores/useSessionStore';
import { LoginScreen } from './components/common/LoginScreen';
import { useAutosave } from './hooks/useAutosave';
import { useAuthStore } from './stores/useAuthStore';
import { getMe, logout } from './lib/api';
import { useAnnotationStore } from './stores/useAnnotationStore';
import { useUIStore } from './stores/useUIStore';

export default function App() {
  const username = useAuthStore((s) => s.username);
  const authLoading = useAuthStore((s) => s.loading);
  const setUsername = useAuthStore((s) => s.setUsername);
  const setAuthLoading = useAuthStore((s) => s.setLoading);

  const videoRef = useRef<HTMLVideoElement>(null);
  const videoContainerRef = useRef<HTMLDivElement>(null);
  const { togglePlay, stepFrames, setSpeed, rewind, jumpForward, seekTo, pause } = useVideoControl(videoRef);

  useFrameSync(videoRef);
  useHotkeys({ togglePlay, stepFrames, setSpeed, seekTo, pause });
  useAutosave();
  usePauseAtEvents(videoRef);

  // Check existing session on mount
  useEffect(() => {
    getMe()
      .then((user) => {
        if (user) setUsername(user.username);
      })
      .catch(() => {})
      .finally(() => setAuthLoading(false));
  }, [setUsername, setAuthLoading]);

  const handleLogout = async () => {
    await logout();
    setUsername(null);
    useAnnotationStore.getState().reset();
    useUIStore.getState().closeEditor();
    useSessionStore.getState().clearSource();
    localStorage.removeItem('cbb-annotator-autosave');
  };

  // Loading state
  if (authLoading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  // Not logged in
  if (!username) {
    return <LoginScreen />;
  }

  // Logged in — show app
  return (
    <AppShell
      padding={0}
      header={{ height: 44 }}
      aside={{ width: 320, breakpoint: 'sm' }}
    >
      <AppShell.Header>
        <Group h="100%" px="sm" justify="space-between">
          <Group gap="xs">
            <FileLoader />
            <GameBrowser />
          </Group>
          <Group gap="xs">
            <Text size="sm" c="dimmed">{username}</Text>
            <Button variant="subtle" size="compact-xs" onClick={handleLogout}>
              Logout
            </Button>
            <ThemeToggle />
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Main style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <div ref={videoContainerRef} style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <VideoPlayer videoRef={videoRef} />
          <Timeline onSeek={seekTo} />
          <ControlBar
            videoRef={videoRef}
            videoContainerRef={videoContainerRef}
            onTogglePlay={togglePlay}
            onStepFrames={stepFrames}
            onSetSpeed={setSpeed}
            onRewind={rewind}
            onJumpForward={jumpForward}
          />
        </div>
      </AppShell.Main>

      <AppShell.Aside p="xs">
        <AnnotationList videoRef={videoRef} />
      </AppShell.Aside>

      <AnnotationEditor videoRef={videoRef} />
    </AppShell>
  );
}

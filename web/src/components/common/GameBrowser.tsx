import { useState, useEffect } from 'react';
import { Modal, Stack, Text, Button, Group, Loader, Table, ScrollArea } from '@mantine/core';
import { IconCloud, IconVideo } from '@tabler/icons-react';
import { fetchGames, fetchVideos, fetchVideoUrl, loadAnnotations, type GameVideo, type GameMeta } from '../../lib/api';
import { useVideoStore } from '../../stores/useVideoStore';
import { useAnnotationStore } from '../../stores/useAnnotationStore';
import { useAuthStore } from '../../stores/useAuthStore';
import { useSessionStore } from '../../stores/useSessionStore';

export function GameBrowser() {
  const [opened, setOpened] = useState(false);
  const [games, setGames] = useState<GameMeta[]>([]);
  const [selectedGame, setSelectedGame] = useState<GameMeta | null>(null);
  const [videos, setVideos] = useState<GameVideo[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const username = useAuthStore((s) => s.username);

  const setVideoSrc = useVideoStore((s) => s.setVideoSrc);

  // Load games when modal opens
  useEffect(() => {
    if (!opened) return;
    setLoading(true);
    setError(null);
    setSelectedGame(null);
    fetchGames()
      .then(setGames)
      .catch((e) => setError(`Failed to load games: ${e.message}`))
      .finally(() => setLoading(false));
  }, [opened]);

  // Load videos when game selected
  useEffect(() => {
    if (!selectedGame) { setVideos([]); return; }
    setLoading(true);
    fetchVideos(selectedGame.gameId)
      .then(setVideos)
      .catch((e) => setError(`Failed to load videos: ${e.message}`))
      .finally(() => setLoading(false));
  }, [selectedGame]);

  const handleVideoSelect = async (video: GameVideo) => {
    if (!selectedGame) return;
    const gameId = selectedGame.gameId;

    setLoadingVideo(video.name);
    setError(null);

    try {
      // Get video URL (signed URL in prod, stream URL in dev)
      const streamUrl = await fetchVideoUrl(gameId, video.name);

      // Revoke previous object URL if any
      const prev = useVideoStore.getState().videoSrc;
      if (prev?.startsWith('blob:')) URL.revokeObjectURL(prev);

      // Load video
      setVideoSrc(streamUrl, video.name);

      // Set GCS session for save/autosave
      useSessionStore.getState().setGCSSource(gameId, video.name);

      // Load existing annotations — don't block video load if this fails
      useAnnotationStore.getState().reset();
      try {
        const result = await loadAnnotations(gameId, video.name);
        if (result.annotations) {
          useAnnotationStore.getState().loadFromJSON(JSON.stringify(result.annotations));
        }
      } catch (annErr: any) {
        console.warn('Failed to load annotations:', annErr.message);
      }

      setOpened(false);
    } catch (e: any) {
      setError(`Failed to load video: ${e.message}`);
    } finally {
      setLoadingVideo(null);
    }
  };

  return (
    <>
      <Button
        variant="subtle"
        size="compact-sm"
        leftSection={<IconCloud size={16} />}
        onClick={() => setOpened(true)}
      >
        Browse Games
      </Button>

      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title="Load from GCS"
        size="lg"
        centered
      >
        <Stack gap="sm">
          <Text size="sm" c="dimmed">
            Logged in as <b>{username}</b> — annotations save to your personal file.
          </Text>

          {error && <Text c="red" size="sm">{error}</Text>}
          {loading && <Loader size="sm" />}

          {/* Game list or video list */}
          {!selectedGame ? (
            <>
              <Text fw={600} size="sm">Select a game:</Text>
              <ScrollArea h={300}>
                <Table highlightOnHover verticalSpacing={6}>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Game</Table.Th>
                      <Table.Th w={100}>Date</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {games.map((game) => (
                      <Table.Tr
                        key={game.gameId}
                        onClick={() => setSelectedGame(game)}
                        style={{ cursor: 'pointer' }}
                      >
                        <Table.Td>
                          <Text size="sm" fw={500}>
                            {game.displayName || game.gameId}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Text size="xs" c="dimmed">{game.date || ''}</Text>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
                {games.length === 0 && !loading && (
                  <Text c="dimmed" size="sm" mt="sm">No games found.</Text>
                )}
              </ScrollArea>
            </>
          ) : (
            <>
              <Group>
                <Button variant="subtle" size="compact-xs" onClick={() => setSelectedGame(null)}>
                  &larr; Back
                </Button>
                <Text fw={600} size="sm">{selectedGame.displayName || selectedGame.gameId}</Text>
              </Group>
              <ScrollArea h={300}>
                <Table highlightOnHover verticalSpacing={6}>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Video</Table.Th>
                      <Table.Th w={100}>Size</Table.Th>
                      <Table.Th w={80}></Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {videos.map((v) => (
                      <Table.Tr key={v.name}>
                        <Table.Td>
                          <Group gap={4}>
                            <IconVideo size={14} />
                            <Text size="sm">{v.name}</Text>
                          </Group>
                        </Table.Td>
                        <Table.Td>
                          <Text size="xs" c="dimmed">{formatSize(v.size)}</Text>
                        </Table.Td>
                        <Table.Td>
                          <Button
                            size="compact-xs"
                            loading={loadingVideo === v.name}
                            onClick={() => handleVideoSelect(v)}
                          >
                            Load
                          </Button>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                    {videos.length === 0 && !loading && (
                      <Table.Tr>
                        <Table.Td colSpan={3}>
                          <Text c="dimmed" size="sm">No video files found.</Text>
                        </Table.Td>
                      </Table.Tr>
                    )}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </>
          )}
        </Stack>
      </Modal>
    </>
  );
}

function formatSize(bytes: string | number | undefined): string {
  if (!bytes) return '';
  const b = typeof bytes === 'string' ? parseInt(bytes, 10) : bytes;
  if (b > 1e9) return `${(b / 1e9).toFixed(1)} GB`;
  if (b > 1e6) return `${(b / 1e6).toFixed(0)} MB`;
  return `${(b / 1e3).toFixed(0)} KB`;
}

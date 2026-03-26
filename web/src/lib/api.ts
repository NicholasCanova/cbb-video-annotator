// In production, API is same origin (no base needed). In dev, point to local server.
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:3001');

const f = (path: string, opts?: RequestInit) =>
  fetch(`${API_BASE}${path}`, { credentials: 'include', ...opts });

// ---- Auth ----

export async function login(username: string, password: string): Promise<{ username: string }> {
  const res = await f('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Login failed');
  }
  return res.json();
}

export async function logout(): Promise<void> {
  await f('/api/auth/logout', { method: 'POST' });
}

export async function getMe(): Promise<{ username: string; allowedGameIds: number[] } | null> {
  const res = await f('/api/auth/me');
  if (!res.ok) return null;
  return res.json();
}

// ---- Videos ----

export interface GameMeta {
  gameId: string;
  date?: string;
  homeTeam?: string;
  awayTeam?: string;
  displayName?: string;
}

export interface GameVideo {
  name: string;
  path: string;
  size: string;
}

export async function fetchGames(): Promise<GameMeta[]> {
  const res = await f('/api/videos');
  if (!res.ok) throw new Error('Failed to load games');
  const data = await res.json();
  return data.games;
}

export async function fetchVideos(gameFolder: string): Promise<GameVideo[]> {
  const res = await f(`/api/videos/${encodeURIComponent(gameFolder)}`);
  if (!res.ok) throw new Error('Failed to load videos');
  const data = await res.json();
  return data.videos;
}

export async function fetchVideoUrl(gameFolder: string, fileName: string): Promise<string> {
  const res = await f(
    `/api/videos/${encodeURIComponent(gameFolder)}/video-url?file=${encodeURIComponent(fileName)}`
  );
  if (!res.ok) throw new Error('Failed to get video URL');
  const data = await res.json();
  return data.url;
}

// ---- Annotations ----

export async function loadAnnotations(
  gameFolder: string,
  videoFile: string
): Promise<{ annotations: any | null; source: string | null }> {
  const res = await f(
    `/api/videos/${encodeURIComponent(gameFolder)}/annotations?video=${encodeURIComponent(videoFile)}`
  );
  if (!res.ok) throw new Error('Failed to load annotations');
  return res.json();
}

export async function saveAnnotations(
  gameFolder: string,
  videoFile: string,
  data: any
): Promise<{ saved: string }> {
  const res = await f(`/api/videos/${encodeURIComponent(gameFolder)}/annotations`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video: videoFile, data }),
  });
  if (!res.ok) throw new Error('Failed to save annotations');
  return res.json();
}

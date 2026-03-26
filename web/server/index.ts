import express from 'express';
import cors from 'cors';
import session from 'express-session';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Storage } from '@google-cloud/storage';
import { createHash, randomBytes } from 'crypto';
import { loadUsers, findUser, verifyPassword, isGameAllowed, extractGameId } from './users.js';
import { requireAuth, getSessionUser } from './auth.js';
import * as paths from './paths.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const IS_PROD = process.env.NODE_ENV === 'production';

const app = express();

// --- Config ---
const BUCKET = process.env.GCS_BUCKET || 'cbb-tracking';
const PORT = parseInt(process.env.PORT || '3001', 10);
const SESSION_SECRET = process.env.SESSION_SECRET || 'cbb-annotator-dev-secret-change-me';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

// --- Middleware ---
if (IS_PROD) {
  app.set('trust proxy', 1); // Trust Cloud Run's load balancer for secure cookies
}
if (!IS_PROD) {
  // Dev: CORS for separate frontend dev server
  app.use(cors({
    origin: FRONTEND_URL,
    credentials: true,
  }));
}
app.use(express.json({ limit: '10mb' }));
app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  proxy: IS_PROD, // trust Cloud Run's proxy
  cookie: {
    httpOnly: true,
    secure: IS_PROD,
    sameSite: 'lax',
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
  },
}));

// --- GCS ---
const storage = new Storage();
const bucket = storage.bucket(BUCKET);

// --- Load users ---
loadUsers();

// ==========================================
// STREAM TOKENS — short-lived tokens for video streaming without cookies
// ==========================================
const streamTokens = new Map<string, { expires: number }>();

function generateStreamToken(): string {
  const token = randomBytes(32).toString('hex');
  // Token valid for 2 hours
  streamTokens.set(token, { expires: Date.now() + 2 * 60 * 60 * 1000 });
  return token;
}

function validateStreamToken(token: string): boolean {
  const entry = streamTokens.get(token);
  if (!entry) return false;
  if (Date.now() > entry.expires) {
    streamTokens.delete(token);
    return false;
  }
  return true;
}

// Cleanup expired tokens every 10 minutes
setInterval(() => {
  const now = Date.now();
  for (const [token, { expires }] of streamTokens) {
    if (now > expires) streamTokens.delete(token);
  }
}, 10 * 60 * 1000);

// ==========================================
// AUTH ENDPOINTS
// ==========================================

/**
 * POST /api/auth/login
 * Body: { username, password }
 */
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }

  const user = findUser(username);
  if (!user || !verifyPassword(user, password)) {
    return res.status(401).json({ error: 'Invalid username or password' });
  }

  req.session.username = user.username;
  res.json({ username: user.username });
});

/**
 * POST /api/auth/logout
 */
app.post('/api/auth/logout', (req, res) => {
  req.session.destroy(() => {
    res.json({ ok: true });
  });
});

/**
 * GET /api/auth/me
 */
app.get('/api/auth/me', (req, res) => {
  const username = getSessionUser(req);
  if (!username) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  const user = findUser(username);
  res.json({
    username,
    allowedGameIds: user?.allowedGameIds || [],
  });
});

// ==========================================
// VIDEO ENDPOINTS (all require auth)
// ==========================================

export interface GameMeta {
  gameId: string;
  date?: string;
  homeTeam?: string;
  awayTeam?: string;
  displayName?: string;
}

/**
 * GET /api/videos
 * List games the current user has access to, with meta.json display info.
 */
app.get('/api/videos', requireAuth, async (req, res) => {
  try {
    const username = getSessionUser(req)!;
    const user = findUser(username)!;

    const [, , apiResponse] = await bucket.getFiles({
      prefix: paths.gamesPrefix(),
      delimiter: '/',
      autoPaginate: false,
    });

    const allFolders: string[] = ((apiResponse as any)?.prefixes || [])
      .map((p: string) => p.replace(paths.gamesPrefix(), '').replace(/\/$/, ''))
      .filter((name: string) => name && name !== 'annotations');

    // Filter by allowed game IDs
    const allowedFolders = allFolders.filter((folder: string) => {
      const gameId = extractGameId(folder);
      return isGameAllowed(user, gameId);
    });

    // Load meta.json for each game (in parallel)
    const games: GameMeta[] = await Promise.all(
      allowedFolders.map(async (folder) => {
        const metaFile = bucket.file(paths.metaPath(folder));
        try {
          const [exists] = await metaFile.exists();
          if (exists) {
            const [content] = await metaFile.download();
            const meta = JSON.parse(content.toString());
            return {
              gameId: folder,
              date: meta.date,
              homeTeam: meta.homeTeam,
              awayTeam: meta.awayTeam,
              displayName: meta.displayName || `${meta.awayTeam} @ ${meta.homeTeam}`,
            };
          }
        } catch {
          // meta.json missing or invalid — use folder name
        }
        return { gameId: folder, displayName: folder };
      })
    );

    res.json({ games });
  } catch (err: any) {
    console.error('Error listing games:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/videos/:gameFolder
 * List video files in a game folder. Verifies access.
 */
app.get('/api/videos/:gameFolder', requireAuth, async (req, res) => {
  try {
    const username = getSessionUser(req)!;
    const user = findUser(username)!;
    const { gameFolder } = req.params;

    // Check access
    const gameId = extractGameId(gameFolder);
    if (!isGameAllowed(user, gameId)) {
      return res.status(403).json({ error: 'Access denied to this game' });
    }

    const prefix = paths.gamePrefix(gameFolder);
    const [files] = await bucket.getFiles({ prefix });

    const videos = files
      .filter((f) => /\.(mp4|mkv|mov|webm)$/i.test(f.name))
      .map((f) => ({
        name: f.name.replace(prefix, ''),
        path: f.name,
        size: f.metadata.size,
      }));

    res.json({ videos });
  } catch (err: any) {
    console.error('Error listing videos:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/videos/:gameFolder/video-url?file=...
 * Returns a tokenized stream URL the browser can use to load the video.
 * Auth is checked here; the token allows /stream to skip session cookies.
 */
app.get('/api/videos/:gameFolder/video-url', requireAuth, async (req, res) => {
  try {
    const username = getSessionUser(req)!;
    const user = findUser(username)!;
    const { gameFolder } = req.params;
    const fileName = req.query.file as string;

    if (!fileName) {
      return res.status(400).json({ error: 'file query param required' });
    }

    const gameId = extractGameId(gameFolder);
    if (!isGameAllowed(user, gameId)) {
      return res.status(403).json({ error: 'Access denied to this game' });
    }

    const filePath = `${paths.gamePrefix(gameFolder)}${fileName}`;

    // Return the stream proxy URL — works in both dev and prod
    // No signed URL needed; server streams from GCS with its own credentials
    // Generate a short-lived token so /stream doesn't need session cookies
    const token = generateStreamToken();
    const streamPath = `/api/videos/${encodeURIComponent(gameFolder)}/stream?file=${encodeURIComponent(fileName)}&token=${token}`;
    if (IS_PROD) {
      return res.json({ url: streamPath });
    } else {
      return res.json({ url: `http://localhost:${PORT}${streamPath}` });
    }
  } catch (err: any) {
    console.error('Error generating video URL:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/videos/:gameFolder/stream?file=...
 * Stream a video file from GCS through the server (dev fallback).
 */
app.get('/api/videos/:gameFolder/stream', async (req, res) => {
  try {
    const { gameFolder } = req.params;
    const fileName = req.query.file as string;
    const token = req.query.token as string;

    if (!fileName) {
      return res.status(400).json({ error: 'file query param required' });
    }

    // Validate stream token (issued by /video-url after auth check)
    if (!token || !validateStreamToken(token)) {
      return res.status(403).json({ error: 'Invalid or expired stream token' });
    }
    const filePath = `${paths.gamePrefix(gameFolder)}${fileName}`;
    const file = bucket.file(filePath);

    const [metadata] = await file.getMetadata();
    const fileSize = parseInt(metadata.size as string, 10);
    const contentType = metadata.contentType || 'video/mp4';

    const range = req.headers.range;
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : Math.min(start + 10 * 1024 * 1024 - 1, fileSize - 1); // 10MB chunks
      const chunkSize = end - start + 1;

      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunkSize,
        'Content-Type': contentType,
      });

      file.createReadStream({ start, end }).pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': contentType,
        'Accept-Ranges': 'bytes',
      });

      file.createReadStream().pipe(res);
    }
  } catch (err: any) {
    console.error('Error streaming video:', err.message);
    if (!res.headersSent) {
      res.status(500).json({ error: err.message });
    }
  }
});

/**
 * GET /api/videos/:gameFolder/annotations?video=...
 * Load annotations for the logged-in user.
 * Load user-specific annotation file, or start blank.
 */
app.get('/api/videos/:gameFolder/annotations', requireAuth, async (req, res) => {
  try {
    const username = getSessionUser(req)!;
    const user = findUser(username)!;
    const { gameFolder } = req.params;
    const videoFile = req.query.video as string;

    if (!videoFile) {
      return res.status(400).json({ error: 'video query param required' });
    }

    // Check access
    const gameId = extractGameId(gameFolder);
    if (!isGameAllowed(user, gameId)) {
      return res.status(403).json({ error: 'Access denied to this game' });
    }

    // Only load user-specific annotation file — no fallbacks
    const userPath = paths.userAnnotationPath(gameFolder, videoFile, username);
    const [userExists] = await bucket.file(userPath).exists();
    if (userExists) {
      const [content] = await bucket.file(userPath).download();
      return res.json({ annotations: JSON.parse(content.toString()), source: userPath });
    }

    // Nothing found — start blank
    res.json({ annotations: null, source: null });
  } catch (err: any) {
    console.error('Error loading annotations:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * PUT /api/videos/:gameFolder/annotations
 * Save annotations for the logged-in user.
 * Body: { video, data }
 */
app.put('/api/videos/:gameFolder/annotations', requireAuth, async (req, res) => {
  try {
    const username = getSessionUser(req)!;
    const user = findUser(username)!;
    const { gameFolder } = req.params;
    const { video, data } = req.body;

    if (!video || !data) {
      return res.status(400).json({ error: 'video and data are required' });
    }

    // Check access
    const gameId = extractGameId(gameFolder);
    if (!isGameAllowed(user, gameId)) {
      return res.status(403).json({ error: 'Access denied to this game' });
    }

    // Always save to user-specific file
    const filePath = paths.userAnnotationPath(gameFolder, video, username);
    await bucket.file(filePath).save(JSON.stringify(data, null, 4), {
      contentType: 'application/json',
    });

    res.json({ saved: filePath });
  } catch (err: any) {
    console.error('Error saving annotations:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// STATIC FILES (production only)
// ==========================================

if (IS_PROD) {
  const publicDir = join(__dirname, '..', 'public');
  app.use(express.static(publicDir));
  // SPA fallback — serve index.html for any non-API route
  app.get('*', (_req, res) => {
    res.sendFile(join(publicDir, 'index.html'));
  });
}

// ==========================================
// START
// ==========================================

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT} (${IS_PROD ? 'production' : 'development'})`);
  console.log(`Bucket: ${BUCKET}`);
  if (!IS_PROD) console.log(`CORS origin: ${FRONTEND_URL}`);
});

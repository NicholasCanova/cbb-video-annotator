import { createHash } from 'crypto';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface UserConfig {
  username: string;
  passwordHash: string;
  allowedGameIds: number[];
}

let users: UserConfig[] = [];

export function loadUsers() {
  // In production, users.json is one level up from dist/
  const candidates = [
    join(__dirname, 'users.json'),
    join(__dirname, '..', 'users.json'),
  ];
  const filePath = candidates.find((p) => {
    try { readFileSync(p); return true; } catch { return false; }
  });
  if (!filePath) throw new Error('users.json not found');
  const raw = readFileSync(filePath, 'utf-8');
  users = JSON.parse(raw);
  console.log(`Loaded ${users.length} users`);
}

export function findUser(username: string): UserConfig | undefined {
  return users.find((u) => u.username === username);
}

export function verifyPassword(user: UserConfig, password: string): boolean {
  const hash = createHash('sha256').update(password).digest('hex');
  return hash === user.passwordHash;
}

export function isGameAllowed(user: UserConfig, gameId: number): boolean {
  // Empty array = all games allowed
  if (user.allowedGameIds.length === 0) return true;
  return user.allowedGameIds.includes(gameId);
}

/**
 * Extract gameId from a game folder name or video filename.
 * Handles patterns like "game1", "video-2427661.mp4", folder names, etc.
 * Returns the numeric portion if found, or -1 to allow access by default.
 */
export function extractGameId(input: string): number {
  const match = input.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : -1;
}

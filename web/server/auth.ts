import { Request, Response, NextFunction } from 'express';

// Augment express-session with our user field
declare module 'express-session' {
  interface SessionData {
    username?: string;
  }
}

/**
 * Middleware: require authenticated session.
 * Sends 401 if not logged in.
 */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.session?.username) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  next();
}

/**
 * Get the logged-in username from the session.
 */
export function getSessionUser(req: Request): string | undefined {
  return req.session?.username;
}

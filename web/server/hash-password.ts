/**
 * Utility to hash a password for users.json
 * Usage: npx tsx hash-password.ts <password>
 */
import { createHash } from 'crypto';

const password = process.argv[2];
if (!password) {
  console.error('Usage: npx tsx hash-password.ts <password>');
  process.exit(1);
}

const hash = createHash('sha256').update(password).digest('hex');
console.log(hash);

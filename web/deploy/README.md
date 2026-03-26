# Deploying CBB Video Annotator Web

## Architecture

React frontend + Express backend → Docker (Node.js) → Cloud Run

The Express server handles:
- User auth (session cookies, hashed passwords in `server/users.json`)
- GCS video streaming (proxied through the server with range request support)
- Annotation load/save (per-user JSON files in GCS)
- Serving the built React frontend in production

## Prerequisites

- `gcloud` CLI installed and authenticated
- Access to the `cbbanalytics` GCP project
- The Cloud Run service account needs `Storage Object Admin` on `gs://cbb-tracking`

## Deploy

From the `web/` directory:

```bash
./deploy/deploy.sh
```

This submits to Cloud Build, which:
1. Builds the React frontend (Vite)
2. Builds the Express server (TypeScript)
3. Packages both into a single Docker image
4. Pushes to `gcr.io/cbbanalytics/cbb-images/video-annotator`
5. Deploys to Cloud Run (`video-annotator` service, `us-west1`)

## Local Development

```bash
# Terminal 1: backend
cd web/server
gcloud auth application-default login  # one-time setup
npm run dev

# Terminal 2: frontend
cd web
npm run dev
```

Frontend: `http://localhost:5173`
Backend: `http://localhost:3001`

## Managing Users

Users are stored in `server/users.json` with SHA-256 hashed passwords.

To hash a new password:
```bash
cd server && npx tsx hash-password.ts <password>
```

Add the hash to `users.json`, then redeploy.

## Cloud Run Config

- **Service**: `video-annotator`
- **Region**: `us-west1`
- **Memory**: 1Gi (video streaming)
- **CPU**: 1
- **Scaling**: 0-2 instances
- **Auth**: Public URL, app-level auth via session cookies

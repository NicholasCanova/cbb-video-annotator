# CBB Video Annotator — Web

Browser-based basketball video annotation tool. Replaces the previous PyQt5 desktop app that was delivered via Compute Engine + Chrome Remote Desktop.

## Stack

- **Frontend**: React + TypeScript + Vite + Mantine + Zustand
- **Backend**: Express + TypeScript + @google-cloud/storage
- **Deploy**: Docker + Cloud Run (`us-west1`)
- **Storage**: GCS (`gs://cbb-tracking/video/video-annotation-tasks/`)

## Local Development

```bash
# Terminal 1: backend (requires GCS credentials)
cd server
npm install
npm run dev

# Terminal 2: frontend
npm install
npm run dev
```

Frontend: http://localhost:5173 | Backend: http://localhost:3001

First-time GCS setup: `gcloud auth application-default login`

## Deploy to Cloud Run

```bash
./deploy/deploy.sh
```

See `deploy/README.md` for full details.

## Key Directories

```
web/
├── src/                  # React frontend
│   ├── components/       # UI components (video, annotations, layout, common)
│   ├── stores/           # Zustand state (video, annotations, UI, auth, session)
│   ├── hooks/            # Custom hooks (hotkeys, frame sync, autosave, pause-at-events)
│   ├── lib/              # Utilities (api client, frame math, hotkey map, save logic)
│   └── types/            # TypeScript interfaces
├── server/               # Express backend (auth, GCS proxy, annotation CRUD)
├── deploy/               # Dockerfile, Cloud Build config, deploy script
└── public/               # Static assets (classes.json action config)
```

## Users

Managed via `server/users.json` (hashed passwords). See `deploy/README.md` for instructions.

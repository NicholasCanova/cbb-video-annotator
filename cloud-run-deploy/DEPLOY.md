# Deploying to GCP Cloud Run

Taggers access the annotation tool through a browser URL via noVNC. Videos and annotation JSON
files live in a GCS bucket (`cbb-tracking`), mounted as `/videos` inside the container.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) authenticated (`gcloud auth login`)
- GCP project `cbbanalytics` with Cloud Run, Container Registry, and Cloud Storage APIs enabled

---

## 1. Set up GCS bucket (one-time)

```bash
gsutil mb gs://cbb-tracking

# Upload videos — organize by game/folder
gsutil cp /path/to/local/1.mp4 gs://cbb-tracking/game1/1.mp4
gsutil cp /path/to/local/Labels-v2.json gs://cbb-tracking/game1/Labels-v2.json
```

The app expects each video to have a matching `Labels-v2.json` in the same folder.
See `Annotation/example_video/Labels-v2.json` for the format.

---

## 2. Build the Docker image

```bash
docker build --platform linux/amd64 -f cloud-run-deploy/Dockerfile -t gcr.io/cbbanalytics/cbb-images/video-annotator .
```

All commands run from the project root. The `-f` flag points to the Dockerfile inside `cloud-run-deploy/`.

### (Optional) Test locally

```bash
docker run --rm --name annotator -p 8080:8080 gcr.io/cbbanalytics/cbb-images/video-annotator
# Open http://localhost:8080 — confirms the container starts (no GCS mount locally)
```

---

## 3. Push image to Google Container Registry

```bash
# Authenticate Docker with GCR (one-time)
gcloud auth configure-docker

docker push gcr.io/cbbanalytics/cbb-images/video-annotator
```

---

## 4. Deploy to Cloud Run

```bash
gcloud run services replace cloud-run-deploy/cloud-run.yaml --region=us-west1
```

The Cloud Run service config is in `cloud-run-deploy/cloud-run.yaml` (2 vCPU, 4 GiB, 1 tagger per instance, GCS FUSE mount, gen2 execution).

---

## 5. One-time setup (service account permissions)

These only need to be run once when first setting up the service, not on every deploy.

### Grant GCS access to the Cloud Run service account

```bash
# Get your project number
gcloud projects describe cbbanalytics --format="value(projectNumber)"

# Grant access (replace PROJECT_NUMBER)
gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectAdmin gs://cbb-tracking
```

### Grant your user permission to act as the service account

```bash
# Also available as cloud-run-deploy/grant-sa-permission.sh
gcloud iam service-accounts add-iam-policy-binding \
  cbb-compute@cbbanalytics.iam.gserviceaccount.com \
  --member="user:nick@cbbanalytics.com" \
  --role="roles/iam.serviceAccountUser"
```

### (Optional) Allow unauthenticated access

```bash
gcloud run services add-iam-policy-binding cbb-video-annotator \
  --region=us-west1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

---

## 6. Share with taggers

```bash
# Get the service URL
gcloud run services describe cbb-video-annotator --region=us-west1 --format="value(status.url)"
```

Give taggers the URL. They open it in a browser and see the annotation tool via noVNC.

To open a video: click **Open video** → navigate to `/videos` → select the game folder → open the `.mp4` file.

---

## Rebuilding after code changes

Just repeat steps 2-4:

```bash
docker build --platform linux/amd64 -f cloud-run-deploy/Dockerfile -t gcr.io/cbbanalytics/cbb-images/video-annotator .
docker push gcr.io/cbbanalytics/cbb-images/video-annotator
gcloud run services replace cloud-run-deploy/cloud-run.yaml --region=us-west1
```

---

## Known limitations

- **VNC lag/framerate**: Cloud Run serves the PyQt5 app via noVNC (VNC in the browser). Because VNC encodes every pixel change as images over the network, video playback is inherently choppy — especially for a video annotation tool. There is no GPU or hardware acceleration in Cloud Run containers. For better performance, consider Compute Engine VMs with Chrome Remote Desktop.
- **60-minute session timeout**: Cloud Run kills WebSocket connections after 1 hour max. noVNC will auto-reconnect, but taggers should save work frequently. Unsaved annotations are lost if the container shuts down.

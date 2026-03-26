#!/bin/bash
set -euo pipefail

# Deploy CBB Video Annotator Web to Cloud Run
#
# Usage:
#   cd web
#   ./deploy/deploy.sh
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - Docker installed (for local builds) OR use Cloud Build

PROJECT_ID="${GCP_PROJECT:-cbbanalytics}"
REGION="${GCP_REGION:-us-west1}"
SERVICE_NAME="video-annotator"
IMAGE="gcr.io/${PROJECT_ID}/cbb-images/video-annotator"

echo "=== Building and deploying ${SERVICE_NAME} ==="
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"
echo ""

# Option 1: Cloud Build (recommended — builds in the cloud)
echo "Submitting build to Cloud Build..."
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=deploy/cloudbuild.yaml \
  .

echo ""
echo "=== Deploy complete ==="
echo "Service URL:"
gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)'

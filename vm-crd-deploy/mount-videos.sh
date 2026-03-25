#!/usr/bin/env bash
set -euo pipefail

# Mount the annotation bucket onto the VM at /videos using gcsfuse.
# This is meant for the CRD VM host, not for inside the app container.
# The VM should already have a service account attached with bucket access,
# and vm-bootstrap-crd.sh should have installed gcsfuse ahead of time.

GCS_BUCKET="${GCS_BUCKET:-cbb-tracking}"
VIDEOS_MOUNT="${VIDEOS_MOUNT:-/videos}"

if ! command -v gcsfuse >/dev/null 2>&1; then
  echo "gcsfuse is not installed. Run vm-crd-deploy/vm-bootstrap-crd.sh first."
  exit 1
fi

mkdir -p "${VIDEOS_MOUNT}"

if mount | grep -q "on ${VIDEOS_MOUNT} "; then
  echo "${VIDEOS_MOUNT} is already mounted."
  exit 0
fi

echo "This script mounts the GCS bucket onto the VM so the annotator can access videos at ${VIDEOS_MOUNT}."
echo "Mounting gs://${GCS_BUCKET} at ${VIDEOS_MOUNT}"
sudo gcsfuse -o allow_other --only-dir video/video-annotation-tasks "${GCS_BUCKET}" "${VIDEOS_MOUNT}"

echo "Mount complete."

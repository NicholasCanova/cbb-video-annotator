#!/usr/bin/env bash
set -euo pipefail

# Launch the annotator Docker container against the VM's active X display.
# This is meant to be run on the CRD VM host after the bucket is mounted and
# after the Docker image has already been built from vm-crd-deploy/Dockerfile.
# The mounted /videos path is passed through so the app can open GCS-backed files.

IMAGE_NAME="${IMAGE_NAME:-cbb-video-annotator}"
VIDEOS_MOUNT="${VIDEOS_MOUNT:-/videos}"
TAGGER_NAME="${TAGGER_NAME:-nick}"

if [[ ! -S /tmp/.X11-unix/X0 && -z "${DISPLAY:-}" ]]; then
  echo "No X display detected. Start a CRD session first, then rerun this script."
  exit 1
fi

DISPLAY_VALUE="${DISPLAY:-:0}"

echo "This script starts the annotator container on the VM's current desktop session."
echo "Allowing local Docker access to the X server"
xhost +local:docker

echo "Starting ${IMAGE_NAME}"
docker run --rm \
  -e DISPLAY="${DISPLAY_VALUE}" \
  -e TAGGER_NAME="${TAGGER_NAME}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${HOME}/.Xauthority:/root/.Xauthority:ro" \
  -v "${VIDEOS_MOUNT}:${VIDEOS_MOUNT}" \
  "${IMAGE_NAME}"

#!/usr/bin/env bash
set -euo pipefail

# Launch the annotator Docker container against the VM's active X display.
# This is meant to be run on the CRD VM host after the bucket is mounted and
# after the Docker image has already been built from vm-crd-deploy/Dockerfile.
# The mounted /videos path is passed through so the app can open GCS-backed files.

IMAGE_NAME="${IMAGE_NAME:-cbb-video-annotator}"
VIDEOS_MOUNT="${VIDEOS_MOUNT:-/videos}"
TAGGER_NAME="${TAGGER_NAME:-nick}"

# CRD typically uses :20; fall back to :0 for local displays
if [[ -S /tmp/.X11-unix/X20 ]]; then
  DISPLAY_VALUE="${DISPLAY:-:20}"
elif [[ -S /tmp/.X11-unix/X0 ]]; then
  DISPLAY_VALUE="${DISPLAY:-:0}"
elif [[ -n "${DISPLAY:-}" ]]; then
  DISPLAY_VALUE="${DISPLAY}"
else
  echo "No X display detected. Start a CRD session first, then rerun this script."
  exit 1
fi

echo "This script starts the annotator container on the VM's current desktop session."
echo "Allowing local Docker access to the X server"
xhost +local:docker

echo "Starting ${IMAGE_NAME}"
docker run --rm \
  -e DISPLAY="${DISPLAY_VALUE}" \
  -e TAGGER_NAME="${TAGGER_NAME}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "${HOME}/.Xauthority:/root/.Xauthority:ro" \
  --mount type=bind,source="${VIDEOS_MOUNT}",target="${VIDEOS_MOUNT}" \
  "${IMAGE_NAME}"

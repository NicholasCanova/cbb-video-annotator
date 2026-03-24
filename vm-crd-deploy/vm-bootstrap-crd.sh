#!/usr/bin/env bash
set -euo pipefail

# Host bootstrap for a Compute Engine VM that will run cbb-video-annotator
# through Chrome Remote Desktop, with the app itself running in Docker.
#
# Run as a sudo-capable user on a fresh Debian/Ubuntu VM.

GCS_BUCKET="${GCS_BUCKET:-cbb-tracking}"
VIDEOS_MOUNT="${VIDEOS_MOUNT:-/videos}"

echo "==> Updating apt metadata"
sudo apt-get update

echo "==> Installing host packages"
sudo DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes \
  curl \
  wget \
  gnupg \
  ca-certificates \
  lsb-release \
  software-properties-common \
  dbus-x11 \
  xscreensaver \
  xfce4 \
  desktop-base \
  docker.io \
  docker-compose-plugin \
  git

echo "==> Enabling Docker"
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo "==> Installing Chrome Remote Desktop"
curl https://dl.google.com/linux/linux_signing_key.pub \
  | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/chrome-remote-desktop.gpg
echo "deb [arch=amd64] https://dl.google.com/linux/chrome-remote-desktop/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/chrome-remote-desktop.list >/dev/null
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes chrome-remote-desktop

echo "==> Configuring CRD to use Xfce"
echo "exec /etc/X11/Xsession /usr/bin/xfce4-session" \
  | sudo tee /etc/chrome-remote-desktop-session >/dev/null
sudo systemctl disable lightdm.service 2>/dev/null || true

echo "==> Installing gcsfuse"
export GCSFUSE_REPO="gcsfuse-$(lsb_release -c -s)"
echo "deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt ${GCSFUSE_REPO} main" \
  | sudo tee /etc/apt/sources.list.d/gcsfuse.list >/dev/null
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null
sudo apt-get update
sudo apt-get install --assume-yes gcsfuse

echo "==> Preparing mountpoint"
sudo mkdir -p "${VIDEOS_MOUNT}"
sudo chown "$USER":"$USER" "${VIDEOS_MOUNT}"

echo "==> Host bootstrap complete"
cat <<EOF

Next manual steps:

1. Re-login or run this once so Docker group membership applies:
   newgrp docker

2. Authorize Chrome Remote Desktop:
   https://remotedesktop.google.com/access

3. Mount the bucket once for testing:
   gcsfuse ${GCS_BUCKET} ${VIDEOS_MOUNT}

4. Build the app image from the repo root:
   docker build -f vm-crd-deploy/Dockerfile -t cbb-video-annotator .

5. Start the app against the host display:
   xhost +local:docker
   docker run --rm \\
     -e DISPLAY=\$DISPLAY \\
     -e TAGGER_NAME=nick \\
     -v /tmp/.X11-unix:/tmp/.X11-unix \\
     -v \$HOME/.Xauthority:/root/.Xauthority:ro \\
     -v ${VIDEOS_MOUNT}:${VIDEOS_MOUNT} \\
     cbb-video-annotator

EOF

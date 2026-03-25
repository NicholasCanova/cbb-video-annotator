# VM + CRD Deploy

This folder contains the files needed to run `cbb-video-annotator` on a Compute Engine VM through Chrome Remote Desktop, with the app itself running in Docker.

## Files

- `vm-bootstrap-crd.sh`: installs host-level VM dependencies like CRD, Xfce, Docker, and `gcsfuse`
- `Dockerfile`: builds the app container with Python, PyQt, and multimedia dependencies
- `run-annotator.sh`: launches the app container against the host display
- `mount-videos.sh`: mounts the GCS bucket to `/videos`
- `vm-instance-details.txt`: suggested VM settings for the first pilot
- `iam-setup.txt`: suggested IAM/service account setup for the VM

## Suggested Flow

1. Create the VM using the notes in `vm-instance-details.txt`.
2. Make sure the VM uses the service account described in `iam-setup.txt`.
3. Copy the bootstrap script from locally to the VM (git is not yet installed on a fresh VM). Run from local terminal inside of cbb-video-annotator:

```bash
gcloud compute scp vm-crd-deploy/vm-bootstrap-crd.sh nick@cbb-annotator-vm:~ --zone=us-west1-b --project=cbbanalytics
```

4. SSH into the VM (typically use the GCP Compute Engine UI):

```bash
gcloud compute ssh cbb-annotator-vm --zone=us-west1-b --project=cbbanalytics
```

5. Run the bootstrap.:
Run from anywhere on the VM. The script uses absolute paths and sudo.

```bash
chmod +x ~/vm-bootstrap-crd.sh
~/vm-bootstrap-crd.sh
newgrp docker
```

6. Verify the bootstrap installed everything:

```bash
docker --version                         # Docker CE
dpkg -l | grep chrome-remote-desktop     # CRD
which gcsfuse                            # gcsfuse
git --version                            # git
```

All four should return a version or path. If any are missing, re-run the bootstrap script.

7. Authorize Chrome Remote Desktop:

   - Open https://remotedesktop.google.com/headless in your browser
   - Click **"Set up via SSH"** in the left sidebar (should already be selected)
   - Click **"Begin"**, then **"Next"**
   - Click **"Authorize"** and sign in with your Google account. ENSURE CORRECT GOOGLE ACCOUNT.
   - Select **"Debian Linux"** and copy the command it gives you
   - Paste that command into your VM SSH session and hit Enter
   - Set a 6-digit PIN when prompted (this is your CRD login PIN)
   - Verify: go to https://remotedesktop.google.com/access — your VM should appear as online

8. Set up an SSH key for GitHub on the VM:

```bash
ssh-keygen -t ed25519 -C "nick@cbbanalytics.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Copy the output and add it to GitHub: **Account Settings → SSH and GPG keys → New SSH key** (Authentication Key).

9. Clone the repo on the VM:

```bash
git clone git@github.com:NicholasCanova/cbb-video-annotator.git ~/cbb-video-annotator
cd ~/cbb-video-annotator
chmod +x vm-crd-deploy/*.sh
```

10. Mount the bucket:

```bash
./vm-crd-deploy/mount-videos.sh
```

11. Build the app image from the repo root:

```bash
docker build -f vm-crd-deploy/Dockerfile -t cbb-video-annotator .
```

12. Connect to the VM via Chrome Remote Desktop and launch the app:

   - Go to https://remotedesktop.google.com/access
   - ENSURE you are on the right user - nick@cbbanalytics.com
   - Click on `cbb-annotator-vm` and enter your PIN
   - You should see the Xfce desktop. Cancel any "Authenticate" popups (color management — not needed).
   - Adjust display: click the small blue arrow `>` on the right edge to open the CRD sidebar → **Display** → set resolution to 1920x1080 or higher, enable "Resize to fit"
   - Open a terminal: right-click the desktop → **Terminal Emulator** (or Applications menu → System → Terminal)
   - **Important:** the app must be launched from inside this CRD terminal, not from SSH. The CRD session provides the X display.

```bash
cd ~/cbb-video-annotator
TAGGER_NAME=nick ./vm-crd-deploy/run-annotator.sh
```

## Notes

- For the first pilot, a manual `gcsfuse` mount is fine.
- After the pilot works, consider turning the bucket mount and app launch into `systemd` services.
- The VM needs a service account attached to it. Do not start with a downloaded JSON key unless you have a strong reason to do so.

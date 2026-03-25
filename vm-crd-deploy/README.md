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

6. Complete Chrome Remote Desktop authorization in the browser:

```text
https://remotedesktop.google.com/headless
```

7. Clone the repo on the VM:

```bash
git clone git@github.com:YOUR_USERNAME/cbb-video-annotator.git ~/cbb-video-annotator
cd ~/cbb-video-annotator
chmod +x vm-crd-deploy/*.sh
```

8. Mount the bucket:

```bash
./vm-crd-deploy/mount-videos.sh
```

9. Build the app image from the repo root:

```bash
docker build -f vm-crd-deploy/Dockerfile -t cbb-video-annotator .
```

10. Connect via CRD, open a terminal, and start the annotator:

```bash
cd ~/cbb-video-annotator
TAGGER_NAME=nick ./vm-crd-deploy/run-annotator.sh
```

## Notes

- For the first pilot, a manual `gcsfuse` mount is fine.
- After the pilot works, consider turning the bucket mount and app launch into `systemd` services.
- The VM needs a service account attached to it. Do not start with a downloaded JSON key unless you have a strong reason to do so.

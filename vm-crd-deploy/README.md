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
3. SSH into the VM and run:

```bash
chmod +x vm-crd-deploy/*.sh
./vm-crd-deploy/vm-bootstrap-crd.sh
```

4. Complete Chrome Remote Desktop authorization in the browser:

```text
https://remotedesktop.google.com/access
```

5. Mount the bucket:

```bash
./vm-crd-deploy/mount-videos.sh
```

6. Build the app image from the repo root:

```bash
docker build -f vm-crd-deploy/Dockerfile -t cbb-video-annotator .
```

7. Start the annotator:

```bash
TAGGER_NAME=nick ./vm-crd-deploy/run-annotator.sh
```

## Notes

- For the first pilot, a manual `gcsfuse` mount is fine.
- After the pilot works, consider turning the bucket mount and app launch into `systemd` services.
- The VM needs a service account attached to it. Do not start with a downloaded JSON key unless you have a strong reason to do so.

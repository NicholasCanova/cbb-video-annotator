# Deployment Plan for `cbb-video-annotator`

## Current Process

Today the tool runs on **Cloud Run + noVNC + Xvfb**:

- the PyQt5 app starts inside a container
- the GUI is exposed through VNC in the browser
- videos are mounted from GCS at `/videos`

This works for basic access, but it is a poor fit for video annotation:

- VNC is too laggy for video playback and frame-accurate tagging
- Cloud Run has a 60-minute request/session limit
- the app keeps working state in `/tmp` during a session, so disconnects are risky until saved

We are **not** converting this tool into a web app. The goal is to keep the native Python/PyQt5 app and change how it is delivered.

## Recommended Path Now

Use **Compute Engine + Chrome Remote Desktop (CRD)**.

This means:

1. We run the annotator on a Linux VM instead of Cloud Run.
2. The tagger connects to that VM through Chrome Remote Desktop.
3. The VM mounts the same GCS bucket used today.
4. The app keeps running on a persistent machine with no 60-minute timeout.

Why this is the current preference:

- keeps the "use a tool on the internet" workflow
- avoids asking taggers to clone the repo or set up Python
- should perform much better than browser VNC for video playback
- works for both Windows and Mac taggers because the app runs on the VM, not on their laptop
- is the fastest path to a realistic pilot

## Proposed Setup

For the first pilot, keep it simple:

- **1 Linux VM**
- Debian or Ubuntu
- lightweight desktop environment
- Python 3.11 + app dependencies
- PyQt5 / Qt multimedia dependencies
- Chrome Remote Desktop
- gcsfuse mount for the annotation bucket

Suggested shape:

- machine type: start around `e2-standard-2`
- one VM per active tagger if this scales out
- persistent disk attached to each VM
- no MIG at first

`MIG` means **Managed Instance Group**: a fleet of identical VMs created from one template. That is useful later for scale, but it is not the right first move for named human workstations.

## App Changes We Should Make

Before wider rollout, add lightweight autosave.

Current behavior:

- annotation work is written to a local temp file first
- the file is copied to mounted storage when the user saves to GCS

We should change that to:

- autosave locally after every few annotations or every N seconds
- copy to mounted storage on a timer and on explicit save
- also save on app close when possible

This is a small change and matters regardless of whether we use CRD, RDP, or local packaging.

## Pilot Plan

1. Build one Linux VM with the app, CRD, and bucket mount.
2. Have our developer test:
   - video playback smoothness
   - frame stepping responsiveness
   - keyboard shortcut reliability
   - reconnect behavior
   - autosave / recovery behavior
3. If the pilot is good, turn that VM into an image and create one VM per tagger.

## Backup Options If CRD Fails

### 1. Compute Engine + xrdp / RDP

This is the first backup option.

Use a Linux VM again, but expose it through RDP instead of CRD. This is worth testing if:

- CRD video quality is not good enough
- keyboard handling feels off
- we want a more traditional remote desktop stack

Tradeoffs:

- setup is more involved than CRD
- client experience is less universal than CRD
- still a much better fit than Cloud Run + VNC

### 2. Local Packaged Desktop App

If hosted remote desktop is still not good enough, package the app as a real desktop install.

This would likely mean:

- a Windows build
- a macOS build
- synced access to videos / annotations through cloud storage

Pros:

- best performance and lowest latency
- no remote desktop artifacts

Cons:

- installers, updates, and support for two OSes
- more operational overhead for distribution

We are **not** choosing this first because hosted access is easier for onboarding, but it remains the strongest fallback if remote desktop quality is still not acceptable.

### 3. Managed Instance Group Later

Only consider a `MIG` after the single-VM CRD approach is proven.

That is a scaling mechanism, not the first deployment decision.

## Not Recommended

- **Cloud Run + noVNC**: current approach; too laggy and session-limited
- **Cloud Workstations**: likely more expensive than needed and unclear for video-heavy GUI use

## Decision

Current plan:

1. move off Cloud Run
2. pilot **Compute Engine + Chrome Remote Desktop**
3. add autosave
4. fall back to **xrdp/RDP** if CRD is not good enough
5. only consider a packaged local desktop app if remote desktop still fails

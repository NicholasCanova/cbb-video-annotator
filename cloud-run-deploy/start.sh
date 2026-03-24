#!/bin/bash
set -e

export DISPLAY=:1

# Start virtual framebuffer display
Xvfb :1 -screen 0 1920x1080x24 -ac &
sleep 1

# Start VNC server (localhost only — noVNC proxies it externally)
if [ -n "$VNC_PASSWORD" ]; then
    x11vnc -display :1 -passwd "$VNC_PASSWORD" -listen localhost -xkb -forever -shared -quiet &
else
    x11vnc -display :1 -nopw -listen localhost -xkb -forever -shared -quiet &
fi
sleep 1

# Start window manager (so Qt windows are visible and movable)
fluxbox >/dev/null 2>&1 &
sleep 1

# Start noVNC websocket proxy + web UI on $PORT (Cloud Run sets this to 8080)
PORT=${PORT:-8080}
websockify --web /usr/share/novnc ${PORT} localhost:5900 &

# Launch the annotation app (container lives as long as this process runs)
cd /app/Annotation/src
exec python main.py

FROM --platform=linux/amd64 python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Virtual display
    xvfb \
    # VNC server
    x11vnc \
    # noVNC browser client + websocket proxy
    novnc \
    websockify \
    # Qt system libraries (needed by pip-installed PyQt5)
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    # GStreamer — required by Qt QMediaPlayer for video playback on Linux
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    gstreamer1.0-x \
    gstreamer1.0-gl \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    # PulseAudio (needed by Qt multimedia)
    libpulse-mainloop-glib0 \
    # Lightweight window manager (needed to display Qt windows)
    fluxbox \
    # Fonts
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Redirect root URL to noVNC with auto-connect and scaling
RUN echo '<html><head><meta http-equiv="refresh" content="0;url=/vnc.html?resize=scale&autoconnect=true"></head></html>' > /usr/share/novnc/index.html

# Configure fluxbox: hide toolbar, no decorations, no auto-maximize
RUN mkdir -p /root/.fluxbox && \
    echo 'session.screen0.toolbar.visible: false' > /root/.fluxbox/init && \
    printf '[app] (.*)\n  [Deco] {NONE}\n[end]\n' > /root/.fluxbox/apps

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Annotation/ /app/Annotation/

COPY cloud-run-deploy/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080

CMD ["/start.sh"]

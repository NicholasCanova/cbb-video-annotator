# Adapted from https://codeloop.org/python-how-to-create-media-player-in-pyqt5/
import os
from bisect import bisect_left

import cv2

from PyQt5.QtWidgets import QWidget, QPushButton, QStyle, QSlider, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaMetaData
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QEvent
from utils.event_class import ms_to_time

class MediaPlayer(QWidget):

	def __init__(self, main_window):

		# Defining the elements of the media player
		super().__init__()

		self.main_window = main_window

		# Media Player
		self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
		self.media_player.setNotifyInterval(33)

		# Video Widget
		self.video_widget = QVideoWidget()
		
		# Create container widget for video with overlay
		self.video_container = QWidget()
		video_container_layout = QVBoxLayout()
		video_container_layout.setContentsMargins(0, 0, 0, 0)
		video_container_layout.addWidget(self.video_widget)
		self.video_container.setLayout(video_container_layout)
		
		# Create overlay label for displaying position and editing mode
		self.overlay_label = QLabel(self.video_container)
		# Initial stylesheet (black background, will be updated dynamically)
		self.overlay_label.setStyleSheet("""
			QLabel {
				background-color: rgba(0, 0, 0, 180);
				color: white;
				padding: 8px 12px;
				font-size: 16px;
				font-weight: bold;
				border-radius: 4px;
			}
		""")
		self.overlay_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.overlay_label.setText("00:00")
		self.overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Allow clicks to pass through
		self.overlay_label.raise_()  # Raise above video widget
		self.overlay_label.hide()  # Hide until video is loaded

		self._pass_label_x = 150

		# Label for showing current event info (top-right)
		self.event_overlay = QLabel(self.video_container)
		self.event_overlay.setStyleSheet("""
			QLabel {
				background-color: rgba(0, 0, 0, 180);
				color: white;
				padding: 8px 12px;
				font-size: 16px;
				font-weight: bold;
				border-radius: 4px;
			}
		""")
		self.event_overlay.setAlignment(Qt.AlignRight | Qt.AlignTop)
		self.event_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
		self.event_overlay.raise_()
		self.event_overlay.hide()

		self.pass_label = QLabel(self.video_container)
		self.pass_label.setStyleSheet("""
			QLabel {
				background-color: rgba(0, 0, 0, 120);
				color: white;
				padding: 6px 10px;
				font-size: 14px;
				border-radius: 4px;
			}
		""")
		self.pass_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.pass_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
		self.pass_label.raise_()
		self.pass_label.hide()

		self.pause_at_events = False
		self.pause_at_event_frames = []
		self._next_pause_index = 0
		self._last_position_frame = 0
		self._pause_event_source = None

		self.video_container.installEventFilter(self)

		# Button to open a new file
		self.open_file_button = QPushButton('Open video')
		self.open_file_button.clicked.connect(self.open_file)

		# Button for playing the video
		self.play_button = QPushButton()
		self.play_button.setEnabled(False)
		self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.play_button.clicked.connect(self.play_video)

		# Button for the slider
		self.slider = QSlider(Qt.Horizontal)
		self.slider.setRange(0,0)
		self.slider.sliderMoved.connect(self.set_position)
		self.slider.sliderReleased.connect(self._slider_released)

		self.pause_at_events_button = QPushButton("Pause At Tags")
		self.pause_at_events_button.setCheckable(True)
		self.pause_at_events_button.toggled.connect(self._set_pause_at_events)

		#create hbox layout
		hboxLayout = QHBoxLayout()
		hboxLayout.setContentsMargins(0,0,0,0)

		#set widgets to the hbox layout
		hboxLayout.addWidget(self.open_file_button)
		hboxLayout.addWidget(self.play_button)
		hboxLayout.addWidget(self.pause_at_events_button)
		hboxLayout.addWidget(self.slider)

		#create vbox layout
		self.layout = QVBoxLayout()
		self.layout.addWidget(self.video_container)
		self.layout.addLayout(hboxLayout)

		self.media_player.setVideoOutput(self.video_widget)

		# Media player signals
		self.media_player.stateChanged.connect(self.mediastate_changed)
		self.media_player.positionChanged.connect(self.position_changed)
		self.media_player.durationChanged.connect(self.duration_changed)
		self.media_player.metaDataChanged.connect(self._update_video_metadata)

		self.path_label = None

	def open_file(self):
		filename, _ = QFileDialog.getOpenFileName(self, "Open Video")

		if filename != '':
			self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
			self.play_button.setEnabled(True)
			fps = self._read_video_frame_rate(filename)
			if fps:
				self.main_window.set_frame_rate(fps)
			self.overlay_label.show() 
			self.update_overlay()
			filpath = os.path.basename(filename)
			self.main_window.half = int(filpath[0])

			self.path_label = os.path.dirname(filename) + "/Labels.json"
			self.path_label = self.get_last_label_file()
			self.main_window.list_manager.create_list_from_json(self.path_label, self.main_window.half)
			self.main_window.list_display.display_list()

	def get_last_label_file(self):
		path_label = self.path_label
		folder_label = os.path.dirname(path_label)
		if os.path.isfile(folder_label + "/Labels-v2.json"):
			return folder_label + "/Labels-v2.json"
		else:
			return path_label

	def play_video(self):
		if self.media_player.state() == QMediaPlayer.PlayingState:
			self.media_player.pause()

		else:
			if getattr(self.main_window, "list_display", None):
				self.main_window.list_display.list_widget.setCurrentRow(-1)
			self.media_player.play()
			self.media_player.play()

	def mediastate_changed(self, state):
		if self.media_player.state() == QMediaPlayer.PlayingState:
			self.play_button.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPause)

			)

		else:
			self.play_button.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPlay)

			)

	def position_changed(self, position):
		self.slider.setValue(position)
		frame_number = self.update_overlay()
		if self.pause_at_events:
			if frame_number < self._last_position_frame:
				self._refresh_pause_queue(current_frame=frame_number)
			self._maybe_pause_for_event(frame_number)
		self._last_position_frame = frame_number

	def duration_changed(self, duration):
		self.slider.setRange(0, duration)

	def set_position(self, position):
		self.media_player.setPosition(position)
	
	def _slider_released(self):
		self.set_position(self.slider.value())
	
	def update_overlay(self):
		"""Update the overlay label with current position and editing mode"""
		position = self.media_player.position()
		# Convert milliseconds to frame number
		frame_number = int(round(position / self.main_window.frame_duration_ms))
		frame_str = f"Frame: {frame_number}"
		
		# Check if we're in editing mode
		if self.main_window.editing_event and self.main_window.edit_event_obj:
			event_label = self.main_window.edit_event_obj.label if self.main_window.edit_event_obj.label else 'Unknown Event'
			overlay_text = f"EDITING: {event_label}\nNew {frame_str}"
			bg_color = "rgba(255, 0, 0, 180)" # red
		else:
			overlay_text = frame_str
			bg_color = "rgba(0, 0, 0, 180)" # black
		
		# Update stylesheet with appropriate background color
		self.overlay_label.setStyleSheet(f"""
			QLabel {{
				background-color: {bg_color};
				color: white;
				padding: 8px 12px;
				font-size: 16px;
				font-weight: bold;
				border-radius: 4px;
			}}
		""")
		
		self.overlay_label.setText(overlay_text)
		
		# Resize and position overlay label
		self.overlay_label.adjustSize()
		self.overlay_label.raise_()  # Ensure it's on top
		self._update_passing_events(frame_number)
		self._position_pass_label()
		return frame_number

	def display_event_info(self, event):
		if not event:
			self.event_overlay.hide()
			return

		label = event.label or "Unknown Event"
		frame = getattr(event, "frame", "?")
		position = getattr(event, "position", None)
		if position is None:
			time_str = event.time or "00:00"
		else:
			time_str = ms_to_time(position)

		parts = [label]
		if event.subType and not event.subType == "None":
			parts.append(event.subType)
		parts.append(f"{time_str} | Frame: {frame}")
		self.event_overlay.setText(" · ".join(parts))
		self.event_overlay.adjustSize()
		self.event_overlay.raise_()
		self.event_overlay.show()
		self._position_event_overlay()
		frame_number = None
		frame_number = int(getattr(event, "frame", None))
		if frame_number is not None:
			self._update_passing_events(frame_number)
		self._position_pass_label()
		return frame_number

	def _update_passing_events(self, current_frame):
		if self.main_window.editing_event or (
			getattr(self.main_window, "list_display", None)
			and getattr(self.main_window.list_display, "_playing_clips", False)
		):
			self.pass_label.hide()
			return

		if not getattr(self.main_window, "list_manager", None):
			self.pass_label.hide()
			return

		frame_duration = self.main_window.frame_duration_ms if self.main_window.frame_duration_ms else 40.0
		frames_visible = max(1, int(round(2000.0 / frame_duration)))

		events = []
		for event in sorted(self.main_window.list_manager.event_list, key=lambda e: getattr(e, "frame", float("inf"))):
			event_frame = getattr(event, "frame", None)
			if event_frame is None:
				continue

			if current_frame >= event_frame and current_frame < event_frame + frames_visible:
				events.append(f"{event.label or 'Event'} ({event_frame})")

		if not events:
			self.pass_label.hide()
			return

		self.pass_label.setText(" | ".join(events))
		self.pass_label.adjustSize()
		self.pass_label.show()
		self._position_pass_label()

	def _position_pass_label(self):
		if not self.pass_label.isVisible():
			return

		x = self.overlay_label.x() + self._pass_label_x
		y = self.overlay_label.y()
		self.pass_label.move(x, y)

	def _maybe_pause_for_event(self, current_frame):
		if (
			not self.pause_at_events
			or self.media_player.state() != QMediaPlayer.PlayingState
			or not self.pause_at_event_frames
			or self._next_pause_index >= len(self.pause_at_event_frames)
		):
			return

		next_frame = self.pause_at_event_frames[self._next_pause_index]
		if current_frame >= next_frame:
			self.media_player.pause()
			if getattr(self.main_window, "list_display", None):
				self.main_window.list_display.highlight_event_by_frame(next_frame)
			self._next_pause_index += 1

	def _refresh_pause_queue(self, current_frame=None, events=None):
		if events is not None:
			self._pause_event_source = list(events)
		event_source = self._pause_event_source

		if event_source is None:
			manager = getattr(self.main_window, "list_manager", None)
			event_source = manager.event_list if manager else []

		self.pause_at_event_frames = sorted(
			{
				getattr(event, "frame", None)
				for event in (event_source or [])
				if getattr(event, "frame", None) is not None
			}
		)

		if current_frame is None:
			current_frame = self.main_window.position_to_frame(self.media_player.position())

		self._sync_pause_index(current_frame, reset=True)

	def _sync_pause_index(self, frame, reset=False):
		if not self.pause_at_event_frames:
			self._next_pause_index = 0
			return

		target = bisect_left(self.pause_at_event_frames, frame)
		if reset:
			self._next_pause_index = target
		else:
			self._next_pause_index = max(self._next_pause_index, target)

	def refresh_event_pause_queue(self, events=None):
		self._refresh_pause_queue(events=events)

	def _set_pause_at_events(self, enable):
		self.pause_at_events = enable
		if enable:
			current_frame = self.main_window.position_to_frame(self.media_player.position())
			list_display = getattr(self.main_window, "list_display", None)
			filtered_events = getattr(list_display, "_visible_events", None)
			self._refresh_pause_queue(current_frame=current_frame, events=filtered_events)
		else:
			self._next_pause_index = 0

	def _position_event_overlay(self):
		if not self.event_overlay.isVisible():
			return
		margin = 16
		container_width = self.video_container.width()
		x = max(0, container_width - self.event_overlay.width() - margin)
		self.event_overlay.move(x, self.overlay_label.y())

	def eventFilter(self, obj, event):
		if obj is self.video_container and event.type() == QEvent.Resize:
			self._position_event_overlay()
			self._position_pass_label()
		return super().eventFilter(obj, event)

	def handle_errors(self):
		self.play_button.setEnabled(False)
		print("Error: " + self.media_player.errorString())

	def cleanup(self):
		# clean up media player resources to prevent segfaults
		self.media_player.stop()
		self.media_player.setMedia(QMediaContent())
		self.media_player.stateChanged.disconnect()
		self.media_player.positionChanged.disconnect()
		self.media_player.durationChanged.disconnect()

	def _update_video_metadata(self):
		frame_rate = self.media_player.metaData(QMediaMetaData.VideoFrameRate)
		self.main_window.set_frame_rate(frame_rate)
		self.update_overlay()

	def _read_video_frame_rate(self, filename):
		cap = cv2.VideoCapture(filename)
		if not cap.isOpened():
			return None
		fps = cap.get(cv2.CAP_PROP_FPS)
		cap.release()
		if fps and fps > 0:
			return fps
		return None
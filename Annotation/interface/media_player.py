# Adapted from https://codeloop.org/python-how-to-create-media-player-in-pyqt5/
import os
from bisect import bisect_left

import cv2
from PyQt5.QtWidgets import QWidget, QPushButton, QStyle, QSlider, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QGraphicsView, QGraphicsScene, QMessageBox, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QSizePolicy, QButtonGroup
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaMetaData
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5.QtCore import Qt, QUrl, QEvent, QSizeF, QSize

from utils.event_class import ms_to_time


class MediaPlayer(QWidget):

	def __init__(self, main_window):

		# Defining the elements of the media player
		super().__init__()

		self.main_window = main_window

		# Media Player
		self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
		self.media_player.setNotifyInterval(33)

		self.video_scene = QGraphicsScene(self)
		self.video_item = QGraphicsVideoItem()
		self.video_scene.addItem(self.video_item)

		self.video_view = QGraphicsView(self.video_scene)
		self.video_view.setFrameShape(QGraphicsView.NoFrame)
		self.video_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.video_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.video_view.setStyleSheet("background: transparent;")
		self.video_view.setAttribute(Qt.WA_TranslucentBackground, True)
		self.video_view.viewport().setAttribute(Qt.WA_TranslucentBackground, True)
		self.video_view.setFocusPolicy(Qt.NoFocus)

		# Create container widget for video with overlay
		self.video_container = QWidget()
		video_container_layout = QVBoxLayout()
		video_container_layout.setContentsMargins(0, 0, 0, 0)
		video_container_layout.addWidget(self.video_view)
		self.video_container.setLayout(video_container_layout)

		# Create overlay label for displaying position and editing mode
		self.overlay_label = QLabel(self.video_container)
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
		self.overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
		self.overlay_label.raise_()
		self.overlay_label.hide()

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

		# Passing-event badges (stacked)
		self._badge_width = 300
		self._badge_height = 26

		self.pass_label_container = QWidget(self.video_container)
		# Make sure container itself never paints a background
		self.pass_label_container.setAutoFillBackground(False)
		self.pass_label_container.setAttribute(Qt.WA_NoSystemBackground, True)
		self.pass_label_container.setAttribute(Qt.WA_TranslucentBackground, True)
		self.pass_label_container.setStyleSheet("QWidget { background-color: rgba(0,0,0,0); border: none; }")

		pass_layout = QVBoxLayout()
		pass_layout.setSpacing(4)
		pass_layout.setContentsMargins(0, 0, 0, 0)
		self.pass_label_container.setLayout(pass_layout)
		self.pass_label_container.setAttribute(Qt.WA_TransparentForMouseEvents, True)
		self.pass_label_container.raise_()
		self.pass_label_container.hide()
		self._pass_label_layout = pass_layout

		self.pause_at_events = False
		self.pause_at_event_frames = []
		self._pause_action_filter = None
		self._pass_event_display_filter = None
		self._next_pause_index = 0
		self._last_position_frame = 0
		self._pause_event_source = None

		self.video_container.installEventFilter(self)

		# Button to open a new file
		self.open_file_button = QPushButton('Open video')
		self.open_file_button.clicked.connect(self.open_file)
		self.open_file_button.setFocusPolicy(Qt.NoFocus)
		self.open_file_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		# Button for playing the video
		self.play_button = QPushButton()
		self.play_button.setEnabled(False)
		self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.play_button.clicked.connect(self.play_video)
		self.play_button.setFocusPolicy(Qt.NoFocus)
		self.play_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.speed_half_button = QPushButton("1/2x")
		self.speed_half_button.setCheckable(True)
		self.speed_half_button.clicked.connect(lambda: self.set_playback_rate(0.5))
		self.speed_half_button.setFocusPolicy(Qt.NoFocus)
		self.speed_half_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.speed_normal_button = QPushButton("1x")
		self.speed_normal_button.setCheckable(True)
		self.speed_normal_button.clicked.connect(lambda: self.set_playback_rate(1.0))
		self.speed_normal_button.setFocusPolicy(Qt.NoFocus)
		self.speed_normal_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.speed_double_button = QPushButton("2x")
		self.speed_double_button.setCheckable(True)
		self.speed_double_button.clicked.connect(lambda: self.set_playback_rate(2.0))
		self.speed_double_button.setFocusPolicy(Qt.NoFocus)
		self.speed_double_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.speed_quad_button = QPushButton("4x")
		self.speed_quad_button.setCheckable(True)
		self.speed_quad_button.clicked.connect(lambda: self.set_playback_rate(4.0))
		self.speed_quad_button.setFocusPolicy(Qt.NoFocus)
		self.speed_quad_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self._speed_button_group = QButtonGroup(self)
		self._speed_button_group.setExclusive(True)
		self._speed_button_group.addButton(self.speed_half_button)
		self._speed_button_group.addButton(self.speed_normal_button)
		self._speed_button_group.addButton(self.speed_double_button)
		self._speed_button_group.addButton(self.speed_quad_button)

		self.set_playback_rate(1.0)

		# Button for the slider
		self.slider = QSlider(Qt.Horizontal)
		self.slider.setRange(0, 0)
		self.slider.sliderMoved.connect(self.set_position)
		self.slider.sliderReleased.connect(self._slider_released)
		self.slider.setFocusPolicy(Qt.NoFocus)

		# Volume slider
		self.volume_button = QPushButton()
		self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
		self.volume_button.setFlat(True)
		self.volume_button.setFocusPolicy(Qt.NoFocus)

		# Make the icon button *tight* (removes the big built-in padding/width)
		self.volume_button.setFixedSize(24, 24)
		self.volume_button.setIconSize(QSize(18, 18))
		self.volume_button.setStyleSheet("QPushButton { padding: 0px; border: none; }")

		self.volume_slider = QSlider(Qt.Horizontal)
		self.volume_slider.setRange(0, 100)
		self.volume_slider.setValue(self.media_player.volume() or 100)
		self.volume_slider.sliderMoved.connect(self._set_volume)
		self.volume_slider.valueChanged.connect(self._set_volume)
		self.volume_slider.setFixedWidth(110)
		self.volume_slider.setFocusPolicy(Qt.NoFocus)

		self.help_button = QPushButton("Help")
		self.help_button.clicked.connect(self._show_help_dialog)
		self.help_button.setFocusPolicy(Qt.NoFocus)
		self.help_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.pause_at_events_button = QPushButton("Pause At Tags")
		self.pause_at_events_button.setCheckable(True)
		self.pause_at_events_button.toggled.connect(self._set_pause_at_events)
		self.pause_at_events_button.setFocusPolicy(Qt.NoFocus)
		self.pause_at_events_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.pause_actions_button = QPushButton("Choose Pause Actions")
		self.pause_actions_button.clicked.connect(self._open_pause_action_selector)
		self.pause_actions_button.setFocusPolicy(Qt.NoFocus)
		self.pause_actions_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		self.filter_events_button = QPushButton("Filter Displayed Events")
		self.filter_events_button.clicked.connect(self._open_event_display_filter)
		self.filter_events_button.setFocusPolicy(Qt.NoFocus)
		self.filter_events_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

		# create hbox layout for controls
		control_row = QHBoxLayout()
		control_row.setContentsMargins(0, 0, 0, 0)
		control_row.setSpacing(12)
		control_row.addWidget(self.open_file_button)
		control_row.addWidget(self.play_button)
		control_row.addWidget(self.speed_half_button)
		control_row.addWidget(self.speed_normal_button)
		control_row.addWidget(self.speed_double_button)
		control_row.addWidget(self.speed_quad_button)
		control_row.addWidget(self.pause_at_events_button)
		control_row.addWidget(self.pause_actions_button)
		control_row.addWidget(self.filter_events_button)
		volume_widget = QWidget()
		volume_layout = QHBoxLayout(volume_widget)
		volume_layout.setContentsMargins(0, 0, 0, 0)
		volume_layout.setSpacing(2)
		volume_layout.addWidget(self.volume_button)
		volume_layout.addWidget(self.volume_slider)
		control_row.addWidget(volume_widget)
		control_row.addWidget(self.help_button)
		control_row.addStretch(1)

		# create vbox layout
		self.layout = QVBoxLayout()
		self.layout.addWidget(self.video_container)
		self.layout.addWidget(self.slider)
		self.layout.addLayout(control_row)

		# route video into QGraphicsVideoItem (not QVideoWidget)
		self.media_player.setVideoOutput(self.video_item)

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
			try:
				self.main_window.half = int(filpath[0])
			except (ValueError, IndexError):
				QMessageBox.warning(
					self,
					"Unsupported filename",
					"Please choose a video whose name begins with a number (e.g., \"1.mp4\").",
				)
				self.media_player.setMedia(QMediaContent())
				self.play_button.setEnabled(False)
				return

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

	def _show_help_dialog(self):
		list_display = getattr(self.main_window, "list_display", None)
		if list_display:
			list_display._show_help()

	def set_playback_rate(self, rate):
		position = self.media_player.position()
		self.media_player.setPlaybackRate(rate)
		self.media_player.setPosition(position)

		button_map = {
			0.5: self.speed_half_button,
			1.0: self.speed_normal_button,
			2.0: self.speed_double_button,
			4.0: self.speed_quad_button,
		}
		for r, btn in button_map.items():
			btn.setChecked(r == rate)

	def _set_volume(self, value):
		self.media_player.setVolume(value)

	def mediastate_changed(self, state):
		if self.media_player.state() == QMediaPlayer.PlayingState:
			self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
		else:
			self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

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

	def _video_rect_points_in_container(self):
		"""
		Return (top_left_point, bottom_right_point) IN self.video_container coords
		for where the video is actually drawn inside the QGraphicsView viewport.

		This accounts for letterboxing caused by fitInView(...KeepAspectRatio).
		"""
		scene_rect = self.video_item.sceneBoundingRect()

		# QGraphicsView.mapFromScene -> coordinates in the VIEW/viewport space
		tl_vp = self.video_view.mapFromScene(scene_rect.topLeft())
		br_vp = self.video_view.mapFromScene(scene_rect.bottomRight())

		# Map viewport coords -> container coords
		vp = self.video_view.viewport()
		tl_container = vp.mapTo(self.video_container, tl_vp)
		br_container = vp.mapTo(self.video_container, br_vp)

		return tl_container, br_container

	def _position_overlay_label(self):
		if not self.overlay_label.isVisible():
			return

		margin = 0
		tl, _ = self._video_rect_points_in_container()
		self.overlay_label.move(tl.x() + margin, tl.y() + margin)
		self.overlay_label.raise_()

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
			bg_color = "rgba(255, 0, 0, 180)"  # red
		else:
			overlay_text = frame_str
			bg_color = "rgba(0, 0, 0, 180)"  # black

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

		self.overlay_label.adjustSize()
		self._position_overlay_label()
		self.overlay_label.raise_()

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
			self.pass_label_container.hide()
			self._clear_pass_badges()
			return

		if not getattr(self.main_window, "list_manager", None):
			self.pass_label_container.hide()
			self._clear_pass_badges()
			return

		frame_duration = self.main_window.frame_duration_ms if self.main_window.frame_duration_ms else 40.0
		frames_visible = max(1, int(round(2000.0 / frame_duration)))

		event_entries = []
		for event in sorted(self.main_window.list_manager.event_list, key=lambda e: getattr(e, "frame", float("inf"))):
			event_frame = getattr(event, "frame", None)
			if event_frame is None:
				continue

			if current_frame >= event_frame and current_frame < event_frame + frames_visible:
				if not self._pass_event_display_filter or self._passes_display_filter(event):
					label = event.label or "Event"
					subtype = getattr(event, "subType", None)
					if subtype and subtype != "None":
						text = f"{label} ({subtype})"
					else:
						text = label
					event_entries.append((text, event_frame))

		if not event_entries:
			self._clear_pass_badges()
			self.pass_label_container.hide()
			return

		self._populate_pass_badges([text for text, _ in event_entries])
		self.pass_label_container.show()
		self._position_pass_label()

		list_display = getattr(self.main_window, "list_display", None)
		if list_display:
			closest_event = min(event_entries, key=lambda entry: abs(entry[1] - current_frame))
			list_display.highlight_event_by_frame(closest_event[1])

	def _position_pass_label(self):
		if not self.pass_label_container.isVisible():
			return
		# Center badges over the *actual drawn video* (not the letterboxed container)
		tl, br = self._video_rect_points_in_container()
		video_width = max(1, br.x() - tl.x())

		x = tl.x() + max(0, (video_width - self.pass_label_container.width()) // 2)

		# RESTORE OLD Y: based on label height only (not its y position)
		y = self.overlay_label.height() + 8

		self.pass_label_container.move(x, y)

	def _clear_pass_badges(self):
		while self._pass_label_layout.count():
			item = self._pass_label_layout.takeAt(0)
			if widget := item.widget():
				widget.deleteLater()

	def _populate_pass_badges(self, events):
		self._clear_pass_badges()

		for text in events:
			badge = QLabel(text, self.pass_label_container)
			badge.setFixedSize(self._badge_width, self._badge_height)
			badge.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

			# With QGraphicsVideoItem transparency blended with the video
			badge.setStyleSheet("""
				QLabel {
					background-color: rgba(255, 0, 0, 204);
					color: black;
					padding: 4px 10px;
					border-radius: 4px;
					font-weight: bold;
					font-size: 17px;
				}
			""")
			self._pass_label_layout.addWidget(badge)

		spacing = self._pass_label_layout.spacing()
		count = self._pass_label_layout.count()
		total_height = count * self._badge_height + max(0, count - 1) * spacing
		self.pass_label_container.setFixedSize(self._badge_width, total_height)

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
				if getattr(event, "frame", None) is not None and self._event_allowed_for_pause(event)
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
	
	def _open_multi_select_filter_dialog(self, *, title: str, empty_title: str, empty_message: str, choices, current_filter, on_apply):
		# choices: list[str]
		# current_filter: None or set[str] of normalized keys
		# on_apply: callable(new_filter_or_none) -> None

		if not choices:
			QMessageBox.information(self, empty_title, empty_message)
			return

		dialog = QDialog(self)
		dialog.setWindowTitle(title)
		layout = QVBoxLayout(dialog)

		# Controls row
		control_row = QHBoxLayout()
		select_all = QPushButton("Select All", dialog)
		deselect_all = QPushButton("Deselect All", dialog)
		control_row.addWidget(select_all)
		control_row.addWidget(deselect_all)
		layout.addLayout(control_row)

		# List of checkboxes
		list_widget = QListWidget(dialog)

		active_filter = None if current_filter is None else set(current_filter)

		for action in choices:
			action_key = self._normalize_pause_label(action)
			item = QListWidgetItem(action)
			item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
			item.setCheckState(
				Qt.Checked if active_filter is None or action_key in active_filter else Qt.Unchecked
			)
			list_widget.addItem(item)

		layout.addWidget(list_widget)

		# OK / Cancel
		buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
		buttons.accepted.connect(dialog.accept)
		buttons.rejected.connect(dialog.reject)
		layout.addWidget(buttons)

		def _set_all(state):
			for i in range(list_widget.count()):
				list_widget.item(i).setCheckState(state)

		select_all.clicked.connect(lambda: _set_all(Qt.Checked))
		deselect_all.clicked.connect(lambda: _set_all(Qt.Unchecked))

		if dialog.exec() != QDialog.Accepted:
			return

		selected = {
			self._normalize_pause_label(list_widget.item(i).text())
			for i in range(list_widget.count())
			if list_widget.item(i).checkState() == Qt.Checked
		}

		normalized_choices = {self._normalize_pause_label(choice) for choice in choices}

		new_filter = None
		if selected and selected != normalized_choices:
			new_filter = selected

		on_apply(new_filter)

	def _open_pause_action_selector(self):
		manager = getattr(self.main_window, "list_manager", None)
		if not manager:
			QMessageBox.information(self, "Pause Actions", "Load a video with annotations first.")
			return

		choices = self._pause_action_choices(manager.event_list)

		def _apply(new_filter):
			self._pause_action_filter = new_filter
			self._refresh_pause_queue()

		self._open_multi_select_filter_dialog(
			title="Pause At Actions",
			empty_title="Pause Actions",
			empty_message="No annotated events are available yet.",
			choices=choices,
			current_filter=self._pause_action_filter,
			on_apply=_apply,
		)

	def _open_event_display_filter(self):
		manager = getattr(self.main_window, "list_manager", None)
		if not manager:
			QMessageBox.information(self, "Filter Displayed Events", "Load a video with annotations first.")
			return

		choices = self._pause_action_choices(manager.event_list)

		def _apply(new_filter):
			self._pass_event_display_filter = new_filter
			self.update_overlay()

		self._open_multi_select_filter_dialog(
			title="Filter Displayed Events",
			empty_title="Filter Displayed Events",
			empty_message="No annotated events are available yet.",
			choices=choices,
			current_filter=self._pass_event_display_filter,
			on_apply=_apply,
		)

	def _pause_action_choices(self, events):
		seen = set()
		choices = []
		for event in sorted(events, key=lambda e: self._formatted_pause_label(e)):
			label = self._formatted_pause_label(event)
			key = self._normalize_pause_label(label)
			if label and key not in seen:
				seen.add(key)
				choices.append(label)
		return choices

	def _formatted_pause_label(self, event):
		return getattr(event, "label", None) or "Event"

	def _normalize_pause_label(self, label):
		if label is None:
			return ""
		return str(label).strip().lower()

	def _event_allowed_for_pause(self, event):
		if self._pause_action_filter is None:
			return True
		return (
			self._normalize_pause_label(self._formatted_pause_label(event))
			in self._pause_action_filter
		)

	def _passes_display_filter(self, event):
		if self._pass_event_display_filter is None:
			return True
		return (
			self._normalize_pause_label(self._formatted_pause_label(event))
			in self._pass_event_display_filter
		)

	def _position_event_overlay(self):
		if not self.event_overlay.isVisible():
			return

		margin = 12
		tl, br = self._video_rect_points_in_container()
		video_width = max(1, br.x() - tl.x())

		x = tl.x() + max(0, video_width - self.event_overlay.width() - margin)
		y = tl.y() + margin
		self.event_overlay.move(x, y)
		self.event_overlay.raise_()

	def eventFilter(self, obj, event):
		if obj is self.video_container and event.type() == QEvent.Resize:
			# Keep the video item sized to the view/viewport
			r = self.video_view.viewport().rect()
			self.video_item.setSize(QSizeF(r.width(), r.height()))
			self.video_scene.setSceneRect(0, 0, r.width(), r.height())
			self.video_view.fitInView(self.video_item, Qt.KeepAspectRatio)

			# Reposition overlays relative to the *drawn video* (not letterboxed container)
			self._position_overlay_label()
			self._position_event_overlay()
			self._position_pass_label()

		return super().eventFilter(obj, event)

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
from re import M
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtMultimedia import QMediaPlayer

from interface.media_player import MediaPlayer
from interface.list_display import ListDisplay
from interface.event_selection import EventSelectionWindow
from utils.list_management import ListManager
from utils.event_class import Event, ms_to_time

class MainWindow(QMainWindow):
	QUICK_LABEL_COMBOS = {
		Qt.Key_D: {
			Qt.Key_D: "Drive",
			Qt.Key_H: "Handoff",
			Qt.Key_T: "Defenders Double Team",
			Qt.Key_S: "Defenders Switch",
			Qt.Key_F: "Deflection",
			Qt.Key_U: "Ballhandler Defender Under Screen",
			Qt.Key_O: "Ballhandler Defender Over Screen",
			Qt.Key_B: "Dead Ball Turnover",
			Qt.Key_R: "Defensive Rebound",
		},
		Qt.Key_O: {
			Qt.Key_B: "On Ball Screen",
			Qt.Key_S: "Off Ball Screen",
			Qt.Key_F: "Offensive Foul",
			Qt.Key_O: "Out of Bounds",
			Qt.Key_R: "Offensive Rebound",
		},
		Qt.Key_F: {
			Qt.Key_H: "Fake Handoff",
			Qt.Key_T: "Free Throw",
		},
		Qt.Key_P: {
			Qt.Key_U: "Post Up",
			Qt.Key_S: "Pass",
			Qt.Key_R: "Pass Received",
		},
		Qt.Key_S: {
			Qt.Key_U: "Spot Up",
			Qt.Key_R: "Screener Rolling to Rim",
			Qt.Key_P: "Screener Popping to 3P Line",
			Qt.Key_G: "Screener Ghosts to 3P Line",
			Qt.Key_S: "Screener Slipping the Screen",
			Qt.Key_T: "Steal",
			Qt.Key_F: "Shooting Foul",
		},
		Qt.Key_T: {
			Qt.Key_S: "Transition",
		},
		Qt.Key_I: {
			Qt.Key_S: "Isolation",
			Qt.Key_P: "Inbound Pass",
		},
		Qt.Key_C: {
			Qt.Key_T: "Cut",
			Qt.Key_F: "Common Foul",
		},
		Qt.Key_B: {
			Qt.Key_S: "Blocked Shot",
		},
		Qt.Key_R: {
			Qt.Key_S: "Ballhandler Rejects Screen",
			Qt.Key_U: "Roller Defender Up on Screen",
			Qt.Key_D: "Roller Defender Dropping",
			Qt.Key_H: "Roller Defender Hedging",
		},
		Qt.Key_At: { # Shift + 2
			Qt.Key_P: "2P Shot",
		},
		Qt.Key_NumberSign: { # Shift + 3
			Qt.Key_P: "3P Shot",
		},
		Qt.Key_M: {
			Qt.Key_S: "Made Shot",
		},
		Qt.Key_X: {
			Qt.Key_S: "Missed Shot",
		},
		Qt.Key_V: {
			Qt.Key_NumberSign: "3 Second Violation", # Shift + V + 3
			Qt.Key_Percent: "5 Second Violation", # Shift + V + 5
			Qt.Key_ParenRight: "10 Second Violation", # Shift + V + 10
			Qt.Key_S: "Shot Clock Violation", 
			Qt.Key_T: "Travel Violation",
			Qt.Key_O: "Offensive Goaltending Violation", 
			Qt.Key_L: "Free Throw Lane Violation",
		}
	}
	QUICK_LABEL_NAMES = [
		"Common Foul",
		"Drive"
		"Handoff",
		"Defenders Double Team",
		"Defenders Switch",
		"Deflection",
		"On Ball Screen",
		"Off Ball Screen",
		"Offensive Foul",
		"Ballhandler Rejects Screen",
		"Ballhandler Defender Over Screen",
		"Ballhandler Defender Under Screen",
		"Fake Handoff",
		"Free Throw",
		"Post Up",
		"Pass",
		"Spot Up",
		"Screener Rolling to Rim",
		"Screener Popping to 3P Line",
		"Screener Ghosts to 3P Line",
		"Screener Slipping the Screen",
		"Isolation",
		"Cut",
		"Blocked Shot",
		"Roller Defender Up on Screen",
		"Roller Defender Dropping",
		"Roller Defender Hedging",
		"Defensive Rebound",
		"Offensive Rebound",
		"2P Shot",
		"3P Shot",
		"Made Shot",
		"Missed Shot",
		"Transition",
		"Inbound Pass",
		"Shooting Foul",
		"Steal",
		"Pass Received",
		"Out of Bounds",
		"3 Second Violation",
		"5 Second Violation",
		"10 Second Violation",
		"Shot Clock Violation",
		"Travel Violation",
		"Offensive Goaltending Violation",
		"Free Throw Lane Violation",
	]
	def __init__(self):
		super().__init__()

		# Defining the geometric properties of the window
		self.xpos_main_window = 0 
		self.ypos_main_window = 0
		self.width_main_window = 1920 
		self.height_main_window = 1080

		self.default_frame_duration_ms = 40.0
		self.frame_duration_ms = self.default_frame_duration_ms
		self.video_frame_rate = None

		self.half = 1
		self.editing_event = False
		self.edit_event_obj = None
		self.edit_event_original = None
		self._combo_timer = QTimer(self)
		self._combo_timer.setSingleShot(True)
		self._combo_timer.timeout.connect(self._clear_combo_prefix)
		self._pending_combo = None

		# Defining some variables of the window
		self.title_main_window = "Event Annotator"

		# Setting the window appropriately
		self.setWindowTitle(self.title_main_window)
		self.setGeometry(self.xpos_main_window, self.ypos_main_window, self.width_main_window, self.height_main_window)

		self.palette_main_window = self.palette()
		self.palette_main_window.setColor(QPalette.Window, Qt.black)

		# Initiate the sub-widgets
		self.init_main_window()

		# Show the window
		self.show()

		# Make sure the main window can receive keyboard focus
		self.setFocusPolicy(Qt.StrongFocus)

		# Delay focus until after Qt finishes showing/layout
		QTimer.singleShot(0, self._set_initial_focus)


	def init_main_window(self):

		# Add the media player
		self.media_player = MediaPlayer(self)
		video_display = QWidget(self)
		video_display.setLayout(self.media_player.layout)

		# Create the list manager and corresponding display
		self.list_manager = ListManager()
		self.list_display = ListDisplay(self)

		# Create the Event selection Window
		self.event_window = EventSelectionWindow(self)

		self.list_display.display_list()


		# Layout the different widgets
		central_display = QWidget(self)
		self.setCentralWidget(central_display)

		final_layout = QHBoxLayout()
		final_layout.addWidget(video_display)
		final_layout.addWidget(self.list_display)

		central_display.setLayout(final_layout)

	def keyPressEvent(self, event):
		ctrl = False

		if self._handle_multi_key_combo(event):
			return


		# Edit-mode: Left/Right moves the locked event timestamp
		if self.editing_event and event.key() in (Qt.Key_Left, Qt.Key_Right):
			if not self.media_player.play_button.isEnabled():
				return

			if not self.edit_event_obj:
				self._end_edit_event()
				return

			step_ms = self._frame_step_ms_with_modifiers(event)
			delta = -step_ms if event.key() == Qt.Key_Left else step_ms

			old_pos = int(self.edit_event_obj.position)
			new_pos = max(0, old_pos + int(delta))

			duration = self.media_player.media_player.duration()
			if duration and duration > 0:
				new_pos = min(new_pos, duration)

			attempts = 0
			while attempts < 1000:
				new_frame = self.position_to_frame(new_pos)
				if not self.list_manager.find_event_by_frame(new_frame, self.half, exclude=self.edit_event_obj):
					break

				if delta > 0:
					if duration and new_pos >= duration:
						new_pos = duration
						break
					new_pos = max(0, new_pos + step_ms)
					if duration and new_pos > duration:
						new_pos = duration
						break
				else:
					if new_pos <= 0:
						new_pos = 0
						break
					new_pos = max(0, new_pos - step_ms)

				attempts += 1

			# Update the object in-place, then resort list
			self.edit_event_obj.position = new_pos
			self.edit_event_obj.time = ms_to_time(new_pos)
			self.edit_event_obj.frame = self.position_to_frame(new_pos)
			self.list_manager.sort_list()

			# Refresh UI + keep the edited event highlighted
			self.list_display.display_list()
			try:
				new_row = self.list_manager.event_list.index(self.edit_event_obj)
				self.list_display.list_widget.setCurrentRow(new_row)
			except ValueError:
				pass

			# Seek video to new timestamp (feedback)
			self.media_player.set_position(new_pos)

			self.setFocus()
			return

		# Remove an event with the delete key
		if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
			index = self.list_display.list_widget.currentRow()
			if index >= 0:
				visible_events = getattr(self.list_display, "_visible_events", [])
				if 0 <= index < len(visible_events):
					target_event = visible_events[index]
				else:
					target_event = self.list_manager.get_event(index)
				if target_event:
					self.list_manager.delete_event(target_event)
					self.list_display.display_list()
					path_label = self.media_player.get_last_label_file()
					self.list_manager.save_file(path_label, self.half)
					self._end_edit_event()
			self.setFocus()

		# Play or pause the video with the space key
		if event.key() == Qt.Key_Space:
			if self.media_player.play_button.isEnabled():
				self.media_player.play_video()
				self.setFocus()

		# Move one frame backwards in time
		if event.key() == Qt.Key_Left:
			if self.media_player.play_button.isEnabled():
				position = self.media_player.media_player.position()
				step = self._frame_step_ms_with_modifiers(event)
				if position > step:
					self.media_player.media_player.setPosition(position - step)
			self.setFocus()
		
		if event.key() == Qt.Key_Right:
			if self.media_player.play_button.isEnabled():
				position = self.media_player.media_player.position()
				duration = self.media_player.media_player.duration()
				step = self._frame_step_ms_with_modifiers(event)
				if position < duration - step:
					self.media_player.media_player.setPosition(position + step)
			self.setFocus()

		# Enter: when viewing clips, stop and start editing; otherwise lock timestamp, edit label, or open new annotation
		if event.key() in (Qt.Key_Return, Qt.Key_Enter):
			if self.list_display._playing_clips:
				row = self.list_display.list_widget.currentRow()
				self.list_display._stop_clip_sequence()
				if row >= 0:
					self.list_display._activate_row(row)
				return
			# Command/Ctrl + Enter should reopen the annotation window while editing
			if self.editing_event and event.modifiers() & (Qt.MetaModifier | Qt.ControlModifier):
				self._open_event_window_for_edit()
				return

			# Enter in edit mode: save and exit edit mode
			if self.editing_event:
				if self.media_player.play_button.isEnabled():
					path_label = self.media_player.get_last_label_file()
					self.list_manager.save_file(path_label, self.half)
				self._end_edit_event()
				return

			# Enter when not editing: open new annotation
			if self.media_player.play_button.isEnabled() and not self.media_player.media_player.state() == QMediaPlayer.PlayingState:
				self._open_event_window_with_label(None)
			return


		# Set the playback rate to normal
		if event.key() == Qt.Key_F1 or event.key() == Qt.Key_A:
			position = self.media_player.media_player.position()
			self.media_player.media_player.setPlaybackRate(1.0)
			self.media_player.media_player.setPosition(position)
			self.setFocus()

		# Set the playback rate to x2
		if event.key() == Qt.Key_F2 or event.key() == Qt.Key_Z:
			position = self.media_player.media_player.position()
			self.media_player.media_player.setPlaybackRate(2.0)
			self.media_player.media_player.setPosition(position)
			self.setFocus()

		# Set the playback rate to x4
		if event.key() == Qt.Key_F3 or event.key() == Qt.Key_E:
			position = self.media_player.media_player.position()
			self.media_player.media_player.setPlaybackRate(4.0)
			self.media_player.media_player.setPosition(position)
			self.setFocus()

		if event.key() == Qt.Key_Escape:
			if self.editing_event:
				self._revert_edit_event()
			else:
				self.list_display.list_widget.setCurrentRow(-1)
				self.setFocus()
			return

		if event.modifiers() & Qt.ControlModifier:
			ctrl = True

		if event.key() == Qt.Key_S and ctrl:
			if self.media_player.play_button.isEnabled():
				path_label = self.media_player.get_last_label_file()
				self.list_manager.save_file(path_label, self.half)

	def _handle_multi_key_combo(self, event):
		if not (event.modifiers() & Qt.ShiftModifier):
			self._clear_combo_prefix()
			return False

		key = event.key()
		if self._pending_combo is None:
			if key in self.QUICK_LABEL_COMBOS:
				self._set_combo_prefix(key)
				return True
			return False

		combo_map = self.QUICK_LABEL_COMBOS.get(self._pending_combo, {})
		label = combo_map.get(key)
		self._clear_combo_prefix()
		if label:
			self._open_event_window_with_label(label)
			return True

		return False

	def _set_combo_prefix(self, value):
		self._pending_combo = value
		self._combo_timer.start(1000)

	def _clear_combo_prefix(self):
		self._pending_combo = None
		self._combo_timer.stop()

	def set_frame_rate(self, frame_rate):
		try:
			rate = float(frame_rate)
		except (TypeError, ValueError):
			rate = None

		if rate and rate > 0:
			self.video_frame_rate = rate
			self.frame_duration_ms = 1000.0 / rate
		else:
			self.video_frame_rate = None
			self.frame_duration_ms = self.default_frame_duration_ms

	def _frame_step_ms_with_modifiers(self, event):
		multiplier = 1
		if event.modifiers() & Qt.ShiftModifier:
			multiplier *= 5
		if event.modifiers() & Qt.ControlModifier:
			multiplier *= 10
		frame_duration_ms = self.frame_duration_ms or self.default_frame_duration_ms
		return max(1, int(round(frame_duration_ms * multiplier)))

	def position_to_frame(self, position_ms):
		frame_duration_ms = self.frame_duration_ms if self.frame_duration_ms else self.default_frame_duration_ms
		frame_duration_ms = max(frame_duration_ms, 0.001)
		return max(0, int(round(position_ms / frame_duration_ms)))

	def _open_event_window_with_label(self, label: str):
		if not self._show_event_window():
			return

		ok = self.event_window.preselect_first_label(label)
		if not ok:
			self.event_window.list_widget.setFocus()

	def _open_event_window_for_edit(self):
		if not self.edit_event_obj:
			return
		if not self._show_event_window(for_edit=True):
			return

		ok = self.event_window.preselect_event(self.edit_event_obj)
		if not ok:
			self.event_window.list_widget.setFocus()

	def _show_event_window(self, for_edit=False):
		if not self.media_player.play_button.isEnabled():
			return False
		if self.media_player.media_player.state() == QMediaPlayer.PlayingState:
			return False

		if not for_edit:
			frame = self.position_to_frame(self.media_player.media_player.position())
			if self.list_manager.find_event_by_frame(frame, self.half):
				QMessageBox.warning(
					self,
					"Duplicate frame",
					"An event already exists on this frame. Delete it before creating another or pick a different frame. If you are editing an existing event, use Command/Ctrl + Enter to reopen the annotation window.",
				)
				return False

		self.event_window.set_position()
		self.event_window.show()
		self.event_window.setFocus()
		return True

	def _set_initial_focus(self):
		# Prefer focusing the main window so keyPressEvent gets keys
		self.setFocus()
		# Also clear list selection so it doesn't steal attention
		self.list_display.list_widget.setCurrentRow(-1)

	def _begin_edit_event(self, event_obj):
		self.editing_event = True
		self.edit_event_obj = event_obj
		self.edit_event_original = {
			"position": event_obj.position,
			"time": event_obj.time,
			"frame": event_obj.frame,
		}
		# Update overlay to show editing mode
		self.media_player.update_overlay()

	def _revert_edit_event(self):
		if not self.edit_event_obj or not self.edit_event_original:
			self._end_edit_event()
			return

		self.edit_event_obj.position = self.edit_event_original["position"]
		self.edit_event_obj.time = self.edit_event_original["time"]
		self.edit_event_obj.frame = self.edit_event_original["frame"]

		self.list_manager.sort_list()
		self.list_display.display_list()
		
		new_row = self.list_manager.event_list.index(self.edit_event_obj)
		self.list_display.list_widget.setCurrentRow(new_row)

		self.media_player.set_position(self.edit_event_original["position"])
		self._end_edit_event()

	def _end_edit_event(self, keep_focus=False):
		self.editing_event = False
		self.edit_event_obj = None
		self.edit_event_original = None
		# Clear list selection so arrows go back to scrubbing
		self.list_display.list_widget.setCurrentRow(-1)
		# Update overlay to show normal mode
		self.media_player.update_overlay()
		if not keep_focus:
			self.setFocus()

	def closeEvent(self, event):
		# Clean up media player before closing
		self.media_player.cleanup()
		event.accept()

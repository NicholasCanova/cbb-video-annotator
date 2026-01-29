from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtMultimedia import QMediaPlayer

from interface.media_player import MediaPlayer
from interface.list_display import ListDisplay
from interface.event_selection import EventSelectionWindow
from utils.list_management import ListManager
from utils.event_class import Event, ms_to_time

class MainWindow(QMainWindow):
	QUICK_LABEL_HOTKEYS = {
		Qt.Key_1: "Drive",
		Qt.Key_2: "On Ball Screen",
		Qt.Key_3: "Dribble Handoff",
		Qt.Key_4: "Fake Handoff",
		Qt.Key_5: "Off Ball Screen",
		Qt.Key_6: "Post Up",
		Qt.Key_7: "Spot Up",
		Qt.Key_8: "Isolation",
		Qt.Key_9: "Cut",
		Qt.Key_0: "Screener Rolling to Rim",
		Qt.Key_Minus: "Screener Popping to 3P Line",
		Qt.Key_Equal: "Screener Slipping the Screen",
		Qt.Key_Q: "Defenders Double Team",
		Qt.Key_W: "Defenders Switch",
		Qt.Key_R: "Ballhandler Defender Over Screen",
		Qt.Key_T: "Ballhandler Defender Under Screen",
		Qt.Key_Y: "Roller Defender Up on Screen",
		Qt.Key_U: "Roller Defender Dropping",
		Qt.Key_I: "Roller Defender Hedging",
		Qt.Key_J: "2P Shot",
		Qt.Key_K: "3P Shot",
		Qt.Key_F: "Free Throw",
		Qt.Key_G: "Missed Shot",
		Qt.Key_B: "Made Shot",
		Qt.Key_C: "Blocked Shot",
		Qt.Key_V: "Rebound",
		Qt.Key_N: "Turnover with Steal",
		Qt.Key_M: "Turnover without Steal",
		Qt.Key_L: "Foul Committed",
		Qt.Key_P: "Pass",
	}
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

		if self._handle_quick_label_hotkey(event):
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
				self.list_manager.delete_event(index)
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

		# Enter: lock edited timestamp, edit label, or open new annotation
		if event.key() in (Qt.Key_Return, Qt.Key_Enter):
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
			self.list_display.list_widget.setCurrentRow(-1)
			self.setFocus()

		if event.modifiers() & Qt.ControlModifier:
			ctrl = True

		if event.key() == Qt.Key_S and ctrl:
			if self.media_player.play_button.isEnabled():
				path_label = self.media_player.get_last_label_file()
				self.list_manager.save_file(path_label, self.half)

	def _handle_quick_label_hotkey(self, event):
		if event.modifiers() != Qt.NoModifier:
			return False
		label = self.QUICK_LABEL_HOTKEYS.get(event.key())
		if not label:
			return False

		self._open_event_window_with_label(label)
		return True

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
		return max(1, int(round(self.frame_duration_ms * multiplier)))

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
		if not self._show_event_window():
			return

		ok = self.event_window.preselect_event(self.edit_event_obj)
		if not ok:
			self.event_window.list_widget.setFocus()

	def _show_event_window(self):
		if not self.media_player.play_button.isEnabled():
			return False
		if self.media_player.media_player.state() == QMediaPlayer.PlayingState:
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
		# Update overlay to show editing mode
		self.media_player.update_overlay()

	def _end_edit_event(self, keep_focus=False):
		self.editing_event = False
		self.edit_event_obj = None
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

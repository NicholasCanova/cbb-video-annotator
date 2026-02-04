from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QCompleter, QApplication
from PyQt5.QtCore import Qt, QStringListModel, QEvent, QTimer
from PyQt5.QtMultimedia import QMediaPlayer


class ListDisplay(QWidget):

	def __init__(self, main_window):
		super().__init__()

		self.max_width = 300
		self.setMaximumWidth(self.max_width)

		self.main_window = main_window

		# Filter state:
		self._typed_text = ""
		self._committed_action = ""
		self._visible_events = []

		# Completer model (action types only)
		self._actions_model = QStringListModel()
		self._completer = QCompleter(self._actions_model, self)
		self._completer.setCaseSensitivity(Qt.CaseInsensitive)

		# PopupCompletion: show dropdown (no inline completion in the line edit)
		# MatchStartsWith: "p" keeps only items that start with p
		self._completer.setCompletionMode(QCompleter.PopupCompletion)
		self._completer.setFilterMode(Qt.MatchStartsWith)

		# When user picks from dropdown (mouse or Enter while popup focus), commit
		self._completer.activated.connect(self._commit_action_from_dropdown)

		# Layout
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)

		self._filter_layout = QHBoxLayout()

		# Create and configure the search/filter input box for action filtering
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("Filter actions")
		self.search_input.setCompleter(self._completer)
		self.search_input.installEventFilter(self)
		self.search_input.textEdited.connect(self._on_search_text_edited)
		self.search_input.returnPressed.connect(self._commit_from_enter)

		self.clear_filter_button = QPushButton("Clear")
		self.clear_filter_button.clicked.connect(self._clear_filter)

		self._filter_layout.addWidget(self.search_input)
		self._filter_layout.addWidget(self.clear_filter_button)
		self.layout.addLayout(self._filter_layout)

		# Event list
		self.list_widget = QListWidget()
		self.list_widget.setSelectionMode(QListWidget.SingleSelection)

		self.list_widget.clicked.connect(self._on_event_clicked)
		self.layout.addWidget(self.list_widget)

		self.play_clips_button = QPushButton("View Event Clips")
		self.play_clips_button.clicked.connect(self._toggle_play_clips)
		self.layout.addWidget(self.play_clips_button)

		self._clip_sequence = []
		self._current_clip_index = 0
		self._playing_clips = False
		self._current_clip_end = None

		self._clip_pause_timer = QTimer(self)
		self._clip_pause_timer.setSingleShot(True)
		self._clip_pause_timer.timeout.connect(self._play_next_clip)
		self.list_widget.itemDoubleClicked.connect(self._on_event_double_clicked)

		self.main_window.media_player.media_player.positionChanged.connect(self._handle_position_update)

		

	def _on_event_clicked(self, model_index):
		row = model_index.row()
		if row >= 0:
			if self._playing_clips:
				self._jump_to_clip_for_row(row)
			else:
				self._activate_row(row)

	def _on_event_double_clicked(self, item):
		row = self.list_widget.row(item)
		if row < 0:
			return

		if self._playing_clips:
			self._stop_clip_sequence()

		self._activate_row(row)

	def _activate_row(self, row):
		if row < 0 or row >= len(self._visible_events):
			return

		self.list_widget.setCurrentRow(row)
		event = self._visible_events[row]

		self._update_event_info(event)

		self.main_window._begin_edit_event(event)
		self.main_window.media_player.media_player.pause()
		self.main_window.media_player.set_position(event.position)
		self.main_window.setFocus()

	def display_list(self, events=None):
		self._stop_clip_sequence()
		if events is None:
			events = list(
				getattr(self.main_window, "list_manager", None).event_list
				if getattr(self.main_window, "list_manager", None)
				else []
			)
		self._visible_events = self._filter_events(events)

		self.list_widget.clear()
		for idx, event in enumerate(self._visible_events):
			self.list_widget.insertItem(idx, event.to_text())

	def _available_action_list(self):
		actions = set(self.main_window.QUICK_LABEL_HOTKEYS.values())
		if getattr(self.main_window, "list_manager", None):
			for event in self.main_window.list_manager.event_list:
				val = getattr(event, "label", None)
				if val:
					actions.add(str(val))
		return sorted(actions, key=lambda s: s.lower())

	def _show_dropdown(self):
		# Make sure model is fresh before showing
		self._actions_model.setStringList(self._available_action_list())

		# Set the completer prefix to whatever user typed
		self._completer.setCompletionPrefix(self._typed_text)
		self._completer.complete()

		# Set the index to the search bar
		popup = self._completer.popup()
		popup.setCurrentIndex(popup.model().index(-1, -1))


	def _commit_action_from_dropdown(self, text):
		# Commit the chosen action and filter event list
		action = (text or "").strip()
		if not action:
			return

		self._committed_action = action

		# Update the text box to show committed filter
		self.search_input.blockSignals(True)
		self.search_input.setText(action)
		self.search_input.blockSignals(False)

		# Filter the events list
		self.display_list()

	def _commit_from_enter(self):
		# Enter should commit the currently highlighted dropdown item if popup is open.
		popup = self._completer.popup()
		if popup and popup.isVisible():
			idx = popup.currentIndex()
			if idx.isValid():
				text = idx.data()
				self._commit_action_from_dropdown(text)
				popup.hide()
				return

		# If popup isn't open, commit whatever is typed as an exact action filter
		txt = (self.search_input.text() or "").strip()
		if txt:
			self._commit_action_from_dropdown(txt)

	def _on_search_text_edited(self, text):
		self._typed_text = (text or "")
		self._show_dropdown()


	def _clear_filter(self):
		self._typed_text = ""
		self._committed_action = ""

		self.search_input.blockSignals(True)
		self.search_input.clear()
		self.search_input.blockSignals(False)

		# Hide popup if open
		popup = self._completer.popup()
		if popup and popup.isVisible():
			popup.hide()

		self.display_list()

	def _toggle_play_clips(self):
		if self._playing_clips:
			self._stop_clip_sequence()
			return

		if not self.main_window.media_player.play_button.isEnabled():
			return

		if self.main_window.editing_event:
			self.main_window._end_edit_event()

		events = list(self._visible_events)
		self._clip_sequence = self._build_clip_sequence(events)
		if not self._clip_sequence:
			return

		self._playing_clips = True
		self._current_clip_index = 0
		self.play_clips_button.setText("Stop Clips")
		self._play_next_clip()

	def _build_clip_sequence(self, events):
		if not events:
			return []
		duration = self.main_window.media_player.media_player.duration()
		indexed = [
			(idx, event)
			for idx, event in enumerate(events)
			if getattr(event, "position", None) is not None
		]
		indexed.sort(key=lambda pair: getattr(pair[1], "position", 0))
		sequence = []
		for idx, event in indexed:
			position = int(getattr(event, "position"))
			start = max(0, position - 2000)
			end = position + 4000
			if duration and end > duration:
				end = duration
			if end <= start:
				continue
			sequence.append({"row": idx, "start": start, "end": end})
		return sequence

	def _play_next_clip(self):
		self._clip_pause_timer.stop()
		if not self._playing_clips or self._current_clip_index >= len(self._clip_sequence):
			self._stop_clip_sequence()
			return

		clip = self._clip_sequence[self._current_clip_index]
		self.list_widget.setCurrentRow(clip["row"])
		start, end = clip["start"], clip["end"]
		self.main_window.media_player.set_position(start)

		self._current_clip_end = end
		event = self._visible_events[clip["row"]]
		self._update_event_info(event)
		player = self.main_window.media_player.media_player
		player.play()
		self.main_window.setFocus()

	def _stop_clip_sequence(self):
		self._clip_pause_timer.stop()
		self._match_stop_state()

	def _match_stop_state(self):
		self._playing_clips = False
		self._clip_sequence = []
		self._current_clip_index = 0
		self._current_clip_end = None
		self.play_clips_button.setText("View Event Clips")
		self.main_window.media_player.media_player.pause()
		self.list_widget.setCurrentRow(-1)
		self._update_event_info(None)

	def _update_event_info(self, event):
		self.main_window.media_player.display_event_info(event)


	def _handle_position_update(self, position):
		if not self._playing_clips or self._current_clip_end is None:
			return

		player = self.main_window.media_player.media_player
		if player.state() != QMediaPlayer.PlayingState:
			return

		if position >= self._current_clip_end:
			player.pause()
			self._current_clip_index += 1
			self._current_clip_end = None

			if self._current_clip_index >= len(self._clip_sequence):
				self._stop_clip_sequence()
				return

			self._clip_pause_timer.start(1000)

	def _jump_to_clip_for_row(self, row):
		target = self._find_clip_index_for_row(row)
		if target is None:
			return

		self._clip_pause_timer.stop()
		player = self.main_window.media_player.media_player
		player.pause()
		self._current_clip_end = None
		self._current_clip_index = target
		self._play_next_clip()

	def _find_clip_index_for_row(self, row):
		for idx, clip in enumerate(self._clip_sequence):
			if clip["row"] == row:
				return idx
		return None

	def _filter_events(self, events):
		if not self._committed_action:
			return list(events)

		target = self._committed_action.strip().lower()
		return [e for e in events if str(getattr(e, "label", None)).strip().lower() == target]


	def eventFilter(self, obj, event):
		if obj is self.search_input and event.type() == QEvent.MouseButtonPress:
			self.main_window._end_edit_event(keep_focus=True)
			# Show dropdown on click into the bar
			out = super().eventFilter(obj, event)
			self._typed_text = (self.search_input.text() or "").strip()
			self._show_dropdown()
			return out

		if obj is self.search_input and event.type() == QEvent.KeyPress:
			key = event.key()

			# Up/Down should navigate the dropdown
			if key in (Qt.Key_Down, Qt.Key_Up):
				self._show_dropdown()
				popup = self._completer.popup()
				if popup and popup.isVisible():
					# Forward the key to popup for normal navigation
					QApplication.sendEvent(popup, event)
					return True
				return False

			# Enter commits (handled by returnPressed too, but intercept to be safe)
			if key in (Qt.Key_Return, Qt.Key_Enter):
				self._commit_from_enter()
				return True

			# Escape hides dropdown or clears if already hidden
			if key == Qt.Key_Escape:
				popup = self._completer.popup()
				if popup and popup.isVisible():
					popup.hide()
				else:
					self._clear_filter()
				return True

		return super().eventFilter(obj, event)

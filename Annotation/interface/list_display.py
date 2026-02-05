from PyQt5.QtWidgets import (
	QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
	QCompleter, QApplication, QDialog, QLabel, QTextBrowser, QFrame,
	QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QStringListModel, QEvent, QTimer
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QFont


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

		# Help dialog refs/state (for expand/shrink)
		self._help_dialog = None
		self._help_outer_layout = None
		self._help_instructions_card = None
		self._help_hotkeys_card = None
		self._help_hotkeys_table = None
		self._help_hotkeys_search = None
		self._help_expanded = None
		self._help_hotkeys_target_rows = 5

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

		self.help_button = QPushButton("Help")
		self.help_button.clicked.connect(self._show_help)
		self.layout.addWidget(self.help_button)

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

		self.main_window.media_player.refresh_event_pause_queue()

	def highlight_event_by_frame(self, frame):
		for idx, event in enumerate(self._visible_events):
			if getattr(event, "frame", None) == frame:
				self.list_widget.setCurrentRow(idx)
				return True
		return False

	def _available_action_list(self):
		actions = set(self.main_window.QUICK_LABEL_NAMES)
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
		self.play_clips_button.setText("Stop Viewing Clips")
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

	def _help_subtitle(self):
		if self.main_window.editing_event:
			return "Editing Mode"
		if self._playing_clips:
			return "View Clips Mode"
		return "Normal Mode"

	def _all_hotkey_rows(self):
		return [
			("Shift + D + R", "Drive"),
			("Shift + D + H", "Dribble Handoff"),
			("Shift + D + T", "Defenders Double Team"),
			("Shift + D + S", "Defenders Switch"),
			("Shift + D + F", "Deflection"),
			("Shift + O + B", "On Ball Screen"),
			("Shift + O + F", "Off Ball Screen"),
			("Shift + O + S", "Ballhandler Defender Over Screen"),
			("Shift + U + S", "Ballhandler Defender Under Screen"),
			("Shift + F + H", "Fake Handoff"),
			("Shift + F + T", "Free Throw"),
			("Shift + F + C", "Foul Committed"),
			("Shift + P + U", "Post Up"),
			("Shift + P + S", "Pass"),
			("Shift + S + U", "Spot Up"),
			("Shift + S + R", "Screener Rolling to Rim"),
			("Shift + S + P", "Screener Popping to 3P Line"),
			("Shift + S + G", "Screener Ghosts to 3P Line"),
			("Shift + S + S", "Screener Slipping the Screen"),
			("Shift + I + S", "Isolation"),
			("Shift + C + T", "Cut"),
			("Shift + B + S", "Blocked Shot"),
			("Shift + R + U", "Roller Defender Up on Screen"),
			("Shift + R + D", "Roller Defender Dropping"),
			("Shift + R + H", "Roller Defender Hedging"),
			("Shift + R + B", "Rebound"),
			("Shift + 2 + P (@ + P)", "2P Shot"),
			("Shift + 3 + P (# + P)", "3P Shot"),
			("Shift + M + S", "Made Shot"),
			("Shift + X + S", "Missed Shot"),
			("Shift + T + S", "Turnover with Steal"),
			("Shift + T + W", "Turnover without Steal"),
		]

	def _filter_hotkey_rows(self, query):
		q = (query or "").strip().lower()
		rows = self._all_hotkey_rows()
		if not q:
			return rows
		return [(hk, desc) for hk, desc in rows if (q in hk.lower() or q in desc.lower())]

	def _build_static_help_html(self):
		mode = self._help_subtitle()

		common_style = """
		<style>
			body { font-family: Arial, Helvetica, sans-serif; margin: 0; }
			.card {
				background: #141826;
				border: 1px solid #2a3142;
				border-radius: 12px;
				padding: 12px 12px;
				margin-bottom: 10px;
			}
			.cardTitle {
				font-size: 16px;
				font-weight: 700;
				margin-bottom: 10px;
				color: #ffffff;
			}
			.cardBody { color: #cfd6e6; line-height: 1.45; }
			code {
				background: #0f1117;
				border: 1px solid #2a3142;
				padding: 1px 6px;
				border-radius: 8px;
				color: #e6e9f2;
			}
			ul { margin: 0; padding-left: 18px; }
			li { margin: 4px 0; }
		</style>
		"""

		if mode == "Editing Mode":
			body = """
			<div class="card">
				<div class="cardTitle">Editing Mode</div>
				<div class="cardBody">
					<ul>
						<li>Use Left/Right (with Shift/Command modifiers) to fine-tune the locked frame.</li>
						<li>Press <b>Enter</b> to lock it in and return to normal playback.</li>
						<li>Press <b>Command + Enter</b> to reopen Event Selection.</li>
						<li>Press <b>Esc</b> to cancel editing and revert the previous annotation.</li>
					</ul>
				</div>
			</div>
			"""
			return f"<html><head>{common_style}</head><body>{body}</body></html>"

		if mode == "View Clips Mode":
			body = """
			<div class="card">
				<div class="cardTitle">View Clips Mode</div>
				<div class="cardBody">
					<ul>
						<li>Single-click an event to jump to that clip in the sequence.</li>
						<li>Double-click (or <b>Enter</b>) to stop clip playback and edit the highlighted event.</li>
						<li>The top-right overlay shows the current event.</li>
					</ul>
				</div>
			</div>
			"""
			return f"<html><head>{common_style}</head><body>{body}</body></html>"

		# Normal Mode
		body = """
		<div class="card">
			<div class="cardTitle">Getting Started</div>
			<div class="cardBody">
				<ul>
					<li>Click <b>Open Video</b> to load <code>1.mov</code> with <code>Labels-v2.json</code> in the same folder.</li>
					<li>Space toggles play/pause. Arrow keys step. Use modifiers for bigger jumps (Shift = 5 frames, Command = 10, Shift+Command = 50).</li>
					<li>A = ×1 speed, Z = ×2, E = ×4.</li>
				</ul>
			</div>
		</div>

		<div class="card">
			<div class="cardTitle">Editing Existing Events</div>
			<div class="cardBody">
				<ul>
					<li>Select an event, then hit <b>ENTER</b> to edit what frame it is tagged on or change the label.</li>
					<li>Delete an annotation by selecting it and pressing <b>DELETE</b>.</li>
				</ul>
			</div>
		</div>

		<div class="card">
			<div class="cardTitle">Creating New Events</div>
			<div class="cardBody">
				<ul>
					<li>Navigate to the frame where the event occurs.</li>
					<li>Press <b>ENTER</b> to create a generic event, or use a hotkey below to create a specific action.</li>
				</ul>
			</div>
		</div>
		"""
		return f"<html><head>{common_style}</head><body>{body}</body></html>"



	def _build_instructions_card(self, parent_dialog):
		card = QFrame(parent_dialog)
		card.setObjectName("helpCard")

		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(12, 12, 12, 12)
		card_layout.setSpacing(10)

		# header row
		header_row = QHBoxLayout()
		header_row.setContentsMargins(0, 0, 0, 0)

		title = QLabel("Instructions", card)
		title.setObjectName("helpCardTitle")

		expand_btn = QPushButton("Expand", card)
		expand_btn.setObjectName("cardExpandBtn")
		expand_btn.setCheckable(True)
		expand_btn.clicked.connect(lambda: self._toggle_help_expand("instructions"))

		def _sync_btn():
			expand_btn.setText("Shrink" if expand_btn.isChecked() else "Expand")
		expand_btn.toggled.connect(lambda _: _sync_btn())
		_sync_btn()

		header_row.addWidget(title)
		header_row.addStretch(1)
		header_row.addWidget(expand_btn)
		card_layout.addLayout(header_row)

		body = QTextBrowser(card)
		body.setOpenExternalLinks(True)
		body.setObjectName("helpBody")
		body.setHtml(self._build_static_help_html())
		card_layout.addWidget(body, 1)

		self._help_instructions_card = card
		return card

	def _build_hotkeys_card(self, parent_dialog):
		card = QFrame(parent_dialog)
		card.setObjectName("helpCard")

		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(12, 12, 12, 12)
		card_layout.setSpacing(10)

		# --- Card header row (title + expand button) ---
		header_row = QHBoxLayout()
		header_row.setContentsMargins(0, 0, 0, 0)

		title = QLabel("Action Creation Hotkeys", card)
		title.setObjectName("helpCardTitle")

		expand_btn = QPushButton("Expand", card)
		expand_btn.setObjectName("cardExpandBtn")
		expand_btn.setCheckable(True)
		expand_btn.clicked.connect(lambda: self._toggle_help_expand("hotkeys"))

		def _sync_btn():
			expand_btn.setText("Shrink" if expand_btn.isChecked() else "Expand")
		expand_btn.toggled.connect(lambda _: _sync_btn())
		_sync_btn()

		header_row.addWidget(title)
		header_row.addStretch(1)
		header_row.addWidget(expand_btn)
		card_layout.addLayout(header_row)

		search = QLineEdit(card)
		search.setPlaceholderText("Search hotkeys (e.g. drive, rebound, shift + d)")
		search.setClearButtonEnabled(True)
		search.setObjectName("hotkeySearch")
		card_layout.addWidget(search)

		table = QTableWidget(card)
		table.setColumnCount(2)
		table.setHorizontalHeaderLabels(["Hotkey", "Action"])
		table.verticalHeader().setVisible(False)
		table.setShowGrid(False)
		table.setSelectionMode(QTableWidget.NoSelection)
		table.setEditTriggers(QTableWidget.NoEditTriggers)
		table.setFocusPolicy(Qt.NoFocus)
		table.setObjectName("hotkeyTable")

		h = table.horizontalHeader()
		h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
		h.setSectionResizeMode(1, QHeaderView.Stretch)
		h.setVisible(False)

		# Default compact height (~5 rows)
		row_h = table.sizeHintForRow(0)
		if row_h <= 0:
			row_h = 26
		compact_height = self._help_hotkeys_target_rows * row_h + 10
		table.setMinimumHeight(compact_height)
		table.setMaximumHeight(compact_height)

		card_layout.addWidget(table, 1)

		self._help_hotkeys_card = card
		self._help_hotkeys_table = table
		self._help_hotkeys_search = search

		def populate(q):
			rows = self._filter_hotkey_rows(q)

			# In compact mode, pad to at least 5 rows so height is stable
			if self._help_expanded != "hotkeys" and len(rows) < self._help_hotkeys_target_rows:
				rows = rows + [("", "")] * (self._help_hotkeys_target_rows - len(rows))

			table.setRowCount(len(rows))
			for r, (hk, desc) in enumerate(rows):
				item_hk = QTableWidgetItem(hk)
				item_desc = QTableWidgetItem(desc)

				if hk:
					f = item_hk.font()
					f.setBold(True)
					item_hk.setFont(f)

				item_hk.setFlags(Qt.ItemIsEnabled)
				item_desc.setFlags(Qt.ItemIsEnabled)

				table.setItem(r, 0, item_hk)
				table.setItem(r, 1, item_desc)

		search.textChanged.connect(populate)
		populate("")

		return card

	def _toggle_help_expand(self, which):
		"""
		- Expanding hotkeys: moves hotkeys card to top, hides instructions, makes table fill space
		- Expanding instructions: moves instructions to top, hides hotkeys
		- Clicking again shrinks back to normal
		"""
		if not self._help_outer_layout or not self._help_instructions_card or not self._help_hotkeys_card:
			return

		def _remove_widget(w):
			for i in range(self._help_outer_layout.count()):
				item = self._help_outer_layout.itemAt(i)
				if item and item.widget() is w:
					self._help_outer_layout.takeAt(i)
					return

		# SHRINK back to normal if clicking the same one
		if self._help_expanded == which:
			self._help_expanded = None

			self._help_instructions_card.show()
			self._help_hotkeys_card.show()

			# restore order: instructions then hotkeys
			_remove_widget(self._help_instructions_card)
			_remove_widget(self._help_hotkeys_card)

			# index 0 is the header frame; insert below it
			self._help_outer_layout.insertWidget(1, self._help_instructions_card, 1)
			self._help_outer_layout.insertWidget(2, self._help_hotkeys_card, 0)

			# restore hotkeys compact height
			if self._help_hotkeys_table:
				row_h = self._help_hotkeys_table.sizeHintForRow(0)
				if row_h <= 0:
					row_h = 26
				compact_h = self._help_hotkeys_target_rows * row_h + 10
				self._help_hotkeys_table.setMinimumHeight(compact_h)
				self._help_hotkeys_table.setMaximumHeight(compact_h)

			# refresh rows to re-pad blanks if needed
			if self._help_hotkeys_search:
				self._help_hotkeys_search.setText(self._help_hotkeys_search.text())

			return

		# expand selected
		self._help_expanded = which

		if which == "hotkeys":
			# show hotkeys only
			self._help_instructions_card.hide()
			self._help_hotkeys_card.show()

			# move hotkeys card to top (right under header)
			_remove_widget(self._help_hotkeys_card)
			self._help_outer_layout.insertWidget(1, self._help_hotkeys_card, 1)

			# let hotkeys table grow to fill space
			if self._help_hotkeys_table:
				self._help_hotkeys_table.setMinimumHeight(0)
				self._help_hotkeys_table.setMaximumHeight(16777215)

			# refresh rows to remove padding blanks
			if self._help_hotkeys_search:
				self._help_hotkeys_search.setText(self._help_hotkeys_search.text())

		elif which == "instructions":
			# show instructions only
			self._help_hotkeys_card.hide()
			self._help_instructions_card.show()

			# move instructions card to top
			_remove_widget(self._help_instructions_card)
			self._help_outer_layout.insertWidget(1, self._help_instructions_card, 1)

	def _show_help(self):
		# reset dialog-scoped refs/state
		self._help_dialog = None
		self._help_outer_layout = None
		self._help_instructions_card = None
		self._help_hotkeys_card = None
		self._help_hotkeys_table = None
		self._help_hotkeys_search = None
		self._help_expanded = None

		dialog = QDialog(self)
		dialog.setWindowTitle("Help")
		dialog.setModal(True)

		outer = QVBoxLayout(dialog)
		outer.setContentsMargins(14, 14, 14, 14)
		outer.setSpacing(10)

		# Header bar
		header = QFrame(dialog)
		header.setObjectName("helpHeader")
		header_layout = QHBoxLayout(header)
		header_layout.setContentsMargins(12, 10, 12, 10)

		title = QLabel("Help", header)
		title_font = QFont()
		title_font.setPointSize(14)
		title_font.setBold(True)
		title.setFont(title_font)

		subtitle = QLabel(self._help_subtitle(), header)
		subtitle.setObjectName("helpSubtitle")
		subtitle.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

		header_layout.addWidget(title)
		header_layout.addStretch(1)
		header_layout.addWidget(subtitle)

		outer.addWidget(header)

		# Cards
		instructions_card = self._build_instructions_card(dialog)
		hotkeys_card = self._build_hotkeys_card(dialog)

		outer.addWidget(instructions_card, 1)
		outer.addWidget(hotkeys_card, 0)

		# Footer buttons
		footer = QHBoxLayout()
		footer.addStretch(1)

		close_btn = QPushButton("Close", dialog)
		close_btn.clicked.connect(dialog.accept)
		close_btn.setDefault(True)

		footer.addWidget(close_btn)
		outer.addLayout(footer)

		# Store refs for expand behavior
		self._help_dialog = dialog
		self._help_outer_layout = outer
		self._help_instructions_card = instructions_card
		self._help_hotkeys_card = hotkeys_card

		# Styling
		dialog.setStyleSheet("""
			QDialog {
				background: #111318;
			}
			#helpHeader {
				background: #1b1f2a;
				border: 1px solid #2a3142;
				border-radius: 10px;
			}
			#helpSubtitle {
				color: #a9b1c6;
				font-size: 12px;
			}

			#helpCard {
				background: #141826;
				border: 1px solid #2a3142;
				border-radius: 12px;
			}
			#helpCardTitle {
				color: #ffffff;
				font-size: 16px;
				font-weight: 700;
			}
			#cardExpandBtn {
				padding: 4px 10px;
				border-radius: 8px;
				background: #1b1f2a;
				border: 1px solid #2a3142;
				color: #e6e9f2;
			}
			#cardExpandBtn:hover { background: #22283a; }

			#helpBody {
				background: #0f1117;
				border: 1px solid #2a3142;
				border-radius: 10px;
				padding: 10px;
				color: #e6e9f2;
				font-size: 13px;
			}

			#hotkeySearch {
				background: #0f1117;
				border: 1px solid #2a3142;
				border-radius: 10px;
				padding: 6px 10px;
				color: #e6e9f2;
			}
			#hotkeyTable {
				background: #0f1117;
				border: 1px solid #2a3142;
				border-radius: 10px;
				color: #e6e9f2;
			}

			QPushButton {
				padding: 6px 12px;
				border-radius: 8px;
				background: #1b1f2a;
				border: 1px solid #2a3142;
				color: #e6e9f2;
			}
			QPushButton:hover {
				background: #22283a;
			}
		""")

		dialog.resize(720, 620)
		dialog.exec_()

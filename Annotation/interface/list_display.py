from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QCompleter, QApplication, QDialog, QLabel, QTextBrowser, QFrame
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

	def _show_help(self):
		dialog = QDialog(self)
		dialog.setWindowTitle("Help")
		dialog.setModal(True)

		# Outer layout
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

		# Body
		body = QTextBrowser(dialog)
		body.setOpenExternalLinks(True)
		body.setObjectName("helpBody")
		body.setHtml(self._help_html_for_mode())
		outer.addWidget(body, 1)

		# Footer buttons
		footer = QHBoxLayout()
		footer.addStretch(1)

		close_btn = QPushButton("Close", dialog)
		close_btn.clicked.connect(dialog.accept)
		close_btn.setDefault(True)

		footer.addWidget(close_btn)
		outer.addLayout(footer)

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
				#helpBody {
						background: #0f1117;
						border: 1px solid #2a3142;
						border-radius: 10px;
						padding: 10px;
						color: #e6e9f2;
						font-size: 13px;
				}
				#helpBody a { color: #7aa2ff; text-decoration: none; }
				#helpBody a:hover { text-decoration: underline; }
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

		dialog.resize(640, 520)
		dialog.exec_()

	def _help_subtitle(self):
			if self.main_window.editing_event:
					return "Editing Mode"
			if self._playing_clips:
					return "View Clips Mode"
			return "Normal Mode"

	def _help_html_for_mode(self):
			mode = self._help_subtitle()

			# You can expand these over time
			if mode == "Editing Mode":
					sections = [
							("What you can do",
							["Use Left/Right (with Shift/Command modifiers) to fine-tune the locked frame.",
								"Press Enter to lock it in and return to normal playback.",
								"Press Command + Enter to reopen Event Selection.",
								"Press Esc to cancel editing and revert the previous annotation."]),
					]
					return self._render_help_page(mode, sections)

			if mode == "View Clips Mode":
					sections = [
							("Playback controls",
							["Single-click an event to jump to that clip in the sequence.",
								"Double-click (or Enter) to stop clip playback and edit the highlighted event.",
								"Top-right overlay always shows the current event."]),
					]
					return self._render_help_page(mode, sections)

			# Normal Mode (includes hotkeys)
			# Normal usage help (no page title)
			sections = [
					("Getting Started",
					["Click <b>Open Video</b> to load <code>1.mov</code> with <code>Labels-v2.json</code> in the same folder.",
						"Space toggles play/pause. Arrow keys step. Use modifiers for bigger jumps (Shift = 5 frames, Command = 10, Shift+Command = 50).",
						"A = ×1 speed, Z = ×2, E = ×4."]),
					("Editing Existing Events",
					["Select an event, then hit <b>ENTER</b> to edit what frame it is tagged on or change the label.",
						"Delete an annotation by selecting it and pressing <b>DELETE</b>."]),
					("Creating New Events",
					["Navigate to the frame where the event occurs.",
      			"Press <b>ENTER</b> to create a generic event, or use one of the hotkeys below to create a specific action."]),
					("Hotkeys",
					[self._render_hotkeys_table_html()]),
			]

			# pass empty title so no top header text appears
			return self._render_help_page("", sections)


	def _render_help_page(self, title, sections):
			# Simple "card" layout using HTML blocks.
			cards = []
			for heading, bullets in sections:
					items = []
					for b in bullets:
							# allow raw HTML blocks (like the hotkey table) by not wrapping if it looks like HTML
							if "<table" in b or "<div" in b:
									items.append(b)
							else:
									items.append(f"<li>{b}</li>")
					body = "".join(items)
					if not body.strip().startswith("<"):
							body = f"<ul>{body}</ul>"
					cards.append(f"""
							<div class="card">
								<div class="cardTitle">{heading}</div>
								<div class="cardBody">{body}</div>
							</div>
					""")

			return f"""
			<html>
			<head>
				<style>
					body {{
						font-family: Arial, Helvetica, sans-serif;
						margin: 0;
					}}
					.pageTitle {{
						font-size: 16px;
						font-weight: 700;
						margin: 4px 2px 12px 2px;
						color: #e6e9f2;
					}}
					.card {{
						background: #141826;
						border: 1px solid #2a3142;
						border-radius: 12px;
						padding: 12px 12px;
						margin-bottom: 10px;
					}}
					.cardTitle {{
						font-size: 16px;
						font-weight: 700;
						margin-bottom: 10px;
						color: #ffffff;
					}}
					.cardBody {{
						color: #cfd6e6;
						line-height: 1.45;
					}}
					code {{
						background: #0f1117;
						border: 1px solid #2a3142;
						padding: 1px 6px;
						border-radius: 8px;
						color: #e6e9f2;
					}}
					ul {{
						margin: 0;
						padding-left: 18px;
					}}
					li {{ margin: 4px 0; }}
					table.hotkeys {{
						width: 100%;
						border-collapse: collapse;
						margin-top: 6px;
					}}
					table.hotkeys td {{
						padding: 6px 8px;
						border-top: 1px solid #2a3142;
						vertical-align: top;
					}}
					.hk {{
						white-space: nowrap;
						color: #e6e9f2;
						font-weight: 600;
					}}
					.desc {{
						color: #cfd6e6;
					}}
				</style>
			</head>
			<body>
				<div class="pageTitle">{title}</div>
				{''.join(cards)}
			</body>
			</html>
			"""

	def _render_hotkeys_table_html(self):
			# Put your hotkeys in data so it's easy to maintain.
			rows = [
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

			trs = []
			for hk, desc in rows:
					trs.append(f"<tr><td class='hk'>{hk}</td><td class='desc'>{desc}</td></tr>")

			return f"""
				<table class="hotkeys">
					{''.join(trs)}
				</table>
			"""

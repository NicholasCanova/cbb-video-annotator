from enum import IntEnum
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QHBoxLayout
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

from utils.event_class import Event, ms_to_time


class Step(IntEnum):
	FIRST = 1
	SECOND = 2
	THIRD = 3


class EventSelectionWindow(QMainWindow):
	def __init__(self, main_window):
		super().__init__()

		self.main_window = main_window

		# Defining some variables of the window
		self.title_window = "Event Selection"

		# Setting the window appropriately
		self.setWindowTitle(self.title_window)
		self.set_position()

		self.palette_main_window = self.palette()
		self.palette_main_window.setColor(QPalette.Window, Qt.black)

		# Initiate the sub-widgets
		self.init_window()

	def init_window(self):
		# Allow the code to be run from any working directory
		base = Path(__file__).resolve().parent

		self.labels = self._read_labels(base / "../config/classes.txt")
		self.second_labels = self._read_labels(base / "../config/second_classes.txt")
		self.third_labels = self._read_labels(base / "../config/third_classes.txt")

		self.list_widget = QListWidget()
		self.list_widget_second = QListWidget()
		self.list_widget_third = QListWidget()

		for item_nbr, element in enumerate(self.labels):
			self.list_widget.insertItem(item_nbr, element)
		for item_nbr, element in enumerate(self.second_labels):
			self.list_widget_second.insertItem(item_nbr, element)
		for item_nbr, element in enumerate(self.third_labels):
			self.list_widget_third.insertItem(item_nbr, element)

		# Layout the different widgets
		central_display = QWidget(self)
		self.setCentralWidget(central_display)

		final_layout = QHBoxLayout()
		final_layout.addWidget(self.list_widget)
		final_layout.addWidget(self.list_widget_second)
		final_layout.addWidget(self.list_widget_third)

		central_display.setLayout(final_layout)

		self.step = Step.FIRST
		self.first_label = None
		self.second_label = None

		self._ensure_selected(self.list_widget)
		self.list_widget.setFocus()

	def _read_labels(self, path: Path):
		if not path.exists():
			return []
		return [l.strip() for l in path.read_text().splitlines() if l.strip()]

	def set_position(self):
		x = self.main_window.pos().x() + self.main_window.frameGeometry().width() // 4
		y = self.main_window.pos().y() + self.main_window.frameGeometry().height() // 4
		w = self.main_window.frameGeometry().width() // 2
		h = self.main_window.frameGeometry().height() // 2
		self.setGeometry(x, y, w, h)

	def keyPressEvent(self, event):
		key = event.key()

		if key in (Qt.Key_Return, Qt.Key_Enter):
			self._advance()
			return

		if key == Qt.Key_Backspace:
			self._back()
			return

		if key == Qt.Key_Escape:
			self._reset_and_close()
			return

		super().keyPressEvent(event)

	def _advance(self):
		if self.step == Step.FIRST:
			item = self.list_widget.currentItem()
			if not item:
				self._ensure_selected(self.list_widget)
				return

			self.first_label = item.text()
			self.step = Step.SECOND
			self._enter_step(self.list_widget_second)

		elif self.step == Step.SECOND:
			item = self.list_widget_second.currentItem()
			if not item:
				self._ensure_selected(self.list_widget_second)
				return

			self.second_label = item.text()
			self.step = Step.THIRD
			self._enter_step(self.list_widget_third)

		elif self.step == Step.THIRD:
			item = self.list_widget_third.currentItem()
			if not item:
				self._ensure_selected(self.list_widget_third)
				return

			position = self.main_window.media_player.media_player.position()

			if self.main_window.editing_event and self.main_window.edit_event_obj:
				self.main_window.list_manager.delete_event(self.main_window.edit_event_obj)

			self.main_window.list_manager.add_event(Event(
				self.first_label,
				self.main_window.half,
				ms_to_time(position),
				self.second_label,
				position,
				item.text(),
				self.main_window.position_to_frame(position)
			))

			self.main_window.list_display.display_list()

			path_label = self.main_window.media_player.get_last_label_file()
			self.main_window.list_manager.save_file(path_label, self.main_window.half)

			if self.main_window.editing_event:
				self.main_window._end_edit_event()

			self._reset_and_close()

	def _back(self):
		if self.step == Step.THIRD:
			self.step = Step.SECOND
			self.list_widget_third.setCurrentRow(-1)
			self._enter_step(self.list_widget_second)
			return

		if self.step == Step.SECOND:
			self.step = Step.FIRST
			self.list_widget_second.setCurrentRow(-1)
			self.second_label = None
			self._enter_step(self.list_widget)
			return

	def _enter_step(self, list_widget):
		self._ensure_selected(list_widget)
		list_widget.setFocus()

	def _ensure_selected(self, list_widget):
		if list_widget is None:
			return

		if list_widget.count() <= 0:
			return

		if list_widget.currentRow() < 0:
			list_widget.setCurrentRow(0)

	def _match_and_select(self, list_widget, target_text):
		target = (target_text or "").strip().lower()
		if not target:
			return None

		for idx in range(list_widget.count()):
			item = list_widget.item(idx)
			if item and item.text().strip().lower() == target:
				list_widget.setCurrentRow(idx)
				return item.text()

		return None

	def _reset_and_close(self):
		self.step = Step.FIRST
		self.first_label = None
		self.second_label = None

		# Clear selections more forcefully
		self.list_widget.clearSelection()
		self.list_widget_second.clearSelection()
		self.list_widget_third.clearSelection()

		self.list_widget.setCurrentRow(-1)
		self.list_widget_second.setCurrentRow(-1)
		self.list_widget_third.setCurrentRow(-1)

		# Drop focus off the lists
		self.list_widget.clearFocus()
		self.list_widget_second.clearFocus()
		self.list_widget_third.clearFocus()

		self.hide()
		self.main_window.setFocus()

	def preselect_first_label(self, label: str):
		target = (label or "").strip().lower()
		if not target:
			return False

		for i in range(self.list_widget.count()):
			item = self.list_widget.item(i)
			if item and item.text().strip().lower() == target:
				self.list_widget.setCurrentRow(i)
				self.first_label = item.text()
				self.step = Step.SECOND
				self.second_label = None
				self._enter_step(self.list_widget_second)
				return True

		return False

	def preselect_event(self, event):
		if not event:
			return False

		if not self.preselect_first_label(event.label):
			return False

		second_match = self._match_and_select(self.list_widget_second, event.team)
		if second_match:
			self.second_label = second_match
			self.step = Step.THIRD
			self._enter_step(self.list_widget_third)
			self._match_and_select(self.list_widget_third, event.visibility)
		else:
			self.step = Step.SECOND

		return True

from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QListWidget, QHBoxLayout
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt
from utils.event_class import Event, ms_to_time

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

		# Read the available labels
		self.labels = list()
		with open('../config/classes.txt') as file:
			for cnt, line in enumerate(file):
				self.labels.append(line.rstrip())

		# Read the available second labels
		self.second_labels = list()
		with open('../config/second_classes.txt') as file:
			for cnt, line in enumerate(file):
				self.second_labels.append(line.rstrip())

		# Read the available third labels
		self.third_labels = list()
		with open('../config/third_classes.txt') as file:
			for cnt, line in enumerate(file):
				self.third_labels.append(line.rstrip())

		self.list_widget = QListWidget()
		self.list_widget.clicked.connect(self.clicked)

		for item_nbr, element in enumerate(self.labels):
			self.list_widget.insertItem(item_nbr,element)

		self.list_widget_second = QListWidget()
		self.list_widget_second.clicked.connect(self.clicked)

		for item_nbr, element in enumerate(self.second_labels):
			self.list_widget_second.insertItem(item_nbr,element)

		self.list_widget_third = QListWidget()
		self.list_widget_third.clicked.connect(self.clicked)

		for item_nbr, element in enumerate(self.third_labels):
			self.list_widget_third.insertItem(item_nbr,element)

		# Layout the different widgets
		central_display = QWidget(self)
		self.setCentralWidget(central_display)
		final_layout = QHBoxLayout()
		final_layout.addWidget(self.list_widget)
		final_layout.addWidget(self.list_widget_second)
		final_layout.addWidget(self.list_widget_third)
		central_display.setLayout(final_layout)

		self.to_second = False
		self.to_third = False
		self.first_label = None
		self.second_label = None

	def clicked(self, qmodelindex):
		print("clicked")

	def set_position(self):
		self.xpos_window = self.main_window.pos().x()+self.main_window.frameGeometry().width()//4
		self.ypos_window = self.main_window.pos().y()+self.main_window.frameGeometry().height()//4
		self.width_window = self.main_window.frameGeometry().width()//2
		self.height_window = self.main_window.frameGeometry().height()//2
		self.setGeometry(self.xpos_window, self.ypos_window, self.width_window, self.height_window)

	def keyPressEvent(self, event):

		if event.key() == Qt.Key_Return:
			if not self.to_second and not self.to_third:
				first_item = self.list_widget.currentItem()
				if not first_item:
					return
				self.first_label = first_item.text()
				self.to_second = True
				self._focus_and_select(self.list_widget_second)
			elif self.to_second:
				second_item = self.list_widget_second.currentItem()
				if not second_item:
					return
				self.second_label = second_item.text()
				self.to_second = False
				self.to_third = True
				self._focus_and_select(self.list_widget_third)
			elif self.to_third:
				third_item = self.list_widget_third.currentItem()
				if not third_item:
					return
				position = self.main_window.media_player.media_player.position()
				self.main_window.list_manager.add_event(Event(
					self.first_label,
					self.main_window.half,
					ms_to_time(position),
					self.second_label,
					position,
					third_item.text(),
				))
				self.main_window.list_display.display_list(self.main_window.list_manager.create_text_list())
				self.first_label = None
				self.second_label = None
				self.to_third = False
				path_label = self.main_window.media_player.get_last_label_file()
				self.main_window.list_manager.save_file(path_label, self.main_window.half)
				self.hide()
				self.list_widget_second.setCurrentRow(-1)
				self.list_widget_third.setCurrentRow(-1)
				self.main_window.setFocus()

		# Move back a column in the selection with backspace
		if event.key() == Qt.Key_Backspace:
			self._step_back_selection()

		if event.key() == Qt.Key_Escape:
			self.to_second=False
			self.to_third=False
			self.first_label = None
			self.second_label = None
			self.list_widget_second.setCurrentRow(-1)
			self.list_widget_third.setCurrentRow(-1)
			self.hide()
			self.main_window.setFocus()

	def preselect_first_label(self, label: str):
		"""
		Select the given label in the first list (case-insensitive)
		and continue directly with the second list.
		"""
		target = (label or "").strip().lower()
		if not target:
			return False

		for i in range(self.list_widget.count()):
			item = self.list_widget.item(i)
			if item and item.text().strip().lower() == target:
				self.list_widget.setCurrentRow(i)
				self.first_label = item.text()
				self.to_second = True
				self.to_third = False
				self.second_label = None

				self._focus_and_select(self.list_widget_second)
				return True

		return False

	def _step_back_selection(self):
		if self.to_third:
			self.to_third = False
			self.list_widget_third.setCurrentRow(-1)
			self._focus_and_select(self.list_widget_second, self.second_label)
			return True

		if self.to_second:
			self.to_second = False
			self.list_widget_second.setCurrentRow(-1)
			self._focus_and_select(self.list_widget, self.first_label)
			self.second_label = None
			return True

		return False

	def _focus_and_select(self, list_widget, preferred_text=None):
		if not list_widget:
			return

		if preferred_text and self._select_row_by_text(list_widget, preferred_text):
			pass
		elif list_widget.currentRow() < 0 and list_widget.count() > 0:
			list_widget.setCurrentRow(0)

		list_widget.setFocus()

	def _select_row_by_text(self, list_widget, text):
		target = (text or "").strip().lower()
		if not target:
			return False

		for i in range(list_widget.count()):
			item = list_widget.item(i)
			if item and item.text().strip().lower() == target:
				list_widget.setCurrentRow(i)
				return True

		return False
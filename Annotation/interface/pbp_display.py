import os
from bisect import bisect_right

from PyQt5.QtWidgets import (
	QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
	QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt

_COLUMNS = ["frame_id", "periodIdx", "clock", "shotClock", "actionType", "subType", "qualifiers", "success", "score1", "score2"]
_HEADERS = ["Frame", "Period", "Clock", "Shot Clock", "Action", "Subtype", "Qualifiers", "Success", "Home", "Away"]

_CENTER = Qt.AlignCenter
_LEFT   = Qt.AlignLeft | Qt.AlignVCenter


class PBPDisplay(QWidget):

	def __init__(self, main_window):
		super().__init__()
		self.main_window = main_window
		self._frame_ids = []
		self._loaded = False

		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 4, 0, 0)

		self.table = QTableWidget(0, len(_COLUMNS))  # column count set from _COLUMNS
		self.table.setHorizontalHeaderLabels(_HEADERS)
		self.table.verticalHeader().setVisible(False)
		self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.table.setSelectionMode(QAbstractItemView.SingleSelection)
		self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.table.setShowGrid(False)
		self.table.verticalHeader().setDefaultSectionSize(22)
		self.table.setFocusPolicy(Qt.NoFocus)

		h = self.table.horizontalHeader()
		_fixed = QHeaderView.Fixed
		_stretch = QHeaderView.Stretch
		_widths = {
			"frame_id":   (65,  _fixed),
			"periodIdx":  (50,  _fixed),
			"clock":      (65,  _fixed),
			"shotClock":  (75,  _fixed),
			"actionType": (None, _stretch),
			"subType":    (110, _fixed),
			"qualifiers": (110, _fixed),
			"success":    (55,  _fixed),
			"score1":     (55,  _fixed),
			"score2":     (55,  _fixed),
		}
		for i, col in enumerate(_COLUMNS):
			width, mode = _widths[col]
			h.setSectionResizeMode(i, mode)
			if width:
				self.table.setColumnWidth(i, width)

		self.table.cellClicked.connect(self._on_cell_clicked)
		layout.addWidget(self.table)

		self.setFixedHeight(160)
		self.hide()

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------

	def load_pbp(self, video_path):
		"""Load pbp.csv from the same folder as video_path. Hides itself if not found."""
		self._frame_ids = []
		self._loaded = False
		self.table.setRowCount(0)

		pbp_path = os.path.join(os.path.dirname(video_path), "pbp.csv")
		if not os.path.isfile(pbp_path):
			self.hide()
			return

		try:
			import pandas as pd
			df = pd.read_csv(pbp_path)
		except Exception as e:
			print(f"[PBP] Error loading CSV: {e}")
			self.hide()
			return

		if "frame_id" not in df.columns:
			print(f"[PBP] Missing 'frame_id' column. Available: {list(df.columns)}")
			self.hide()
			return

		# Sort by frame_id so bisect works correctly
		df = df.sort_values("frame_id").reset_index(drop=True)

		# Add any missing display columns as empty
		for col in _COLUMNS:
			if col not in df.columns:
				df[col] = ""

		self._frame_ids = df["frame_id"].fillna(-1).astype(int).tolist()

		self.table.setRowCount(len(df))
		for row_idx, row in df.iterrows():
			for col_idx, col in enumerate(_COLUMNS):
				val = row[col]
				text = "" if pd.isna(val) else str(val)
				align = _CENTER if col not in ("actionType", "subType", "qualifiers") else _LEFT
				item = QTableWidgetItem(text)
				item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
				item.setTextAlignment(align)
				self.table.setItem(row_idx, col_idx, item)

		self._loaded = True
		self.show()

	def update_frame(self, frame_number):
		"""Highlight and scroll to the most recent PBP row for the given frame."""
		if not self._loaded or not self._frame_ids:
			return

		idx = bisect_right(self._frame_ids, frame_number) - 1
		if idx < 0:
			return

		self.table.selectRow(idx)
		self.table.scrollTo(
			self.table.model().index(idx, 0),
			QAbstractItemView.PositionAtCenter,
		)

	# ------------------------------------------------------------------
	# Internal
	# ------------------------------------------------------------------

	def _on_cell_clicked(self, row, _col):
		if not self._loaded or row >= len(self._frame_ids):
			return

		frame_id = self._frame_ids[row]  # already resolved from frame_id column
		if frame_id < 0:
			return

		frame_duration = self.main_window.frame_duration_ms or 40.0
		self.main_window.media_player.set_position(int(frame_id * frame_duration))
		self.main_window.setFocus()

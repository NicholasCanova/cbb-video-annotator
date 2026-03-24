import os
import cv2

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
	QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
	QProgressBar, QPushButton, QFileDialog, QMessageBox,
	QLineEdit, QFrame,
)


# Badge dimensions match the live overlay (300×26 px, rgba(255,0,0,204), black text)
_BADGE_W = 300
_BADGE_H = 26
_BADGE_SPACING = 2
_BADGE_ALPHA = 204 / 255.0
_BADGE_COLOR_BGR = (0, 0, 255)
_TEXT_COLOR_BGR = (0, 0, 0)


def _get_visible_texts(pos_ms, sorted_events, visibility_ms=2000):
	"""Return badge strings for events visible at pos_ms.

	Uses event.position (milliseconds) to match the live overlay exactly,
	avoiding frame-count drift on variable-frame-rate videos.
	"""
	texts = []
	for event in sorted_events:
		ep = getattr(event, "position", None)
		if ep is None:
			continue
		if ep > pos_ms + visibility_ms:
			break
		if ep <= pos_ms < ep + visibility_ms:
			label = event.label or "Event"
			subtype = getattr(event, "subType", None)
			if subtype and subtype != "None":
				texts.append(f"{label} ({subtype})")
			else:
				texts.append(label)
	return texts


def _draw_badges(frame, texts, video_width):
	if not texts:
		return frame

	x_start = max(0, (video_width - _BADGE_W) // 2)
	x_end = x_start + _BADGE_W
	font = cv2.FONT_HERSHEY_SIMPLEX
	font_scale = 0.52
	font_thickness = 1

	for i, text in enumerate(texts):
		y_start = 5 + i * (_BADGE_H + _BADGE_SPACING)
		y_end = y_start + _BADGE_H

		overlay = frame.copy()
		cv2.rectangle(overlay, (x_start, y_start), (x_end, y_end), _BADGE_COLOR_BGR, -1)
		cv2.addWeighted(overlay, _BADGE_ALPHA, frame, 1.0 - _BADGE_ALPHA, 0, frame)

		text_x = x_start + 10
		text_y = y_start + int(_BADGE_H * 0.68)
		cv2.putText(frame, text, (text_x, text_y), font, font_scale,
		            _TEXT_COLOR_BGR, font_thickness, cv2.LINE_AA)

	return frame


class ExportThread(QThread):
	progress = pyqtSignal(int, int)
	finished = pyqtSignal(bool, str)

	def __init__(self, video_path, output_path, events,
	             start_frame=None, end_frame=None):
		super().__init__()
		self.video_path = video_path
		self.output_path = output_path
		self.events = events
		self.start_frame = start_frame  # None = beginning
		self.end_frame = end_frame      # None = end of video
		self._cancelled = False

	def cancel(self):
		self._cancelled = True

	def run(self):
		cap = cv2.VideoCapture(self.video_path)
		if not cap.isOpened():
			self.finished.emit(False, "Could not open the source video.")
			return

		fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
		total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

		# Convert frame bounds to milliseconds for accurate seeking/stopping
		ms_per_frame = 1000.0 / fps
		start_frame = self.start_frame if self.start_frame is not None else 0
		end_frame = self.end_frame if self.end_frame is not None else total_frames
		start_ms = start_frame * ms_per_frame
		end_ms = end_frame * ms_per_frame
		clip_frames = max(1, end_frame - start_frame)

		if start_frame > 0:
			cap.set(cv2.CAP_PROP_POS_MSEC, start_ms)

		writer = None
		for fourcc_str in ("avc1", "mp4v"):
			fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
			writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
			if writer.isOpened():
				break

		if not writer or not writer.isOpened():
			cap.release()
			self.finished.emit(False, "Could not create the output video file.")
			return

		# Sort by position (ms) — used for ms-accurate event visibility
		sorted_events = sorted(
			[e for e in self.events if getattr(e, "position", None) is not None],
			key=lambda e: e.position,
		)

		frames_written = 0
		while True:
			if self._cancelled:
				writer.release()
				cap.release()
				try:
					os.remove(self.output_path)
				except OSError:
					pass
				self.finished.emit(False, "Export cancelled.")
				return

			# Read actual timestamp before consuming the frame
			pos_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
			if pos_ms >= end_ms:
				break

			ret, frame = cap.read()
			if not ret:
				break

			texts = _get_visible_texts(pos_ms, sorted_events)
			if texts:
				frame = _draw_badges(frame, texts, width)

			writer.write(frame)
			frames_written += 1

			if frames_written % 60 == 0:
				self.progress.emit(frames_written, clip_frames)

		writer.release()
		cap.release()
		self.finished.emit(True, self.output_path)


class ExportSetupDialog(QDialog):
	"""Collects optional frame range before export starts."""

	def __init__(self, parent, total_frames):
		super().__init__(parent)
		self._total_frames = total_frames
		self.setWindowTitle("Export Annotated Video")
		self.setModal(True)
		self.setMinimumWidth(320)

		layout = QVBoxLayout(self)
		layout.setSpacing(12)

		layout.addWidget(QLabel("Frame range (edit to export a specific clip):"))

		form = QFormLayout()
		form.setSpacing(8)

		self._start_edit = QLineEdit(str(0))
		self._start_edit.setMinimumWidth(100)
		form.addRow("Start frame:", self._start_edit)

		self._end_edit = QLineEdit(str(total_frames))
		self._end_edit.setMinimumWidth(100)
		form.addRow("End frame:", self._end_edit)

		layout.addLayout(form)

		btn_row = QHBoxLayout()
		btn_row.addStretch(1)
		cancel_btn = QPushButton("Cancel")
		cancel_btn.clicked.connect(self.reject)
		export_btn = QPushButton("Choose Output File…")
		export_btn.setDefault(True)
		export_btn.clicked.connect(self._validate_and_accept)
		btn_row.addWidget(cancel_btn)
		btn_row.addWidget(export_btn)
		layout.addLayout(btn_row)

	def _validate_and_accept(self):
		try:
			start = int(self._start_edit.text())
			end = int(self._end_edit.text())
		except ValueError:
			QMessageBox.warning(self, "Invalid Input", "Start and end frames must be whole numbers.")
			return
		if start < 0 or end > self._total_frames or start >= end:
			QMessageBox.warning(self, "Invalid Range",
			                    f"Range must be between 0 and {self._total_frames}, with start < end.")
			return
		self.accept()

	def start_frame(self):
		return int(self._start_edit.text())

	def end_frame(self):
		return int(self._end_edit.text())


class ExportProgressDialog(QDialog):
	def __init__(self, parent, video_path, output_path, events,
	             start_frame, end_frame):
		super().__init__(parent)
		self.setWindowTitle("Exporting Video")
		self.setModal(True)
		self.setMinimumWidth(420)

		layout = QVBoxLayout(self)
		layout.setSpacing(12)

		self._status = QLabel("Rendering frames…")
		layout.addWidget(self._status)

		self._bar = QProgressBar()
		self._bar.setRange(0, 100)
		self._bar.setValue(0)
		layout.addWidget(self._bar)

		btn_row = QHBoxLayout()
		btn_row.addStretch(1)
		self._cancel_btn = QPushButton("Cancel")
		self._cancel_btn.clicked.connect(self._cancel)
		btn_row.addWidget(self._cancel_btn)
		layout.addLayout(btn_row)

		self._thread = ExportThread(
			video_path, output_path, events,
			start_frame=start_frame, end_frame=end_frame,
		)
		self._thread.progress.connect(self._on_progress)
		self._thread.finished.connect(self._on_finished)
		self._thread.start()

	def _cancel(self):
		self._cancel_btn.setEnabled(False)
		self._status.setText("Cancelling…")
		self._thread.cancel()

	def _on_progress(self, done, total):
		pct = int(100 * done / total) if total else 0
		self._bar.setValue(pct)
		self._status.setText(f"Rendering… {done:,} / {total:,} frames ({pct}%)")

	def _on_finished(self, success, message):
		self._thread.wait()
		self.accept()
		if success:
			QMessageBox.information(
				self.parent(), "Export Complete",
				f"Video saved to:\n{message}",
			)
		elif message != "Export cancelled.":
			QMessageBox.warning(self.parent(), "Export Failed", message)


def start_export(media_player):
	video_path = getattr(media_player, "_current_video_path", None)
	if not video_path:
		QMessageBox.warning(media_player, "No Video", "Open a video before exporting.")
		return

	events = list(getattr(media_player.main_window.list_manager, "event_list", []))
	if not events:
		QMessageBox.information(media_player, "No Events",
		                        "There are no annotated events to render.")
		return

	# Read total frame count for the spinbox bounds
	cap = cv2.VideoCapture(video_path)
	total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.isOpened() else 0
	cap.release()

	# Step 1: frame range dialog
	setup = ExportSetupDialog(media_player, total_frames)
	if setup.exec_() != QDialog.Accepted:
		return

	start_frame = setup.start_frame()
	end_frame = setup.end_frame()

	# Step 2: choose output path
	base, ext = os.path.splitext(video_path)
	default_out = base + "_annotated" + (ext or ".mp4")
	out_path, _ = QFileDialog.getSaveFileName(
		media_player, "Save Annotated Video", default_out,
		"Video Files (*.mp4 *.mov *.avi)",
	)
	if not out_path:
		return

	# Step 3: progress dialog
	dlg = ExportProgressDialog(
		media_player, video_path, out_path, events,
		start_frame, end_frame,
	)
	dlg.exec_()

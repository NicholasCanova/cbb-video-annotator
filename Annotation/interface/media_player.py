# Adapted from https://codeloop.org/python-how-to-create-media-player-in-pyqt5/
import os
from PyQt5.QtWidgets import QWidget, QPushButton, QStyle, QSlider, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaMetaData
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl

class MediaPlayer(QWidget):

	def __init__(self, main_window):

		# Defining the elements of the media player
		super().__init__()

		self.main_window = main_window

		# Media Player
		self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
		self.media_player.setNotifyInterval(33)

		# Video Widget
		self.video_widget = QVideoWidget()
		
		# Create container widget for video with overlay
		self.video_container = QWidget()
		video_container_layout = QVBoxLayout()
		video_container_layout.setContentsMargins(0, 0, 0, 0)
		video_container_layout.addWidget(self.video_widget)
		self.video_container.setLayout(video_container_layout)
		
		# Create overlay label for displaying position and editing mode
		self.overlay_label = QLabel(self.video_container)
		# Initial stylesheet (black background, will be updated dynamically)
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
		self.overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Allow clicks to pass through
		self.overlay_label.raise_()  # Raise above video widget
		self.overlay_label.hide()  # Hide until video is loaded

		# Button to open a new file
		self.open_file_button = QPushButton('Open video')
		self.open_file_button.clicked.connect(self.open_file)

		# Button for playing the video
		self.play_button = QPushButton()
		self.play_button.setEnabled(False)
		self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.play_button.clicked.connect(self.play_video)

		# Button for the slider
		self.slider = QSlider(Qt.Horizontal)
		self.slider.setRange(0,0)
		self.slider.sliderMoved.connect(self.set_position)

		#create hbox layout
		hboxLayout = QHBoxLayout()
		hboxLayout.setContentsMargins(0,0,0,0)

		#set widgets to the hbox layout
		hboxLayout.addWidget(self.open_file_button)
		hboxLayout.addWidget(self.play_button)
		hboxLayout.addWidget(self.slider)

		#create vbox layout
		self.layout = QVBoxLayout()
		self.layout.addWidget(self.video_container)
		self.layout.addLayout(hboxLayout)

		self.media_player.setVideoOutput(self.video_widget)

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
			self.overlay_label.show() 
			self.update_overlay()
			filpath = os.path.basename(filename)
			self.main_window.half = int(filpath[0])

			self.path_label = os.path.dirname(filename) + "/Labels.json"
			self.path_label = self.get_last_label_file()
			self.main_window.list_manager.create_list_from_json(self.path_label, self.main_window.half)
			self.main_window.list_display.display_list(self.main_window.list_manager.create_text_list())

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
			self.media_player.play()

	def mediastate_changed(self, state):
		if self.media_player.state() == QMediaPlayer.PlayingState:
			self.play_button.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPause)

			)

		else:
			self.play_button.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPlay)

			)

	def position_changed(self, position):
		self.slider.setValue(position)
		self.update_overlay()

	def duration_changed(self, duration):
		self.slider.setRange(0, duration)

	def set_position(self, position):
		self.media_player.setPosition(position)
	
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
			bg_color = "rgba(255, 0, 0, 180)" # red
		else:
			overlay_text = frame_str
			bg_color = "rgba(0, 0, 0, 180)" # black
		
		# Update stylesheet with appropriate background color
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
		
		# Resize and position overlay label
		self.overlay_label.adjustSize()
		self.overlay_label.raise_()  # Ensure it's on top

	def handle_errors(self):
		self.play_button.setEnabled(False)
		print("Error: " + self.media_player.errorString())

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


import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSlider
)

from core.player import AudioPlayer


def format_time(ms):
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


class PlayerWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.audio = AudioPlayer()
        self.setWindowTitle("Music Player")
        self.resize(800, 500)

        welcome_label = QLabel(f"Welcome, {username}")
        logout_button = QPushButton("Log out")

        top_bar = QHBoxLayout()
        top_bar.addWidget(welcome_label)
        top_bar.addStretch()
        top_bar.addWidget(logout_button)

        self.now_playing_label = QLabel("No track loaded")
        self.now_playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.elapsed_label = QLabel("0:00")
        self.total_label = QLabel("0:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)

        seek_row = QHBoxLayout()
        seek_row.addWidget(self.elapsed_label)
        seek_row.addWidget(self.seek_slider, stretch=1)
        seek_row.addWidget(self.total_label)

        open_button = QPushButton("Open file")
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(open_button)
        controls.addWidget(play_button)
        controls.addWidget(pause_button)
        controls.addWidget(stop_button)
        controls.addStretch()

        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)

        volume_row = QHBoxLayout()
        volume_row.addStretch()
        volume_row.addWidget(self.mute_button)
        volume_row.addWidget(self.volume_slider)
        volume_row.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addStretch()
        layout.addWidget(self.now_playing_label)
        layout.addLayout(seek_row)
        layout.addLayout(controls)
        layout.addLayout(volume_row)
        layout.addStretch()
        self.setLayout(layout)

        logout_button.clicked.connect(self.logout_requested.emit)
        open_button.clicked.connect(self.open_file)
        play_button.clicked.connect(self.audio.play)
        pause_button.clicked.connect(self.audio.pause)
        stop_button.clicked.connect(self.audio.stop)

        self.audio.position_changed.connect(self.on_position_changed)
        self.audio.duration_changed.connect(self.on_duration_changed)
        self.seek_slider.sliderMoved.connect(self.audio.seek)
        self.volume_slider.valueChanged.connect(self.audio.set_volume)
        self.mute_button.toggled.connect(self.audio.set_muted)

    def on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.elapsed_label.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)
        self.total_label.setText(format_time(duration))

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open audio file",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;All Files (*)",
        )
        if not file_path:
            return
        self.audio.load(file_path)
        self.now_playing_label.setText(os.path.basename(file_path))
        self.audio.play()

    def closeEvent(self, event):
        self.audio.stop()
        super().closeEvent(event)
import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSlider, QListWidget, QStyle
)

from core.player import AudioPlayer
from core.library import read_track, scan_folder


def format_time(ms):
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(),
                int(event.position().x()), self.width(),
            )
            self.setValue(value)
            self.sliderMoved.emit(value)
        super().mousePressEvent(event)

class PlayerWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.audio = AudioPlayer()
        self.tracks = []
        self.setWindowTitle("Music Player")
        self.resize(800, 500)

        welcome_label = QLabel(f"Welcome, {username}")
        logout_button = QPushButton("Log out")

        top_bar = QHBoxLayout()
        top_bar.addWidget(welcome_label)
        top_bar.addStretch()
        top_bar.addWidget(logout_button)

        self.track_list = QListWidget()

        self.now_playing_label = QLabel("No track loaded")
        self.now_playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.elapsed_label = QLabel("0:00")
        self.total_label = QLabel("0:00")
        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)

        seek_row = QHBoxLayout()
        seek_row.addWidget(self.elapsed_label)
        seek_row.addWidget(self.seek_slider, stretch=1)
        seek_row.addWidget(self.total_label)

        add_files_button = QPushButton("Add files")
        add_folder_button = QPushButton("Add folder")
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")

        controls = QHBoxLayout()
        controls.addWidget(add_files_button)
        controls.addWidget(add_folder_button)
        controls.addStretch()
        controls.addWidget(play_button)
        controls.addWidget(pause_button)
        controls.addWidget(stop_button)

        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)

        volume_row = QHBoxLayout()
        volume_row.addStretch()
        volume_row.addWidget(self.mute_button)
        volume_row.addWidget(self.volume_slider)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.track_list, stretch=1)
        layout.addWidget(self.now_playing_label)
        layout.addLayout(seek_row)
        layout.addLayout(controls)
        layout.addLayout(volume_row)
        self.setLayout(layout)

        logout_button.clicked.connect(self.logout_requested.emit)
        add_files_button.clicked.connect(self.add_files)
        add_folder_button.clicked.connect(self.add_folder)
        play_button.clicked.connect(self.audio.play)
        pause_button.clicked.connect(self.audio.pause)
        stop_button.clicked.connect(self.audio.stop)

        self.track_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.audio.position_changed.connect(self.on_position_changed)
        self.audio.duration_changed.connect(self.on_duration_changed)
        self.seek_slider.sliderMoved.connect(self.audio.seek)
        self.volume_slider.valueChanged.connect(self.audio.set_volume)
        self.mute_button.toggled.connect(self.audio.set_muted)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add audio files",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;All Files (*)",
        )
        self.add_tracks(paths)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add folder")
        if folder:
            self.add_tracks(scan_folder(folder))

    def add_tracks(self, paths):
        known = {track["path"] for track in self.tracks}
        for path in paths:
            if path in known:
                continue
            track = read_track(path)
            self.tracks.append(track)
            duration_text = format_time(track["duration"] * 1000)
            self.track_list.addItem(
                f"{track['title']} - {track['artist']}   [{duration_text}]"
            )

    def on_item_double_clicked(self, item):
        self.play_track(self.track_list.row(item))

    def play_track(self, index):
        track = self.tracks[index]
        self.audio.load(track["path"])
        self.now_playing_label.setText(f"{track['title']} - {track['artist']}")
        self.audio.play()

    def on_position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.elapsed_label.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)
        self.total_label.setText(format_time(duration))

    def closeEvent(self, event):
        self.audio.stop()
        super().closeEvent(event)
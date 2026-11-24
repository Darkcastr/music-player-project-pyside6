import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
)

from core.player import AudioPlayer                      


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

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addStretch()
        layout.addWidget(self.now_playing_label)
        layout.addLayout(controls)
        layout.addStretch()
        self.setLayout(layout)

        logout_button.clicked.connect(self.logout_requested.emit)
        open_button.clicked.connect(self.open_file)      
        play_button.clicked.connect(self.audio.play)     
        pause_button.clicked.connect(self.audio.pause)   
        stop_button.clicked.connect(self.audio.stop)     

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
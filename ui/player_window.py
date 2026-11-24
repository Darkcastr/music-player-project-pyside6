from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


class PlayerWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("Music Player")
        self.resize(800, 500)

        welcome_label = QLabel(f"Welcome, {username}")
        logout_button = QPushButton("Log out")

        top_bar = QHBoxLayout()
        top_bar.addWidget(welcome_label)
        top_bar.addStretch()
        top_bar.addWidget(logout_button)

        placeholder = QLabel("Your music will appear here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(placeholder, stretch=1)
        self.setLayout(layout)

        logout_button.clicked.connect(self.logout_requested.emit)
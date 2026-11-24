from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
)

from database import verify_user


class LoginWindow(QWidget):
    login_successful = Signal(str)   
    register_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player - Login")
        self.setFixedSize(320, 280)

        title = QLabel("Welcome back")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.message_label = QLabel("")

        login_button = QPushButton("Login")
        register_button = QPushButton("Create account")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.message_label)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        self.setLayout(layout)

        login_button.clicked.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        register_button.clicked.connect(self.register_requested.emit)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        success, message = verify_user(username, password)

        if success:
            self.login_successful.emit(username.strip())
        else:
            self.message_label.setText(message)
            self.password_input.clear()
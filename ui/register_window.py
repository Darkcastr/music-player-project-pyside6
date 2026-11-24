from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
)

from database import register_user


class RegisterWindow(QWidget):
    account_created = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player - Create Account")
        self.setFixedSize(320, 340)

        title = QLabel("Create your account")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 6 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.message_label = QLabel("")

        create_button = QPushButton("Create account")
        back_button = QPushButton("Back to login")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_input)
        layout.addWidget(self.message_label)
        layout.addWidget(create_button)
        layout.addWidget(back_button)
        self.setLayout(layout)

        create_button.clicked.connect(self.handle_register)
        self.confirm_input.returnPressed.connect(self.handle_register)
        back_button.clicked.connect(self.back_requested.emit)

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if password != confirm:
            self.message_label.setText("Passwords do not match")
            return

        success, message = register_user(username, password)

        if success:
            self.account_created.emit()
        else:
            self.message_label.setText(message)

    def reset(self):
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.message_label.clear()

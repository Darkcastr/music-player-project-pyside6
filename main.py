import sys

from PySide6.QtWidgets import QApplication

from database import init_db
from ui.login_window import LoginWindow


def main():
    init_db()
    app = QApplication(sys.argv)

    login = LoginWindow()
    login.login_successful.connect(lambda username: print("Logged in as", username))
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
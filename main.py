import sys

from PySide6.QtWidgets import QApplication

from database import init_db
from ui.player_window import PlayerWindow
from ui.login_window import LoginWindow
from ui.register_window import RegisterWindow


def main():
    init_db()
    app = QApplication(sys.argv)

    login = LoginWindow()
    register = RegisterWindow()

    def show_register():
        login.hide()
        register.reset()
        register.show()

    def show_login(message=""):
        register.hide()
        login.message_label.setText(message)
        login.password_input.clear()
        login.show()

        login.register_requested.connect(show_register)
    register.back_requested.connect(show_login)
    register.account_created.connect(
        lambda: show_login("Account created. Please log in.")
    )

    player = None

    def show_player(username):
        nonlocal player
        login.hide()
        player = PlayerWindow(username)
        player.logout_requested.connect(handle_logout)
        player.show()

    def handle_logout():
        nonlocal player
        login.username_input.clear()
        show_login()
        player.close()
        player = None

    login.login_successful.connect(show_player)

    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
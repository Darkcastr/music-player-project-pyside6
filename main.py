import sys

from PySide6.QtWidgets import QApplication, QWidget
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Music Player")
window.show()
sys.exit(app.exec())
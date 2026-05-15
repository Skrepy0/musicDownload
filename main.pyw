import sys
from PySide6.QtWidgets import QApplication
from src.window import MusicDownloader

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MusicDownloader()
    win.show()
    sys.exit(app.exec())
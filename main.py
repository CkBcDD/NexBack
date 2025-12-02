import os
import sys

os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"

from PySide6.QtWidgets import QApplication

from src.nexback.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

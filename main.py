"""NexBack - Dual N-Back Cognitive Training Application.

A comprehensive Dual N-Back training application built with PySide6,
providing configurable cognitive training with adaptive difficulty,
performance tracking, and clinical mode support.
"""

import os
import sys

# Suppress Qt multimedia FFmpeg logging
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"

from PySide6.QtWidgets import QApplication

from src.nexback.ui.main_window import MainWindow


def main() -> None:
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

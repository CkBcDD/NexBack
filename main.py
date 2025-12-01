import os
import sys

# 抑制 Qt 多媒体 FFmpeg 后端的日志信息和警告
# 这是 Windows 上的已知问题，不影响功能
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"

from PyQt6.QtWidgets import QApplication

from src.nexback.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

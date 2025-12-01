from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtTextToSpeech import QTextToSpeech
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.nexback.core.engine import NBackEngine, ResponseType, StimulusType
from src.nexback.ui.grid_widget import GridWidget
from src.nexback.utils.config import GameConfig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexBack - Dual N-Back Trainer")
        self.resize(600, 700)

        # Config & Engine
        self.config = GameConfig()
        self.engine = NBackEngine(self.config)
        self.speech = QTextToSpeech()

        # UI Setup
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        self.lbl_score = QLabel("Score: 0")
        self.lbl_level = QLabel(f"N-Level: {self.config.n_level}")
        header_layout.addWidget(self.lbl_level)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_score)
        layout.addLayout(header_layout)

        # Grid
        self.grid = GridWidget()
        layout.addWidget(self.grid, alignment=Qt.AlignmentFlag.AlignCenter)

        # Feedback Area
        self.lbl_feedback = QLabel(
            "Press 'A' for Position Match | Press 'L' for Audio Match"
        )
        self.lbl_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_feedback.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(self.lbl_feedback)

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Session")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self.start_game)
        self.btn_stop.clicked.connect(self.stop_game)

        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        layout.addLayout(controls_layout)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

    def _connect_signals(self):
        self.engine.stimulus_presented.connect(self.on_stimulus)
        self.engine.feedback_generated.connect(self.on_feedback)
        self.engine.score_updated.connect(self.on_score)
        self.engine.progress_updated.connect(self.on_progress)
        self.engine.session_finished.connect(self.on_finished)

    def keyPressEvent(self, a0: QKeyEvent | None):
        if not self.engine.is_running:
            return
        if a0 is None:
            return

        if a0.key() == Qt.Key.Key_A:
            self.engine.submit_response(StimulusType.POSITION)
            self._flash_feedback("Position Checked", "#3498db")
        elif a0.key() == Qt.Key.Key_L:
            self.engine.submit_response(StimulusType.AUDIO)
            self._flash_feedback("Audio Checked", "#e74c3c")

    def start_game(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_score.setText("Score: 0")
        self.progress.setValue(0)
        self.engine.start_session()
        self.grid.setFocus()

    def stop_game(self):
        self.engine.stop_session()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.grid.clear()

    def on_stimulus(self, pos, audio_char):
        # Visual
        self.grid.highlight(pos)

        # Audio
        self.speech.say(audio_char)

        # Clear grid after stimulus duration (e.g., 1000ms)
        # The engine handles the trial timing (3000ms), but we want the visual to disappear earlier
        QTimer.singleShot(self.config.stimulus_duration_ms, self.grid.clear)

    def on_feedback(self, stim_type, response_type):
        msg = f"{stim_type.name}: {response_type.name}"
        color = "#2ecc71" if response_type == ResponseType.HIT else "#e74c3c"
        if response_type == ResponseType.FALSE_ALARM:
            color = "#e67e22"  # Orange
        elif response_type == ResponseType.MISS:
            color = "#95a5a6"  # Gray

        self._flash_feedback(msg, color)

    def _flash_feedback(self, text, color):
        self.lbl_feedback.setText(text)
        self.lbl_feedback.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color};"
        )
        # Reset after 1 sec
        QTimer.singleShot(
            1000,
            lambda: self.lbl_feedback.setStyleSheet("font-size: 14px; color: #555;"),
        )

    def on_score(self, score, total):
        self.lbl_score.setText(f"Score: {score}")

    def on_progress(self, current, total):
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def on_finished(self, stats):
        self.stop_game()

        # Calculate accuracy
        pos_stats = stats[StimulusType.POSITION]
        audio_stats = stats[StimulusType.AUDIO]

        msg = "Session Finished!\n\n"
        msg += "Position:\n"
        msg += f"  Hits: {pos_stats['hit']}\n"
        msg += f"  Misses: {pos_stats['miss']}\n"
        msg += f"  False Alarms: {pos_stats['false_alarm']}\n\n"
        msg += "Audio:\n"
        msg += f"  Hits: {audio_stats['hit']}\n"
        msg += f"  Misses: {audio_stats['miss']}\n"
        msg += f"  False Alarms: {audio_stats['false_alarm']}"

        QMessageBox.information(self, "Results", msg)

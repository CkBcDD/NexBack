from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.nexback.core.audio import AudioManager
from src.nexback.core.engine import NBackEngine, ResponseType, StimulusType
from src.nexback.core.storage import Storage
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
        self.storage = Storage()
        self.audio_manager = AudioManager()

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

        self.chk_clinical = QCheckBox("Clinical Mode")
        self.chk_clinical.toggled.connect(self.on_clinical_toggled)

        header_layout.addWidget(self.lbl_level)
        header_layout.addStretch()
        header_layout.addWidget(self.chk_clinical)
        header_layout.addWidget(self.lbl_score)
        layout.addLayout(header_layout)

        # Grid
        self.grid = GridWidget()
        layout.addWidget(self.grid, alignment=Qt.AlignmentFlag.AlignCenter)

        # Feedback Area
        self.lbl_instructions = QLabel(
            "Press 'A' for Position Match | Press 'L' for Audio Match"
        )
        self.lbl_instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_instructions.setStyleSheet("font-size: 14px; color: #888;")
        layout.addWidget(self.lbl_instructions)

        # Status Area
        status_layout = QHBoxLayout()

        self.lbl_pos_status = QLabel("Position: Waiting")
        self.lbl_pos_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pos_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )

        self.lbl_audio_status = QLabel("Audio: Waiting")
        self.lbl_audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_audio_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )

        status_layout.addWidget(self.lbl_pos_status)
        status_layout.addWidget(self.lbl_audio_status)
        layout.addLayout(status_layout)

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

    def on_clinical_toggled(self, checked):
        self.config.is_clinical_mode = checked
        if checked:
            self.config.scoring_method = self.config.scoring_method.CLINICAL
            # Set a fixed seed for reproducibility in clinical mode (demo purpose)
            # In a real app, this might come from a pre-defined list or user ID
            self.config.random_seed = 42
        else:
            self.config.scoring_method = self.config.scoring_method.STANDARD
            self.config.random_seed = None

        # Re-initialize RNG with new seed
        import random

        self.engine.rng = random.Random(self.config.random_seed)

    def keyPressEvent(self, a0: QKeyEvent | None):
        if not self.engine.is_running:
            return
        if a0 is None:
            return

        if a0.key() == Qt.Key.Key_A:
            self.engine.submit_response(StimulusType.POSITION)
        elif a0.key() == Qt.Key.Key_L:
            self.engine.submit_response(StimulusType.AUDIO)

    def start_game(self):
        self.btn_start.setEnabled(False)
        # In Clinical Mode, we might disable the Stop button to enforce session completion
        # But for safety/UX, we might just warn. For strict requirements:
        if self.config.is_clinical_mode:
            self.btn_stop.setEnabled(False)
        else:
            self.btn_stop.setEnabled(True)

        self.chk_clinical.setEnabled(False)  # Lock mode during session

        self.lbl_score.setText("Score: 0")
        self.lbl_pos_status.setText("Position: Waiting")
        self.lbl_pos_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )
        self.lbl_audio_status.setText("Audio: Waiting")
        self.lbl_audio_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )
        self.progress.setValue(0)
        self.engine.start_session()
        self.grid.setFocus()

    def stop_game(self):
        self.engine.stop_session()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.chk_clinical.setEnabled(True)  # Unlock mode

        self.grid.clear()
        self.lbl_pos_status.setText("Position: Waiting")
        self.lbl_pos_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )
        self.lbl_audio_status.setText("Audio: Waiting")
        self.lbl_audio_status.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #888;"
        )

    def on_stimulus(self, pos, audio_char):
        # Visual
        self.grid.highlight(pos)

        # Audio
        self.audio_manager.play(audio_char)

        # Clear grid after stimulus duration (e.g., 1000ms)
        # The engine handles the trial timing (3000ms), but we want the visual to disappear earlier
        QTimer.singleShot(self.config.stimulus_duration_ms, self.grid.clear)

    def on_feedback(self, stim_type, response_type):
        is_correct = response_type in [ResponseType.HIT, ResponseType.REJECTION]

        text = "Correct" if is_correct else "Incorrect"
        # Green for correct, Red for incorrect.
        color = "#2ecc71" if is_correct else "#e74c3c"

        label = (
            self.lbl_pos_status
            if stim_type == StimulusType.POSITION
            else self.lbl_audio_status
        )
        prefix = "Position" if stim_type == StimulusType.POSITION else "Audio"

        label.setText(f"{prefix}: {text}")
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

    def on_score(self, score, total):
        self.lbl_score.setText(f"Score: {score}")

    def on_progress(self, current, total):
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def on_finished(self, result):
        self.stop_game()

        stats = result["stats"]
        final_score = result["final_score"]
        promotion = result["promotion"]
        demotion = result["demotion"]
        new_level = result["n_level"]

        # Calculate accuracy
        pos_stats = stats[StimulusType.POSITION]
        audio_stats = stats[StimulusType.AUDIO]

        msg = "Session Finished!\n\n"
        msg += f"Final Score: {final_score:.2%}\n"
        if promotion:
            msg += f"Result: PROMOTED to N-Level {new_level}!\n\n"
        elif demotion:
            msg += f"Result: DEMOTED to N-Level {new_level}...\n\n"
        else:
            msg += f"Result: Level Maintained at {new_level}\n\n"

        msg += "Position:\n"
        msg += f"  Hits: {pos_stats['hit']}\n"
        msg += f"  Misses: {pos_stats['miss']}\n"
        msg += f"  False Alarms: {pos_stats['false_alarm']}\n\n"
        msg += "Audio:\n"
        msg += f"  Hits: {audio_stats['hit']}\n"
        msg += f"  Misses: {audio_stats['miss']}\n"
        msg += f"  False Alarms: {audio_stats['false_alarm']}"

        QMessageBox.information(self, "Results", msg)

        # Update level label
        self.lbl_level.setText(f"N-Level: {self.config.n_level}")

        # Save history
        self.storage.save_session(result, self.config)

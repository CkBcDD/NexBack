"""Main application window for NexBack Dual N-Back trainer.

This module provides the primary user interface for the training application,
managing the game flow, user input, and result display.
"""

import random
from typing import TypedDict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
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
from src.nexback.ui.settings_dialog import SettingsDialog
from src.nexback.utils.config import GameConfig


class StimulusStats(TypedDict):
    """Statistics for a single stimulus modality."""

    hit: int
    miss: int
    false_alarm: int
    targets: int


class SessionResult(TypedDict):
    """Result dictionary structure from session completion."""

    stats: dict[StimulusType, StimulusStats]
    final_score: float
    promotion: bool
    demotion: bool
    n_level: int


class MainWindow(QMainWindow):
    """Main application window for the NexBack Dual N-Back trainer.

    Manages:
    - Game initialization and state management
    - UI layout and widget creation
    - Signal connections between engine and UI
    - User input processing
    - Session results display and persistence
    """

    # UI element style constants
    CELL_INACTIVE_STYLE = (
        "background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 8px;"
    )
    STATUS_WAITING_STYLE = "font-size: 16px; font-weight: bold; color: #888;"
    STATUS_CORRECT_STYLE = "font-size: 16px; font-weight: bold; color: #2ecc71;"
    STATUS_INCORRECT_STYLE = "font-size: 16px; font-weight: bold; color: #e74c3c;"
    INSTRUCTIONS_STYLE = "font-size: 14px; color: #888;"

    def __init__(self) -> None:
        """Initialize the main window and all components."""
        super().__init__()
        self.setWindowTitle("NexBack - Dual N-Back Trainer")
        self.resize(600, 700)

        # Initialize core components
        self.config = GameConfig()
        self.engine = NBackEngine(self.config)
        self.storage = Storage()
        self.audio_manager = AudioManager()

        # UI components - initialized in _init_ui
        self.grid: GridWidget
        self.lbl_score: QLabel
        self.lbl_level: QLabel
        self.lbl_instructions: QLabel
        self.lbl_pos_status: QLabel
        self.lbl_audio_status: QLabel
        self.btn_start: QPushButton
        self.btn_stop: QPushButton
        self.chk_clinical: QCheckBox
        self.progress: QProgressBar

        # Initialize UI and connect signals
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize and layout all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header with score, level, and clinical mode toggle
        header_layout = QHBoxLayout()
        self.lbl_level = QLabel(f"N-Level: {self.config.n_level}")
        self.lbl_score = QLabel("Score: 0")
        self.chk_clinical = QCheckBox("Clinical Mode")
        self.chk_clinical.toggled.connect(self.on_clinical_toggled)

        header_layout.addWidget(self.lbl_level)
        header_layout.addStretch()
        header_layout.addWidget(self.chk_clinical)
        header_layout.addWidget(self.lbl_score)
        layout.addLayout(header_layout)

        # 3x3 position stimulus grid
        self.grid = GridWidget()
        layout.addWidget(self.grid, alignment=Qt.AlignmentFlag.AlignCenter)

        # Instructions
        self.lbl_instructions = QLabel(
            "Press 'A' for Position Match | Press 'L' for Audio Match"
        )
        self.lbl_instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_instructions.setStyleSheet(self.INSTRUCTIONS_STYLE)
        layout.addWidget(self.lbl_instructions)

        # Status indicators for each modality
        status_layout = QHBoxLayout()
        self.lbl_pos_status = QLabel("Position: Waiting")
        self.lbl_pos_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pos_status.setStyleSheet(self.STATUS_WAITING_STYLE)

        self.lbl_audio_status = QLabel("Audio: Waiting")
        self.lbl_audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_audio_status.setStyleSheet(self.STATUS_WAITING_STYLE)

        status_layout.addWidget(self.lbl_pos_status)
        status_layout.addWidget(self.lbl_audio_status)
        layout.addLayout(status_layout)

        # Control buttons
        controls_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Session")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_settings = QPushButton("Settings")

        self.btn_start.clicked.connect(self.start_game)
        self.btn_stop.clicked.connect(self.stop_game)
        self.btn_settings.clicked.connect(self.open_settings)

        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.btn_settings)
        layout.addLayout(controls_layout)

        # Progress bar showing trial progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

    def _connect_signals(self) -> None:
        """Connect engine signals to UI update slots."""
        self.engine.stimulus_presented.connect(self.on_stimulus)
        self.engine.feedback_generated.connect(self.on_feedback)
        self.engine.score_updated.connect(self.on_score)
        self.engine.progress_updated.connect(self.on_progress)
        self.engine.session_finished.connect(self.on_finished)

    def on_clinical_toggled(self, checked: bool) -> None:
        """Handle clinical mode toggle.

        Args:
            checked: Whether clinical mode is now enabled.
        """
        self.config.is_clinical_mode = checked
        if checked:
            self.config.scoring_method = self.config.scoring_method.CLINICAL
            # Fixed seed for reproducibility in clinical mode
            self.config.random_seed = 42
        else:
            self.config.scoring_method = self.config.scoring_method.STANDARD
            self.config.random_seed = None

        # Re-initialize RNG with new seed
        self.engine.rng = random.Random(self.config.random_seed)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """Handle keyboard input for stimulus responses.

        Args:
            event: The key press event.
        """
        if not self.engine.is_running or event is None:
            return

        if event.key() == Qt.Key.Key_A:
            self.engine.submit_response(StimulusType.POSITION)
        elif event.key() == Qt.Key.Key_L:
            self.engine.submit_response(StimulusType.AUDIO)

    def start_game(self) -> None:
        """Start a new training session."""
        self.btn_start.setEnabled(False)
        # In clinical mode, disable stop button to enforce session completion (as well as supress xxx is not a known attribute of "None")
        if self.config.is_clinical_mode:
            self.btn_stop.setEnabled(False)
        else:
            self.btn_stop.setEnabled(True)

        self.btn_settings.setEnabled(False)
        self.chk_clinical.setEnabled(False)

        # Reset UI state
        self.lbl_score.setText("Score: 0")
        self._reset_status_labels()
        self.progress.setValue(0)

        # Start engine session
        self.engine.start_session()
        self.grid.setFocus()

    def stop_game(self) -> None:
        """Stop the current training session."""
        self.engine.stop_session()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_settings.setEnabled(True)
        self.chk_clinical.setEnabled(True)

        # Reset UI state
        self.grid.clear()
        self._reset_status_labels()

    def open_settings(self) -> None:
        """Open the settings dialog to modify configuration."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            new_settings = dialog.get_settings()

            # Update config object
            for key, value in new_settings.items():
                setattr(self.config, key, value)

            # Update UI elements that depend on config
            self.lbl_level.setText(f"N-Level: {self.config.n_level}")

            # Save configuration (optional, if we want persistence across restarts)
            # self.config.save("config.toml")

    def _reset_status_labels(self) -> None:
        """Reset status labels to 'Waiting' state."""
        self.lbl_pos_status.setText("Position: Waiting")
        self.lbl_pos_status.setStyleSheet(self.STATUS_WAITING_STYLE)
        self.lbl_audio_status.setText("Audio: Waiting")
        self.lbl_audio_status.setStyleSheet(self.STATUS_WAITING_STYLE)

    def on_stimulus(self, pos: int, audio_char: str) -> None:
        """Handle stimulus presentation.

        Args:
            pos: Position index (0-8) for grid highlighting.
            audio_char: Character identifier for audio playback.
        """
        # Reset feedback status for new stimulus
        self._reset_status_labels()

        # Display position stimulus
        self.grid.highlight(pos)

        # Play audio stimulus
        self.audio_manager.play(audio_char)

        # Clear visual stimulus after display duration
        QTimer.singleShot(self.config.stimulus_duration_ms, self.grid.clear)

    def on_feedback(self, stim_type: StimulusType, response_type: ResponseType) -> None:
        """Handle feedback display for a response.

        Args:
            stim_type: The stimulus modality (Position or Audio).
            response_type: The response classification (Hit, Miss, False Alarm, or Rejection).
        """
        is_correct = response_type in [ResponseType.HIT, ResponseType.REJECTION]

        text = "Correct" if is_correct else "Incorrect"
        style = self.STATUS_CORRECT_STYLE if is_correct else self.STATUS_INCORRECT_STYLE

        # Update appropriate status label
        label = (
            self.lbl_pos_status
            if stim_type == StimulusType.POSITION
            else self.lbl_audio_status
        )
        prefix = "Position" if stim_type == StimulusType.POSITION else "Audio"

        label.setText(f"{prefix}: {text}")
        label.setStyleSheet(style)

    def on_score(self, score: int, total: int) -> None:
        """Update score display.

        Args:
            score: Current score.
            total: Total possible score (unused but included for future use).
        """
        self.lbl_score.setText(f"Score: {score}")

    def on_progress(self, current: int, total: int) -> None:
        """Update progress bar.

        Args:
            current: Current trial number.
            total: Total trials in session.
        """
        self.progress.setMaximum(total)
        self.progress.setValue(current)

    def on_finished(self, result: SessionResult) -> None:
        """Handle session completion and display results.

        Args:
            result: Dictionary containing final statistics and performance metrics.
        """
        self.stop_game()

        stats: dict[StimulusType, StimulusStats] = result["stats"]
        final_score: float = result["final_score"]
        promotion: bool = result["promotion"]
        demotion: bool = result["demotion"]
        new_level: int = result["n_level"]

        # Format results message
        pos_stats: StimulusStats = stats[StimulusType.POSITION]
        audio_stats: StimulusStats = stats[StimulusType.AUDIO]

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

        # Update UI with new level
        self.lbl_level.setText(f"N-Level: {self.config.n_level}")

        # Persist session results
        self.storage.save_session(result, self.config)

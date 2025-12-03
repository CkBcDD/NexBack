"""Settings dialog for NexBack configuration.

This module provides a dialog for users to modify game configuration parameters.
"""

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.nexback.utils.config import GameConfig, ScoringMethod


class SettingsDialog(QDialog):
    """Dialog for editing game configuration settings.

    Allows users to modify N-Level, timing, probabilities, and thresholds.
    """

    def __init__(self, config: GameConfig, parent: QWidget | None = None):
        """Initialize the settings dialog.

        Args:
            config: The current game configuration object.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 500)
        self.config = config

        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Difficulty Settings
        difficulty_group = QGroupBox("Difficulty & Session")
        difficulty_layout = QFormLayout()

        self.spin_n_level = QSpinBox()
        self.spin_n_level.setRange(1, 20)
        self.spin_n_level.setValue(self.config.n_level)
        difficulty_layout.addRow("N-Level:", self.spin_n_level)

        self.spin_total_trials = QSpinBox()
        self.spin_total_trials.setRange(10, 1000)
        self.spin_total_trials.setValue(self.config.total_trials)
        difficulty_layout.addRow("Total Trials:", self.spin_total_trials)

        difficulty_group.setLayout(difficulty_layout)
        layout.addWidget(difficulty_group)

        # Timing Settings
        timing_group = QGroupBox("Timing (ms)")
        timing_layout = QFormLayout()

        self.spin_trial_duration = QSpinBox()
        self.spin_trial_duration.setRange(500, 10000)
        self.spin_trial_duration.setSingleStep(100)
        self.spin_trial_duration.setValue(self.config.trial_duration_ms)
        timing_layout.addRow("Trial Duration:", self.spin_trial_duration)

        self.spin_stimulus_duration = QSpinBox()
        self.spin_stimulus_duration.setRange(100, 5000)
        self.spin_stimulus_duration.setSingleStep(100)
        self.spin_stimulus_duration.setValue(self.config.stimulus_duration_ms)
        timing_layout.addRow("Stimulus Duration:", self.spin_stimulus_duration)

        self.spin_feedback_duration = QSpinBox()
        self.spin_feedback_duration.setRange(0, 5000)
        self.spin_feedback_duration.setSingleStep(100)
        self.spin_feedback_duration.setValue(self.config.feedback_duration_ms)
        timing_layout.addRow("Feedback Duration:", self.spin_feedback_duration)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # Probabilities Settings
        prob_group = QGroupBox("Probabilities (0.0 - 1.0)")
        prob_layout = QFormLayout()

        self.spin_match_prob = QDoubleSpinBox()
        self.spin_match_prob.setRange(0.1, 0.9)
        self.spin_match_prob.setSingleStep(0.05)
        self.spin_match_prob.setValue(self.config.match_probability)
        prob_layout.addRow("Match Probability:", self.spin_match_prob)

        self.spin_interference_prob = QDoubleSpinBox()
        self.spin_interference_prob.setRange(0.0, 0.5)
        self.spin_interference_prob.setSingleStep(0.05)
        self.spin_interference_prob.setValue(self.config.interference_probability)
        prob_layout.addRow("Interference Probability:", self.spin_interference_prob)

        prob_group.setLayout(prob_layout)
        layout.addWidget(prob_group)

        # Thresholds Settings
        threshold_group = QGroupBox("Adaptive Thresholds")
        threshold_layout = QFormLayout()

        self.spin_promotion = QDoubleSpinBox()
        self.spin_promotion.setRange(0.5, 1.0)
        self.spin_promotion.setSingleStep(0.05)
        self.spin_promotion.setValue(self.config.promotion_threshold)
        threshold_layout.addRow("Promotion Threshold:", self.spin_promotion)

        self.spin_demotion = QDoubleSpinBox()
        self.spin_demotion.setRange(0.0, 0.9)
        self.spin_demotion.setSingleStep(0.05)
        self.spin_demotion.setValue(self.config.demotion_threshold)
        threshold_layout.addRow("Demotion Threshold:", self.spin_demotion)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

        # Clinical Mode Settings
        clinical_group = QGroupBox("Clinical Mode")
        clinical_layout = QFormLayout()

        self.check_clinical_mode = QCheckBox()
        self.check_clinical_mode.setChecked(self.config.is_clinical_mode)
        self.check_clinical_mode.stateChanged.connect(self._on_clinical_mode_changed)
        clinical_layout.addRow("Enable Clinical Mode:", self.check_clinical_mode)

        self.combo_scoring_method = QComboBox()
        self.combo_scoring_method.addItem("Standard", ScoringMethod.STANDARD)
        self.combo_scoring_method.addItem("Clinical", ScoringMethod.CLINICAL)
        # Set current index based on config
        current_index = 0 if self.config.scoring_method == ScoringMethod.STANDARD else 1
        self.combo_scoring_method.setCurrentIndex(current_index)
        clinical_layout.addRow("Scoring Method:", self.combo_scoring_method)

        self.spin_random_seed = QSpinBox()
        self.spin_random_seed.setRange(0, 999999)
        self.spin_random_seed.setSpecialValueText("None (Random)")
        self.spin_random_seed.setValue(
            self.config.random_seed if self.config.random_seed else 0
        )
        self.spin_random_seed.setEnabled(self.config.is_clinical_mode)
        clinical_layout.addRow("Random Seed:", self.spin_random_seed)

        clinical_group.setLayout(clinical_layout)
        layout.addWidget(clinical_group)

        # Dialog Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_clinical_mode_changed(self, state: int) -> None:
        """Handle clinical mode checkbox state change.

        Args:
            state: The new checkbox state.
        """
        is_enabled = state != 0
        self.spin_random_seed.setEnabled(is_enabled)

    def get_settings(self) -> dict[str, Any]:
        """Retrieve the updated settings from the dialog widgets.

        Returns:
            dict: A dictionary of updated configuration values.
        """
        return {
            "n_level": self.spin_n_level.value(),
            "total_trials": self.spin_total_trials.value(),
            "trial_duration_ms": self.spin_trial_duration.value(),
            "stimulus_duration_ms": self.spin_stimulus_duration.value(),
            "feedback_duration_ms": self.spin_feedback_duration.value(),
            "match_probability": self.spin_match_prob.value(),
            "interference_probability": self.spin_interference_prob.value(),
            "promotion_threshold": self.spin_promotion.value(),
            "demotion_threshold": self.spin_demotion.value(),
            "is_clinical_mode": self.check_clinical_mode.isChecked(),
            "scoring_method": self.combo_scoring_method.currentData(),
            "random_seed": self.spin_random_seed.value()
            if self.spin_random_seed.value() > 0
            else None,
        }

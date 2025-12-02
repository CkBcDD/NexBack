"""Game configuration and constants for the NexBack training application.

This module defines the GameConfig dataclass which holds all configurable
parameters for the Dual N-Back training task.
"""

from dataclasses import dataclass
from enum import Enum, auto


class ScoringMethod(Enum):
    """Enumeration of available scoring methods for performance evaluation."""

    STANDARD = auto()  # Standard N-Back scoring (accuracy-based)
    CLINICAL = auto()  # Stricter clinical scoring (sensitivity/specificity-based)


@dataclass
class GameConfig:
    """Configuration parameters for the Dual N-Back training game.

    Attributes:
        n_level: Current N-Back level (difficulty). Starts at 2.
        trial_duration_ms: Duration of each trial in milliseconds.
        stimulus_duration_ms: Duration to display each stimulus.
        feedback_duration_ms: Duration to show feedback before next stimulus.
        total_trials: Total number of trials in a session.
        match_probability: Probability that a stimulus will match the N-back stimulus.
        interference_probability: Probability of generating interference (N±1).
        promotion_threshold: Performance threshold for level promotion.
        demotion_threshold: Performance threshold for level demotion.
        scoring_method: Scoring method (STANDARD or CLINICAL).
        is_clinical_mode: Whether clinical mode is enabled.
        random_seed: Seed for reproducible stimulus sequences in clinical mode.
    """

    # Difficulty and timing
    n_level: int = 2
    trial_duration_ms: int = 3000  # Time per trial
    stimulus_duration_ms: int = 1000  # Time stimulus is displayed
    feedback_duration_ms: int = 500  # Time to show feedback

    # Session parameters
    total_trials: int = 20

    # Stimulus generation probabilities
    match_probability: float = 0.3  # Probability of N-back match
    interference_probability: float = 0.1  # Probability of N±1 interference

    # Adaptive difficulty thresholds
    promotion_threshold: float = 0.8
    demotion_threshold: float = 0.5

    # Scoring configuration
    scoring_method: ScoringMethod = ScoringMethod.STANDARD

    # Clinical mode configuration
    is_clinical_mode: bool = False
    random_seed: int | None = None  # For reproducible sequences in clinical mode

"""Game configuration and constants for the NexBack training application.

This module defines the GameConfig dataclass which holds all configurable
parameters for the Dual N-Back training task.
"""

import tomllib
from dataclasses import asdict, dataclass
from enum import Enum, auto
from pathlib import Path

import tomli_w


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

    def save(self, path: Path | str) -> None:
        """Save configuration to a TOML file.

        Args:
            path: Path to the TOML file.
        """
        data = asdict(self)

        # Convert Enum to string
        data["scoring_method"] = self.scoring_method.name

        # Remove None values (TOML doesn't support null)
        data = {k: v for k, v in data.items() if v is not None}

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    @classmethod
    def load(cls, path: Path | str) -> "GameConfig":
        """Load configuration from a TOML file.

        Args:
            path: Path to the TOML file.

        Returns:
            GameConfig: Loaded configuration.
        """
        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Convert string back to Enum
        if "scoring_method" in data:
            try:
                data["scoring_method"] = ScoringMethod[data["scoring_method"]]
            except KeyError:
                # Fallback to default if invalid enum name
                data.pop("scoring_method")

        return cls(**data)

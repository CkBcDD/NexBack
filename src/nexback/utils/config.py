from dataclasses import dataclass


@dataclass
class GameConfig:
    n_level: int = 2
    trial_duration_ms: int = 3000  # Time per trial
    stimulus_duration_ms: int = 1000  # Time stimulus is active
    total_trials: int = 20
    match_probability: float = 0.3

    # Scoring thresholds
    promotion_threshold: float = 0.8
    demotion_threshold: float = 0.5

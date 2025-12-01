from dataclasses import dataclass
from enum import Enum, auto


class ScoringMethod(Enum):
    STANDARD = auto()
    CLINICAL = auto()


@dataclass
class GameConfig:
    n_level: int = 2
    trial_duration_ms: int = 3000  # Time per trial
    stimulus_duration_ms: int = 1000  # Time stimulus is active
    feedback_duration_ms: int = 500  # Time to show feedback before next stimulus
    total_trials: int = 20
    match_probability: float = 0.3
    interference_probability: float = (
        0.1  # Probability of generating interference (N-1 or N+1)
    )

    # Scoring thresholds
    promotion_threshold: float = 0.8
    demotion_threshold: float = 0.5

    # Scoring Method
    scoring_method: ScoringMethod = ScoringMethod.STANDARD

    # Clinical Mode
    is_clinical_mode: bool = False
    random_seed: int | None = None  # For reproducible sequences in clinical mode

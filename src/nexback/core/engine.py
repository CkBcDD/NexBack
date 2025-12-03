"""Dual N-Back game engine implementation.

This module provides the core logic for the Dual N-Back cognitive training task.
It manages stimulus generation, response evaluation, scoring, and adaptive difficulty.
"""

import random
from enum import Enum, auto

from PySide6.QtCore import QObject, QTimer, Signal

from src.nexback.utils.config import GameConfig, ScoringMethod


class StimulusType(Enum):
    """Enumeration of stimulus modalities."""

    POSITION = auto()
    AUDIO = auto()


class ResponseType(Enum):
    """Enumeration of response classification types."""

    HIT = auto()  # Correctly identified match
    MISS = auto()  # Missed a match
    FALSE_ALARM = auto()  # Claimed match when none existed
    REJECTION = auto()  # Correctly ignored non-match (implicit)


class NBackEngine(QObject):
    """Core engine for Dual N-Back training task.

    Manages stimulus generation, response evaluation, scoring, and adaptive difficulty.

    Signals:
        stimulus_presented: Emitted when a new stimulus is presented (position_index, audio_char).
        feedback_generated: Emitted with feedback for a response (StimulusType, ResponseType).
        score_updated: Emitted when score changes (current_score, total_possible).
        session_finished: Emitted when session ends with final statistics dict.
        progress_updated: Emitted when progress changes (current_trial, total_trials).
    """

    stimulus_presented = Signal(int, str)  # position_index (0-8), audio_char
    feedback_generated = Signal(StimulusType, ResponseType)
    score_updated = Signal(int, int)  # current_score, total_possible
    session_finished = Signal(dict)  # final stats
    progress_updated = Signal(int, int)  # current, total

    def __init__(self, config: GameConfig) -> None:
        """Initialize the N-Back engine.

        Args:
            config: Game configuration object containing all game parameters.
        """
        super().__init__()
        self.config = config
        self.history: list[tuple[int, str]] = []  # List of (position, audio) tuples
        self.current_trial: int = 0
        self.is_running: bool = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._next_trial)

        # Random Number Generator for reproducible sequences
        self.rng = random.Random(self.config.random_seed)

        # Current trial state
        self.current_stimulus: tuple[int, str] | None = None
        self.user_responses: dict[StimulusType, bool] = {
            StimulusType.POSITION: False,
            StimulusType.AUDIO: False,
        }

        # Scoring statistics by stimulus type
        self.stats: dict[StimulusType, dict[str, int]] = {
            StimulusType.POSITION: {
                "hit": 0,
                "miss": 0,
                "false_alarm": 0,
                "targets": 0,
            },
            StimulusType.AUDIO: {"hit": 0, "miss": 0, "false_alarm": 0, "targets": 0},
        }

    def start_session(self) -> None:
        """Start a new training session."""
        self.history = []
        self.current_trial = 0
        self.is_running = True
        self._reset_stats()
        self._next_trial()

    def stop_session(self) -> None:
        """Stop the current training session."""
        self.is_running = False
        self.timer.stop()

    def submit_response(self, stimulus_type: StimulusType) -> None:
        """Process user response to a stimulus.

        Args:
            stimulus_type: The stimulus modality for which a response was made.
        """
        if not self.is_running:
            return

        # Prevent double submission for the same trial
        if self.user_responses[stimulus_type]:
            return

        self.user_responses[stimulus_type] = True

        # Evaluate response immediately
        is_match = self._check_match(stimulus_type)
        if is_match:
            self.stats[stimulus_type]["hit"] += 1
            self.feedback_generated.emit(stimulus_type, ResponseType.HIT)
        else:
            self.stats[stimulus_type]["false_alarm"] += 1
            self.feedback_generated.emit(stimulus_type, ResponseType.FALSE_ALARM)

        self._emit_score()

    def _next_trial(self) -> None:
        """Schedule the next trial, handling feedback display."""
        if self.current_trial >= self.config.total_trials:
            self._finish_session()
            return

        # Evaluate previous trial (check for misses) and show feedback
        if self.current_trial > 0:
            self._evaluate_misses()
            # Wait for feedback to be shown before presenting next stimulus
            QTimer.singleShot(self.config.feedback_duration_ms, self._present_stimulus)
        else:
            # First trial, present immediately
            self._present_stimulus()

    def _present_stimulus(self) -> None:
        """Generate and present a new stimulus."""
        if not self.is_running:
            return

        # Generate new stimulus
        pos, audio = self._generate_stimulus()
        self.current_stimulus = (pos, audio)
        self.history.append(self.current_stimulus)

        # Reset user response state for new trial
        self.user_responses = {StimulusType.POSITION: False, StimulusType.AUDIO: False}

        # Emit signals for UI update
        self.stimulus_presented.emit(pos, audio)
        self.progress_updated.emit(self.current_trial + 1, self.config.total_trials)

        # Schedule next trial
        self.current_trial += 1
        self.timer.start(self.config.trial_duration_ms)

    def _generate_stimulus(self) -> tuple[int, str]:
        """Generate a new stimulus based on N-Back rules.

        Returns:
            Tuple of (position_index, audio_character).
        """
        n = self.config.n_level
        force_match = self.rng.random() < self.config.match_probability
        force_interference = (
            not force_match and self.rng.random() < self.config.interference_probability
        )

        pos = self.rng.randint(0, 8)
        audio_pool = "ABCHKLQR"
        audio = self.rng.choice(audio_pool)

        # Generate match or interference if enough history
        if len(self.history) >= n:
            if force_match:
                self._apply_match(pos, audio, n, audio_pool)
            elif force_interference:
                self._apply_interference(pos, audio, n, audio_pool)

        return pos, audio

    def _apply_match(
        self, pos: int, audio: str, n: int, audio_pool: str
    ) -> tuple[int, str]:
        """Apply N-Back match to current stimulus.

        Args:
            pos: Current position value.
            audio: Current audio character.
            n: N-Back level.
            audio_pool: Available audio characters.

        Returns:
            Modified (position, audio) tuple.
        """
        # Decide which modality to match (or both)
        match_type = self.rng.choice(
            [StimulusType.POSITION, StimulusType.AUDIO, "BOTH"]
        )

        target_pos, target_audio = self.history[-n]

        if match_type == StimulusType.POSITION or match_type == "BOTH":
            pos = target_pos
        if match_type == StimulusType.AUDIO or match_type == "BOTH":
            audio = target_audio

        return pos, audio

    def _apply_interference(
        self, pos: int, audio: str, n: int, audio_pool: str
    ) -> tuple[int, str]:
        """Apply interference stimulus (N-1 or N+1).

        Args:
            pos: Current position value.
            audio: Current audio character.
            n: N-Back level.
            audio_pool: Available audio characters.

        Returns:
            Modified (position, audio) tuple.
        """
        offsets: list[int] = []
        if n > 1:
            offsets.append(n - 1)
        if len(self.history) >= n + 1:
            offsets.append(n + 1)

        if not offsets:
            return pos, audio

        interference_n: int = self.rng.choice(offsets)
        target_pos: int
        target_audio: str
        target_pos, target_audio = self.history[-interference_n]
        interference_type = self.rng.choice([StimulusType.POSITION, StimulusType.AUDIO])

        if interference_type == StimulusType.POSITION:
            pos = target_pos
            # Ensure it's NOT a match for N-level
            if pos == self.history[-n][0]:
                candidates = [p for p in range(9) if p != self.history[-n][0]]
                if candidates:
                    pos = self.rng.choice(candidates)

        elif interference_type == StimulusType.AUDIO:
            audio = target_audio
            # Ensure it's NOT a match for N-level
            if audio == self.history[-n][1]:
                candidates = [c for c in audio_pool if c != self.history[-n][1]]
                if candidates:
                    audio = self.rng.choice(candidates)

        return pos, audio

    def _check_match(self, stimulus_type: StimulusType) -> bool:
        """Check if current stimulus matches the N-back stimulus.

        Args:
            stimulus_type: The stimulus modality to check.

        Returns:
            True if current matches N-back stimulus, False otherwise.
        """
        n = self.config.n_level
        if len(self.history) <= n:
            return False

        current = self.history[-1]
        target = self.history[-(n + 1)]

        if stimulus_type == StimulusType.POSITION:
            return current[0] == target[0]
        elif stimulus_type == StimulusType.AUDIO:
            return current[1] == target[1]
        return False

    def _evaluate_misses(self) -> None:
        """Evaluate the previous trial for misses and correct rejections."""
        if not self.history:
            return

        last_stim_idx = len(self.history) - 1
        n = self.config.n_level

        last_pos, last_audio = self.history[-1]

        # Determine if there was a match for each modality
        pos_match = False
        audio_match = False

        if last_stim_idx >= n:
            target_pos, target_audio = self.history[-(1 + n)]
            pos_match = last_pos == target_pos
            audio_match = last_audio == target_audio

        # Evaluate Position modality
        if pos_match:
            self.stats[StimulusType.POSITION]["targets"] += 1
            if not self.user_responses[StimulusType.POSITION]:
                self.stats[StimulusType.POSITION]["miss"] += 1
                self.feedback_generated.emit(StimulusType.POSITION, ResponseType.MISS)
        else:
            if not self.user_responses[StimulusType.POSITION]:
                self.feedback_generated.emit(
                    StimulusType.POSITION, ResponseType.REJECTION
                )

        # Evaluate Audio modality
        if audio_match:
            self.stats[StimulusType.AUDIO]["targets"] += 1
            if not self.user_responses[StimulusType.AUDIO]:
                self.stats[StimulusType.AUDIO]["miss"] += 1
                self.feedback_generated.emit(StimulusType.AUDIO, ResponseType.MISS)
        else:
            if not self.user_responses[StimulusType.AUDIO]:
                self.feedback_generated.emit(StimulusType.AUDIO, ResponseType.REJECTION)

        self._emit_score()

    def _reset_stats(self) -> None:
        """Reset scoring statistics to initial state."""
        self.stats = {
            StimulusType.POSITION: {
                "hit": 0,
                "miss": 0,
                "false_alarm": 0,
                "targets": 0,
            },
            StimulusType.AUDIO: {"hit": 0, "miss": 0, "false_alarm": 0, "targets": 0},
        }

    def _emit_score(self) -> None:
        """Emit current score update signal."""
        total_hits = (
            self.stats[StimulusType.POSITION]["hit"]
            + self.stats[StimulusType.AUDIO]["hit"]
        )
        self.score_updated.emit(total_hits, 0)

    def _finish_session(self) -> None:
        """Finish the session, evaluate performance, and emit results."""
        self.is_running = False
        self.timer.stop()
        self._evaluate_misses()

        # Calculate final score
        final_score = self._calculate_final_score()

        # Determine adaptive difficulty adjustments
        promotion = False
        demotion = False

        if not self.config.is_clinical_mode:
            if final_score >= self.config.promotion_threshold:
                promotion = True
                self.config.n_level += 1
            elif final_score < self.config.demotion_threshold:
                demotion = True
                if self.config.n_level > 1:
                    self.config.n_level -= 1

        # Prepare and emit results
        result = {
            "stats": self.stats,
            "final_score": final_score,
            "promotion": promotion,
            "demotion": demotion,
            "n_level": self.config.n_level,
        }

        self.session_finished.emit(result)

    def _calculate_final_score(self) -> float:
        """Calculate final performance score based on scoring method.

        Returns:
            Final score as a float between 0.0 and 1.0.
        """
        pos_stats = self.stats[StimulusType.POSITION]
        audio_stats = self.stats[StimulusType.AUDIO]

        # Valid trials for scoring (after initial N trials)
        total_valid_trials = max(0, self.config.total_trials - self.config.n_level)

        if self.config.scoring_method == ScoringMethod.STANDARD:
            return self._calculate_standard_score(
                pos_stats, audio_stats, total_valid_trials
            )
        elif self.config.scoring_method == ScoringMethod.CLINICAL:
            return self._calculate_clinical_score(
                pos_stats, audio_stats, total_valid_trials
            )

        return 0.0

    def _calculate_standard_score(
        self,
        pos_stats: dict[str, int],
        audio_stats: dict[str, int],
        total_valid_trials: int,
    ) -> float:
        """Calculate score using standard N-Back scoring method.

        Score = True Positives / (True Positives + False Positives + False Negatives)

        Args:
            pos_stats: Position modality statistics.
            audio_stats: Audio modality statistics.
            total_valid_trials: Number of valid trials for scoring.

        Returns:
            Average score across modalities.
        """

        def calc_standard(stats: dict[str, int]) -> float:
            denom = stats["hit"] + stats["false_alarm"] + stats["miss"]
            return stats["hit"] / denom if denom > 0 else 0.0

        pos_score = calc_standard(pos_stats)
        audio_score = calc_standard(audio_stats)
        return (pos_score + audio_score) / 2.0

    def _calculate_clinical_score(
        self,
        pos_stats: dict[str, int],
        audio_stats: dict[str, int],
        total_valid_trials: int,
    ) -> float:
        """Calculate score using clinical N-Back scoring method.

        Score = (True Positives + True Negatives) / Total Valid Trials
        Final Score = Min(Position Score, Audio Score)

        Args:
            pos_stats: Position modality statistics.
            audio_stats: Audio modality statistics.
            total_valid_trials: Number of valid trials for scoring.

        Returns:
            Minimum score across modalities (stricter evaluation).
        """

        def calc_clinical(stats: dict[str, int]) -> float:
            if total_valid_trials == 0:
                return 0.0

            tp = stats["hit"]
            fp = stats["false_alarm"]
            targets = stats["targets"]

            # Trials without match = Total Valid - Targets
            trials_without_match = total_valid_trials - targets

            # True Negatives = Trials without match - False Positives
            tn = max(0, trials_without_match - fp)

            return (tp + tn) / total_valid_trials

        pos_score = calc_clinical(pos_stats)
        audio_score = calc_clinical(audio_stats)
        return min(pos_score, audio_score)

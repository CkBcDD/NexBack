import random
from enum import Enum, auto

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.nexback.utils.config import GameConfig, ScoringMethod


class StimulusType(Enum):
    POSITION = auto()
    AUDIO = auto()


class ResponseType(Enum):
    HIT = auto()  # Correctly identified match
    MISS = auto()  # Missed a match
    FALSE_ALARM = auto()  # Claimed match when none existed
    REJECTION = auto()  # Correctly ignored non-match (implicit)


class NBackEngine(QObject):
    # Signals
    stimulus_presented = pyqtSignal(int, str)  # position_index (0-8), audio_char
    feedback_generated = pyqtSignal(StimulusType, ResponseType)
    score_updated = pyqtSignal(int, int)  # current_score, total_possible
    session_finished = pyqtSignal(dict)  # final stats
    progress_updated = pyqtSignal(int, int)  # current, total

    def __init__(self, config: GameConfig):
        super().__init__()
        self.config = config
        self.history = []  # List of (position, audio) tuples
        self.current_trial = 0
        self.is_running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._next_trial)

        # State for current trial
        self.current_stimulus = None
        self.user_responses = {StimulusType.POSITION: False, StimulusType.AUDIO: False}

        # Scoring
        self.stats = {
            StimulusType.POSITION: {
                "hit": 0,
                "miss": 0,
                "false_alarm": 0,
                "targets": 0,
            },
            StimulusType.AUDIO: {"hit": 0, "miss": 0, "false_alarm": 0, "targets": 0},
        }

    def start_session(self):
        self.history = []
        self.current_trial = 0
        self.is_running = True
        self._reset_stats()
        self._next_trial()

    def stop_session(self):
        self.is_running = False
        self.timer.stop()

    def submit_response(self, stimulus_type: StimulusType):
        if not self.is_running:
            return

        # Prevent double submission for same trial
        if self.user_responses[stimulus_type]:
            return

        self.user_responses[stimulus_type] = True

        # Immediate feedback logic could go here, but usually we evaluate at end of trial
        # For MVP, let's evaluate immediately for "False Alarm" check or wait?
        # Standard N-Back evaluates response within the window.

        # Let's check if it is a match right now
        is_match = self._check_match(stimulus_type)
        if is_match:
            self.stats[stimulus_type]["hit"] += 1
            self.feedback_generated.emit(stimulus_type, ResponseType.HIT)
        else:
            self.stats[stimulus_type]["false_alarm"] += 1
            self.feedback_generated.emit(stimulus_type, ResponseType.FALSE_ALARM)

        self._emit_score()

    def _next_trial(self):
        if self.current_trial >= self.config.total_trials:
            self._finish_session()
            return

        # 1. Evaluate previous trial (check for Misses)
        if self.current_trial > 0:
            self._evaluate_misses()

        # 2. Generate new stimulus
        pos, audio = self._generate_stimulus()
        self.current_stimulus = (pos, audio)
        self.history.append(self.current_stimulus)

        # 3. Reset user response state for new trial
        self.user_responses = {StimulusType.POSITION: False, StimulusType.AUDIO: False}

        # 4. Emit signals
        self.stimulus_presented.emit(pos, audio)
        self.progress_updated.emit(self.current_trial + 1, self.config.total_trials)

        # 5. Schedule next
        self.current_trial += 1
        self.timer.start(self.config.trial_duration_ms)

    def _generate_stimulus(self):
        n = self.config.n_level
        force_match = random.random() < self.config.match_probability
        force_interference = (
            not force_match and random.random() < self.config.interference_probability
        )

        pos = random.randint(0, 8)
        audio_pool = "ABCHKLQR"
        audio = random.choice(audio_pool)

        # If we have enough history
        if len(self.history) >= n:
            if force_match:
                # Decide which modality to match (or both)
                match_type = random.choice(
                    [StimulusType.POSITION, StimulusType.AUDIO, "BOTH"]
                )

                target_pos, target_audio = self.history[-n]

                if match_type == StimulusType.POSITION or match_type == "BOTH":
                    pos = target_pos
                if match_type == StimulusType.AUDIO or match_type == "BOTH":
                    audio = target_audio

            elif force_interference:
                # Generate interference (N-1 or N+1)
                offsets = []
                if n > 1:
                    offsets.append(n - 1)
                if len(self.history) >= n + 1:
                    offsets.append(n + 1)

                if offsets:
                    interference_n = random.choice(offsets)
                    target_pos, target_audio = self.history[-interference_n]
                    interference_type = random.choice(
                        [StimulusType.POSITION, StimulusType.AUDIO]
                    )

                    if interference_type == StimulusType.POSITION:
                        pos = target_pos
                        # Ensure it's NOT a match for N
                        if pos == self.history[-n][0]:
                            # If it accidentally matches N, change it to something else
                            # Try to find a pos that is NOT the N-back pos
                            candidates = [
                                p for p in range(9) if p != self.history[-n][0]
                            ]
                            if candidates:
                                pos = random.choice(candidates)

                    elif interference_type == StimulusType.AUDIO:
                        audio = target_audio
                        # Ensure it's NOT a match for N
                        if audio == self.history[-n][1]:
                            candidates = [
                                c for c in audio_pool if c != self.history[-n][1]
                            ]
                            if candidates:
                                audio = random.choice(candidates)

        return pos, audio

    def _check_match(self, stimulus_type: StimulusType) -> bool:
        n = self.config.n_level
        if len(self.history) <= n:
            return False

        current = self.history[-1]
        target = self.history[-(n + 1)]  # -1 is current, -(n+1) is N steps back

        if stimulus_type == StimulusType.POSITION:
            return current[0] == target[0]
        elif stimulus_type == StimulusType.AUDIO:
            return current[1] == target[1]
        return False

    def _evaluate_misses(self):
        # Check if the PREVIOUS trial was a match that the user missed
        if not self.history:
            return

        last_stim_idx = len(self.history) - 1
        n = self.config.n_level

        last_pos, last_audio = self.history[-1]

        # Determine if there was a match
        pos_match = False
        audio_match = False

        if last_stim_idx >= n:
            target_pos, target_audio = self.history[-(1 + n)]
            pos_match = last_pos == target_pos
            audio_match = last_audio == target_audio

        # Check Position
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

        # Check Audio
        if audio_match:
            self.stats[StimulusType.AUDIO]["targets"] += 1
            if not self.user_responses[StimulusType.AUDIO]:
                self.stats[StimulusType.AUDIO]["miss"] += 1
                self.feedback_generated.emit(StimulusType.AUDIO, ResponseType.MISS)
        else:
            if not self.user_responses[StimulusType.AUDIO]:
                self.feedback_generated.emit(StimulusType.AUDIO, ResponseType.REJECTION)

        self._emit_score()

    def _reset_stats(self):
        self.stats = {
            StimulusType.POSITION: {
                "hit": 0,
                "miss": 0,
                "false_alarm": 0,
                "targets": 0,
            },
            StimulusType.AUDIO: {"hit": 0, "miss": 0, "false_alarm": 0, "targets": 0},
        }

    def _emit_score(self):
        # Simple score: Hits
        total_hits = (
            self.stats[StimulusType.POSITION]["hit"]
            + self.stats[StimulusType.AUDIO]["hit"]
        )
        # Total possible is hard to know in advance, so just send current hits
        self.score_updated.emit(total_hits, 0)

    def _finish_session(self):
        self.is_running = False
        self.timer.stop()
        # Final evaluation of the very last trial
        self._evaluate_misses()

        # Calculate Score
        final_score = 0.0
        pos_stats = self.stats[StimulusType.POSITION]
        audio_stats = self.stats[StimulusType.AUDIO]

        # Valid trials for scoring (trials where a match was possible)
        # Actually, we should count all trials where user *could* respond?
        # Standard N-Back usually ignores the first N trials for scoring.
        total_valid_trials = max(0, self.config.total_trials - self.config.n_level)

        if self.config.scoring_method == ScoringMethod.STANDARD:
            # Score = True Positive / (True Positive + False Positive + False Negative)
            def calc_standard(stats):
                denom = stats["hit"] + stats["false_alarm"] + stats["miss"]
                return stats["hit"] / denom if denom > 0 else 0.0

            pos_score = calc_standard(pos_stats)
            audio_score = calc_standard(audio_stats)
            final_score = (pos_score + audio_score) / 2.0

        elif self.config.scoring_method == ScoringMethod.CLINICAL:
            # Modality Score = (True Positive + True Negative) / Total Trials
            # Final Score = Min(Modality Scores)
            def calc_clinical(stats):
                if total_valid_trials == 0:
                    return 0.0
                tp = stats["hit"]
                _fn = stats["miss"]  # noqa: F841 - kept for clarity
                fp = stats["false_alarm"]

                # Trials with Match = TP + FN (Targets)
                # But we tracked "targets" in stats, let's use that to be safe
                targets = stats["targets"]

                # Trials without Match = Total Valid - Targets
                trials_without_match = total_valid_trials - targets

                # TN = Trials without Match - FP
                tn = max(0, trials_without_match - fp)

                return (tp + tn) / total_valid_trials

            pos_score = calc_clinical(pos_stats)
            audio_score = calc_clinical(audio_stats)
            final_score = min(pos_score, audio_score)

        # Adaptive Difficulty
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

        result = {
            "stats": self.stats,
            "final_score": final_score,
            "promotion": promotion,
            "demotion": demotion,
            "n_level": self.config.n_level,
        }

        self.session_finished.emit(result)

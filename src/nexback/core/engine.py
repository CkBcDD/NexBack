import random
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from src.nexback.utils.config import GameConfig


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
        # Simple random generation for MVP
        # In a real app, we'd force matches based on probability

        n = self.config.n_level
        force_match = random.random() < self.config.match_probability

        pos = random.randint(0, 8)
        audio_pool = "ABCHKLQR"
        audio = random.choice(audio_pool)

        # If we have enough history, maybe force a match
        if len(self.history) >= n and force_match:
            # Decide which modality to match (or both)
            match_type = random.choice(
                [StimulusType.POSITION, StimulusType.AUDIO, "BOTH"]
            )

            target_pos, target_audio = self.history[-n]

            if match_type == StimulusType.POSITION or match_type == "BOTH":
                pos = target_pos
            if match_type == StimulusType.AUDIO or match_type == "BOTH":
                audio = target_audio

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
        # Note: self.history has already been appended with the *current* (just generated) stimulus?
        # No, _next_trial generates *new* stimulus.
        # So we need to check the *last* stimulus in history before we append the new one?
        # Actually, let's look at the flow:
        # T0: Gen S0. Wait.
        # T1: Eval S0. Gen S1. Wait.

        if not self.history:
            return

        last_stim_idx = len(self.history) - 1
        n = self.config.n_level

        # We can only have a match if we had history N steps before the last stimulus
        if last_stim_idx < n:
            return

        # Re-check if the last stimulus was a match
        # Last stimulus is history[-1]
        # Target for that was history[-(1+n)]

        last_pos, last_audio = self.history[-1]
        target_pos, target_audio = self.history[-(1 + n)]

        # Check Position Miss
        if last_pos == target_pos:
            self.stats[StimulusType.POSITION]["targets"] += 1
            if not self.user_responses[StimulusType.POSITION]:
                self.stats[StimulusType.POSITION]["miss"] += 1
                self.feedback_generated.emit(StimulusType.POSITION, ResponseType.MISS)

        # Check Audio Miss
        if last_audio == target_audio:
            self.stats[StimulusType.AUDIO]["targets"] += 1
            if not self.user_responses[StimulusType.AUDIO]:
                self.stats[StimulusType.AUDIO]["miss"] += 1
                self.feedback_generated.emit(StimulusType.AUDIO, ResponseType.MISS)

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
        self.session_finished.emit(self.stats)

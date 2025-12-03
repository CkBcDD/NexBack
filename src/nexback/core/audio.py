"""Audio playback management for N-Back stimuli.

This module handles playback of pre-recorded audio files (Opus format)
for audio stimuli in the Dual N-Back training task.
"""

import os
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioManager:
    """Manages audio playback for training stimuli.

    Uses Qt's QMediaPlayer to play pre-recorded audio files in Opus format.
    """

    # Audio characters available for training
    AUDIO_POOL = "ABCHKLQR"

    def __init__(self, audio_dir: str | Path | None = None) -> None:
        """Initialize the audio manager.

        Args:
            audio_dir: Directory containing audio files. If None, defaults to
                      'resources/audio' in the current working directory.
        """
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        # Set audio directory
        if audio_dir is None:
            base_path = os.getcwd()
            audio_dir = os.path.join(base_path, "resources", "audio")

        self.audio_dir = Path(audio_dir)

    def play(self, char: str) -> None:
        """Play audio file for the given character.

        Args:
            char: Audio character to play (e.g., 'A', 'B', 'C').

        Raises:
            Warning printed if audio file not found for the character.
        """
        filename = f"{char}.opus"
        file_path = self.audio_dir / filename

        if file_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            self.player.play()
        else:
            print(f"Warning: Audio file not found for '{char}' at {file_path}")

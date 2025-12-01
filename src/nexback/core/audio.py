import os

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioManager:
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        # Assuming resources are in the root/resources/audio
        # Adjust path logic as needed based on entry point
        base_path = os.getcwd()
        self.audio_dir = os.path.join(base_path, "resources", "audio")

    def play(self, char: str):
        """Play the audio file for the given character."""
        filename = f"{char}.opus"
        file_path = os.path.join(self.audio_dir, filename)

        if os.path.exists(file_path):
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
        else:
            print(f"Warning: Audio file not found for '{char}' at {file_path}")

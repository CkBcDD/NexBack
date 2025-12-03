"""Session data storage and retrieval management.

This module provides persistent storage for training session results,
supporting both standard JSON format and secure binary format for clinical data.
"""

import json
import pickle
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast


class Storage:
    """Manages persistent storage of training session results.

    Supports:
    - JSON format for standard session history (human-readable)
    - Secure binary (pickle) format for clinical mode data
    """

    def __init__(self, storage_dir: str | Path = ".data") -> None:
        """Initialize storage manager.

        Args:
            storage_dir: Directory to store session data. Defaults to '.data'.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "history.json"
        self.secure_file = self.storage_dir / "secure_history.bin"

    def save_session(self, result: dict[str, Any] | Any, config: Any) -> None:
        """Save session results to storage.

        Args:
            result: Session result dictionary containing stats, score, and level info.
                    Can be a TypedDict or regular dict.
            config: Game configuration object used for the session.
        """
        # Convert config to dictionary format
        config_dict = self._config_to_dict(config)

        # Make result serializable (convert Enum keys/values)
        serializable_result = self._make_serializable(result)

        # Create session entry with timestamp
        entry = {
            "timestamp": datetime.now().isoformat(),
            "config": config_dict,
            "result": serializable_result,
        }

        # Always save to JSON for user visibility
        history = self.load_history()
        history.append(entry)

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        # If clinical mode, also save to secure binary file
        if config_dict.get("is_clinical_mode", False):
            self._save_secure(entry)

    def load_history(self) -> list[dict[str, Any]]:
        """Load all session history from JSON file.

        Returns:
            List of session entries, or empty list if file doesn't exist.
        """
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def _config_to_dict(config: Any) -> dict[str, Any]:
        """Convert config object to serializable dictionary.

        Args:
            config: Configuration object (dataclass or regular object).

        Returns:
            Dictionary representation with Enums converted to names.
        """
        if is_dataclass(config) and not isinstance(config, type):
            config_dict = asdict(config)
        else:
            config_dict = config.__dict__

        # Convert Enum values to their string names
        for key, value in config_dict.items():
            if isinstance(value, Enum):
                config_dict[key] = value.name

        return config_dict

    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """Recursively convert object to JSON-serializable format.

        Args:
            obj: Object to convert.

        Returns:
            Serializable representation (Enums as names, dicts/lists recursively converted).
        """
        if isinstance(obj, Enum):
            return obj.name
        elif isinstance(obj, dict):
            obj_dict = cast(dict[Any, Any], obj)
            return {
                Storage._make_serializable(k): Storage._make_serializable(v)
                for k, v in obj_dict.items()
            }
        elif isinstance(obj, list):
            obj_list = cast(list[Any], obj)
            return [Storage._make_serializable(i) for i in obj_list]
        else:
            return obj

    def _save_secure(self, entry: dict[str, Any]) -> None:
        """Save session entry to secure binary format (pickle).

        Args:
            entry: Session entry to save securely.
        """
        data: list[dict[str, Any]] = []
        if self.secure_file.exists():
            try:
                with open(self.secure_file, "rb") as f:
                    data = pickle.load(f)
            except (OSError, pickle.UnpicklingError):
                # File corrupted or invalid, start fresh
                data = []

        data.append(entry)

        with open(self.secure_file, "wb") as f:
            pickle.dump(data, f)

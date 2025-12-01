import json
import pickle
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class Storage:
    def __init__(self, storage_dir=".data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "history.json"
        self.secure_file = self.storage_dir / "secure_history.bin"

    def save_session(self, result: dict, config):
        # Convert config to dict
        if is_dataclass(config) and not isinstance(config, type):
            config_dict = asdict(config)
        else:
            config_dict = config.__dict__

        # Handle Enums in config
        for k, v in config_dict.items():
            if isinstance(v, Enum):
                config_dict[k] = v.name

        # Handle Enums in result (StimulusType, ResponseType are keys/values in stats)
        # result['stats'] keys are StimulusType enum members.
        # We need to serialize them.

        serializable_result = self._make_serializable(result)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "config": config_dict,
            "result": serializable_result,
        }

        # Always save to JSON for user visibility
        history = self.load_history()
        history.append(entry)

        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

        # If clinical mode, also save to secure binary file
        if config_dict.get("is_clinical_mode", False):
            self._save_secure(entry)

    def _save_secure(self, entry):
        data = []
        if self.secure_file.exists():
            try:
                with open(self.secure_file, "rb") as f:
                    data = pickle.load(f)
            except Exception:
                pass

        data.append(entry)

        with open(self.secure_file, "wb") as f:
            pickle.dump(data, f)

    def load_history(self):
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except Exception:
            return []

    def _make_serializable(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        elif isinstance(obj, dict):
            return {
                self._make_serializable(k): self._make_serializable(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._make_serializable(i) for i in obj]
        else:
            return obj

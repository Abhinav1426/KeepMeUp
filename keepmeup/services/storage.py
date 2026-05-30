"""
Settings & stats persistence — JSON file in the user config directory.

Stores user preferences, the active profile, schedule, selected content file,
window state and lifetime statistics. Loaded automatically at startup.
"""

import json
import os
import sys


APP_NAME = "KeepMeUp"


def config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


DEFAULTS = {
    "user_preferences": {
        "mode": "simple",                 # simple | power
        "current_profile": "Programmer",
        "minimize_to_tray": True,
        "start_on_launch": False,
        "mouse_enabled": True,
        "keyboard_enabled": True,
        "startup_delay": 30,
    },
    "content": {
        "file": "",                       # absolute path; empty -> bundled content.txt
    },
    "schedule": {
        "enabled": False,
        "start": "09:00",
        "end": "17:00",
        "days": [0, 1, 2, 3, 4],          # Mon-Fri (0=Mon)
    },
    "engine_config": {},                  # serialized EngineConfig override
    "lifetime_stats": {
        "total_runtime_seconds": 0,
        "total_pixels_moved": 0,
        "total_mouse_movements": 0,
        "total_chars_typed": 0,
    },
    "history": [],                        # list of {date, runtime, chars, pixels}
    "window": {"geometry": ""},
}


class Storage:
    def __init__(self, path: str = None):
        self.path = path or os.path.join(config_dir(), "config.json")
        self.data = self._load()

    def _load(self) -> dict:
        data = json.loads(json.dumps(DEFAULTS))  # deep copy of defaults
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                _deep_merge(data, saved)
            except (json.JSONDecodeError, OSError):
                pass
        return data

    def save(self) -> None:
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass

    # --- convenience accessors ------------------------------------------

    def get(self, *keys, default=None):
        node = self.data
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return default
            node = node[k]
        return node

    def set(self, value, *keys) -> None:
        node = self.data
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value

    @property
    def prefs(self) -> dict:
        return self.data["user_preferences"]

    @property
    def lifetime(self) -> dict:
        return self.data["lifetime_stats"]

    def add_session(self, runtime_s, chars, pixels, movements) -> None:
        lt = self.lifetime
        lt["total_runtime_seconds"] += int(runtime_s)
        lt["total_chars_typed"] += int(chars)
        lt["total_pixels_moved"] += int(pixels)
        lt["total_mouse_movements"] += int(movements)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v

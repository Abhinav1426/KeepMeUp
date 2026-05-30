"""
Profile presets — clean structural translation from a named profile to the
core EngineConfig values. The UI selects a profile; this mapper feeds concrete
tunables into the engine without exposing internal variable names.
"""

import copy

from ..core.engine_config import EngineConfig, MouseConfig, KeyboardConfig


def _config(*, wpm, typo, think, mouse_idle, min_dist, max_dist,
            duration_scale=1.0, curvature=1.0, jitter=0.6,
            mouse_enabled=True, keyboard_enabled=True) -> EngineConfig:
    cfg = EngineConfig(
        mouse_enabled=mouse_enabled,
        keyboard_enabled=keyboard_enabled,
        mouse=MouseConfig(
            max_idle=mouse_idle, min_distance=min_dist, max_distance=max_dist,
            duration_scale=duration_scale, curvature=curvature, jitter=jitter,
        ),
        keyboard=KeyboardConfig(typo_prob=typo, long_think_prob=think),
    )
    cfg.set_typing_wpm(wpm)
    return cfg


# Built-in profiles described in the plan.
PROFILES = {
    "Programmer": dict(
        description="Moderate mouse activity, moderate typing, longer think pauses.",
        config=_config(wpm=45, typo=0.02, think=0.15, mouse_idle=75,
                       min_dist=20, max_dist=600),
    ),
    "Active Worker": dict(
        description="Frequent movement, moderate typing, minimal idle.",
        config=_config(wpm=55, typo=0.015, think=0.06, mouse_idle=45,
                       min_dist=40, max_dist=900, duration_scale=0.85),
    ),
    "Reader": dict(
        description="Little typing, occasional movement, long pauses.",
        config=_config(wpm=25, typo=0.005, think=0.25, mouse_idle=75,
                       min_dist=20, max_dist=400, keyboard_enabled=False),
    ),
    "Meeting Mode": dict(
        description="Mostly mouse movement, minimal typing.",
        config=_config(wpm=30, typo=0.01, think=0.1, mouse_idle=60,
                       min_dist=20, max_dist=500, keyboard_enabled=False),
    ),
    "Custom": dict(
        description="User-defined settings.",
        config=_config(wpm=40, typo=0.012, think=0.08, mouse_idle=75,
                       min_dist=20, max_dist=900),
    ),
}

DEFAULT_PROFILE = "Programmer"


def get_profile_config(name: str) -> EngineConfig:
    entry = PROFILES.get(name, PROFILES[DEFAULT_PROFILE])
    return copy.deepcopy(entry["config"])


def profile_names():
    return list(PROFILES.keys())


def profile_description(name: str) -> str:
    return PROFILES.get(name, {}).get("description", "")


# --- Simple Mode style mappings -------------------------------------------

MOUSE_STYLES = {
    "Casual User": dict(mouse_idle=75, min_dist=20, max_dist=500, duration_scale=1.1),
    "Active Worker": dict(mouse_idle=45, min_dist=40, max_dist=900, duration_scale=0.85),
    "Programmer": dict(mouse_idle=75, min_dist=20, max_dist=600, duration_scale=1.0),
    "Reader": dict(mouse_idle=75, min_dist=20, max_dist=400, duration_scale=1.2),
}

TYPING_STYLES = {
    "Slow": 28,
    "Normal": 45,
    "Fast": 70,
}

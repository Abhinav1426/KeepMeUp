"""
Engine configuration object.

Holds every tunable the original `keepmeup_cli.py` exposed as module-level
constants, now as an instance so the UI / services can build and pass them
into the worker threads without touching engine internals.

The defaults below are *exactly* the values from the original script, so the
simulation behaviour is unchanged out of the box.
"""

from dataclasses import dataclass, asdict, field


@dataclass
class MouseConfig:
    # --- timing / idle (Teams away guard) ---
    max_idle: float = 75.0              # MOUSE_MAX_IDLE
    # --- movement kinematics ---
    min_distance: float = 20.0          # short-hop lower bound
    max_distance: float = 900.0         # long-hop upper bound
    duration_scale: float = 1.0         # multiplies computed move duration
    curvature: float = 1.0              # multiplies bezier control-point offset
    jitter: float = 0.6                 # per-step micro jitter (px)
    speed_multiplier: float = 1.0       # >1 = faster moves (shorter duration)
    trajectory: str = "bezier"          # bezier | linear | random
    margin: int = 40                    # clamp margin from screen edge


@dataclass
class KeyboardConfig:
    # --- per character delay (TYPE_DELAY_MIN/MAX) ---
    type_delay_min: float = 0.09
    type_delay_max: float = 0.28
    punct_extra_min: float = 0.10
    punct_extra_max: float = 0.40
    newline_extra_min: float = 0.25
    newline_extra_max: float = 1.10
    # --- thinking pauses ---
    long_think_prob: float = 0.08
    long_think_min: float = 2.5
    long_think_max: float = 6.0
    # --- typo simulation ---
    typo_prob: float = 0.012
    # --- chunk pauses (paragraph blocks) ---
    chunk_pause_min: float = 15.0
    chunk_pause_max: float = 60.0


@dataclass
class EngineConfig:
    startup_delay: int = 30             # STARTUP_DELAY_SECONDS countdown
    content_file: str = "content.txt"
    mouse_enabled: bool = True
    keyboard_enabled: bool = True
    mouse: MouseConfig = field(default_factory=MouseConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EngineConfig":
        data = dict(data or {})
        mouse = MouseConfig(**(data.pop("mouse", {}) or {}))
        keyboard = KeyboardConfig(**(data.pop("keyboard", {}) or {}))
        return cls(mouse=mouse, keyboard=keyboard, **data)

    # --- friendly translations (UI never sees raw var names) -------------

    @property
    def typing_wpm(self) -> int:
        """Approx words-per-minute from the avg per-char delay.

        avg chars/word ~= 5 (+1 space). WPM = 60 / (6 * avg_delay).
        """
        avg = (self.keyboard.type_delay_min + self.keyboard.type_delay_max) / 2
        if avg <= 0:
            return 0
        return max(1, round(60.0 / (6.0 * avg)))

    def set_typing_wpm(self, wpm: int) -> None:
        """Map a target WPM back onto the min/max per-char delay window,
        preserving the original ~3.1x spread between min and max."""
        wpm = max(5, min(200, int(wpm)))
        avg = 60.0 / (6.0 * wpm)
        # original ratio: min=0.09 max=0.28 -> spread factor ~0.51 / 1.49
        self.keyboard.type_delay_min = round(avg * 0.51, 3)
        self.keyboard.type_delay_max = round(avg * 1.49, 3)

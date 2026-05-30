"""
Mouse engine — refactored from the original `keepmeup_cli.py` into a QThread worker.

The Bezier math, easing, target picking and jitter are preserved verbatim from
the original script; only the surrounding loop is adapted to:
  * run inside a QThread,
  * honour thread-safe pause / stop flags with instant responsiveness,
  * emit telemetry (pixel distance + movement count) via Qt signals.
"""

import ctypes
import math
import random
import sys
import time

from PySide6.QtCore import QThread, Signal

from pynput.mouse import Controller as MouseController

from .engine_config import MouseConfig


def get_screen_size():
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return 1920, 1080


# --- preserved pure helpers -------------------------------------------------

def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def cubic_bezier(p0, p1, p2, p3, t):
    u = 1 - t
    x = (u ** 3) * p0[0] + 3 * (u ** 2) * t * p1[0] + 3 * u * (t ** 2) * p2[0] + (t ** 3) * p3[0]
    y = (u ** 3) * p0[1] + 3 * (u ** 2) * t * p1[1] + 3 * u * (t ** 2) * p2[1] + (t ** 3) * p3[1]
    return x, y


class MouseWorker(QThread):
    """Runs the continuous human-like mouse movement loop."""

    moved = Signal(float)          # pixel distance of the completed move
    status = Signal(str)           # human readable status line

    def __init__(self, config: MouseConfig, startup_delay: int = 30, parent=None):
        super().__init__(parent)
        self.cfg = config
        self.startup_delay = startup_delay
        self._mouse = MouseController()
        self._stop = False
        self._paused = False
        self.screen_w, self.screen_h = get_screen_size()

    # --- control ---------------------------------------------------------

    def stop(self):
        self._stop = True

    def set_paused(self, paused: bool):
        self._paused = paused

    def update_config(self, config: MouseConfig):
        self.cfg = config

    # --- interruptible / pause-aware sleep ------------------------------

    def _sleep(self, seconds):
        end = time.perf_counter() + seconds
        while not self._stop:
            if self._paused:
                time.sleep(0.05)
                end += 0.05  # don't burn idle budget while paused
                continue
            remaining = end - time.perf_counter()
            if remaining <= 0:
                return
            time.sleep(min(0.1, remaining))

    # --- preserved movement logic (now config-driven) -------------------

    def clamp_point(self, x, y):
        m = self.cfg.margin
        x = max(m, min(self.screen_w - m, x))
        y = max(m, min(self.screen_h - m, y))
        return x, y

    def pick_target(self, cur_x, cur_y):
        roll = random.random()
        lo, hi = self.cfg.min_distance, self.cfg.max_distance
        if roll < 0.55:
            radius = random.uniform(lo, max(lo, min(120, hi)))
        elif roll < 0.9:
            radius = random.uniform(min(120, hi), max(120, min(400, hi)))
        else:
            radius = random.uniform(min(400, hi), hi)
        angle = random.uniform(0, 2 * math.pi)
        return self.clamp_point(cur_x + radius * math.cos(angle),
                                cur_y + radius * math.sin(angle))

    def human_mouse_move(self, target_x, target_y):
        start_x, start_y = self._mouse.position
        dx, dy = target_x - start_x, target_y - start_y
        distance = math.hypot(dx, dy)
        if distance < 1:
            return 0.0

        perp_x, perp_y = -dy / distance, dx / distance
        curve = self.cfg.curvature
        offset_scale = distance * random.uniform(0.08, 0.25) * curve
        s1 = random.choice((-1, 1))
        s2 = random.choice((-1, 1))

        if self.cfg.trajectory == "linear":
            offset_scale = 0.0

        c1 = (start_x + dx * random.uniform(0.2, 0.4) + perp_x * offset_scale * s1,
              start_y + dy * random.uniform(0.2, 0.4) + perp_y * offset_scale * s1)
        c2 = (start_x + dx * random.uniform(0.6, 0.8) + perp_x * offset_scale * s2 * 0.6,
              start_y + dy * random.uniform(0.6, 0.8) + perp_y * offset_scale * s2 * 0.6)

        duration = min(2.5, max(0.25, 0.0015 * distance + random.uniform(0.15, 0.55)))
        duration *= self.cfg.duration_scale / max(0.1, self.cfg.speed_multiplier)
        steps = max(20, int(duration * random.uniform(55, 85)))

        p0 = (start_x, start_y)
        p3 = (target_x, target_y)
        jit = self.cfg.jitter
        extra_jitter = self.cfg.jitter * 4 if self.cfg.trajectory == "random" else jit

        t0 = time.perf_counter()
        for i in range(1, steps + 1):
            if self._stop:
                return distance
            while self._paused and not self._stop:
                time.sleep(0.05)
                t0 += 0.05
            raw_t = i / steps
            t = ease_in_out(raw_t)
            x, y = cubic_bezier(p0, c1, c2, p3, t)
            x += random.uniform(-extra_jitter, extra_jitter)
            y += random.uniform(-extra_jitter, extra_jitter)
            self._mouse.position = (int(x), int(y))
            sleep_for = (t0 + duration * raw_t) - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)

        if random.random() < 0.35:
            sx, sy = self._mouse.position
            self._mouse.position = (sx + random.randint(-2, 2), sy + random.randint(-2, 2))
        return distance

    # --- thread entry ----------------------------------------------------

    def run(self):
        self._sleep(self.startup_delay)
        self.status.emit("Mouse active")
        while not self._stop:
            while self._paused and not self._stop:
                time.sleep(0.1)
            if self._stop:
                break
            cur_x, cur_y = self._mouse.position
            tx, ty = self.pick_target(cur_x, cur_y)
            distance = self.human_mouse_move(tx, ty)
            if distance:
                self.moved.emit(distance)

            roll = random.random()
            if roll < 0.65:
                pause = random.uniform(2.0, 10.0)
            elif roll < 0.95:
                pause = random.uniform(10.0, 35.0)
            else:
                pause = random.uniform(35.0, self.cfg.max_idle)
            self._sleep(pause)
        self.status.emit("Mouse stopped")

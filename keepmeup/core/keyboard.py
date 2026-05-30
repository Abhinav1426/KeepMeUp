"""
Keyboard engine — refactored from the original `keepmeup_cli.py` into a QThread worker.

Typing cadence, punctuation/newline pauses, thinking pauses, typo + backspace
correction and chunk-based looping are preserved from the original script. The
loop now runs inside a QThread, honours pause/stop flags instantly, and emits
character-typed telemetry.
"""

import os
import random
import time

from PySide6.QtCore import QThread, Signal

from pynput.keyboard import Controller as KeyboardController, Key

from .engine_config import KeyboardConfig


DEFAULT_CONTENT = '''# Paste anything you want typed in this file.
# It will be typed character-by-character into whatever window is focused.
# When the file is exhausted, it loops from the top.

def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''


def load_content(path: str) -> str:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONTENT)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.strip():
        text = DEFAULT_CONTENT
    return text


def split_into_chunks(text: str):
    """Split on blank lines into paragraph-ish chunks (preserved logic)."""
    raw = text.split("\n\n")
    chunks = []
    for r in raw:
        r = r.strip("\n")
        if r:
            chunks.append(r + "\n\n")
    return chunks or [text]


class KeyboardWorker(QThread):
    """Streams content from a file into the focused window, human-like."""

    typed = Signal(int)            # number of characters typed in this batch
    status = Signal(str)
    countdown = Signal(int)        # seconds remaining in the startup countdown

    def __init__(self, config: KeyboardConfig, content_file: str,
                 startup_delay: int = 30, parent=None):
        super().__init__(parent)
        self.cfg = config
        self.content_file = content_file
        self.startup_delay = startup_delay
        self._keyboard = KeyboardController()
        self._stop = False
        self._paused = False

    # --- control ---------------------------------------------------------

    def stop(self):
        self._stop = True

    def set_paused(self, paused: bool):
        self._paused = paused

    def update_config(self, config: KeyboardConfig):
        self.cfg = config

    def _sleep(self, seconds):
        end = time.perf_counter() + seconds
        while not self._stop:
            if self._paused:
                time.sleep(0.05)
                end += 0.05
                continue
            remaining = end - time.perf_counter()
            if remaining <= 0:
                return
            time.sleep(min(0.1, remaining))

    # --- preserved typing logic -----------------------------------------

    def type_char(self, ch):
        try:
            if ch == "\n":
                self._keyboard.press(Key.enter)
                self._keyboard.release(Key.enter)
            elif ch == "\t":
                self._keyboard.press(Key.tab)
                self._keyboard.release(Key.tab)
            else:
                self._keyboard.type(ch)
        except Exception:
            pass

    def type_chunk(self, chunk):
        cfg = self.cfg
        count = 0
        for ch in chunk:
            if self._stop:
                break
            while self._paused and not self._stop:
                time.sleep(0.05)
            # Occasional typo + correction on letters
            if ch.isalpha() and random.random() < cfg.typo_prob:
                self.type_char(random.choice("abcdefghijklmnopqrstuvwxyz"))
                time.sleep(random.uniform(0.12, 0.30))
                self._keyboard.press(Key.backspace)
                self._keyboard.release(Key.backspace)
                time.sleep(random.uniform(0.10, 0.25))

            self.type_char(ch)
            count += 1

            delay = random.uniform(cfg.type_delay_min, cfg.type_delay_max)
            if ch in ",.;:":
                delay += random.uniform(cfg.punct_extra_min, cfg.punct_extra_max)
            if ch == "\n":
                delay += random.uniform(cfg.newline_extra_min, cfg.newline_extra_max)
                if random.random() < cfg.long_think_prob:
                    delay += random.uniform(cfg.long_think_min, cfg.long_think_max)
            time.sleep(delay)

            # flush telemetry every ~16 chars to keep the UI lively but cheap
            if count >= 16:
                self.typed.emit(count)
                count = 0
        if count:
            self.typed.emit(count)

    # --- thread entry ----------------------------------------------------

    def run(self):
        text = load_content(self.content_file)
        chunks = split_into_chunks(text)
        self.status.emit(f"Loaded {len(chunks)} chunk(s)")

        # Startup countdown so the user can focus their editor.
        for remaining in range(self.startup_delay, 0, -1):
            if self._stop:
                return
            self.countdown.emit(remaining)
            time.sleep(1)
        self.countdown.emit(0)
        self.status.emit("Keyboard active")

        idx = 0
        while not self._stop:
            while self._paused and not self._stop:
                time.sleep(0.1)
            if self._stop:
                break
            self.type_chunk(chunks[idx])
            idx = (idx + 1) % len(chunks)
            self._sleep(random.uniform(self.cfg.chunk_pause_min, self.cfg.chunk_pause_max))
        self.status.emit("Keyboard stopped")

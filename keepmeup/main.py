"""
KeepMeUp — application bootstrap.

Loads persisted settings, builds the EngineConfig, wires the service layer and
launches the PySide6 desktop shell. Includes a single-instance lock so only one
copy controls the mouse/keyboard at a time.
"""

import os
import sys

# allow running as `python keepmeup/main.py` or `python -m keepmeup.main`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import Qt, QSharedMemory
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from keepmeup.components import build_stylesheet
from keepmeup.core import EngineConfig
from keepmeup.services import Storage, EngineController, Scheduler, profiles
from keepmeup.views import MainWindow


def bundled_content_path() -> str:
    """The content.txt that ships with the app.

    When frozen by PyInstaller the file is unpacked into the bundle root
    (``sys._MEIPASS``); when running from source it lives one dir above the
    package.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base, "content.txt")
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "content.txt"))


def make_content_resolver(storage: Storage):
    def resolve() -> str:
        chosen = storage.get("content", "file", default="")
        if chosen and os.path.exists(chosen):
            return chosen
        return bundled_content_path()
    return resolve


def build_config(storage: Storage) -> EngineConfig:
    saved = storage.get("engine_config", default={})
    if saved:
        cfg = EngineConfig.from_dict(saved)
    else:
        cfg = profiles.get_profile_config(storage.prefs.get("current_profile", profiles.DEFAULT_PROFILE))
    prefs = storage.prefs
    cfg.mouse_enabled = prefs.get("mouse_enabled", True)
    cfg.keyboard_enabled = prefs.get("keyboard_enabled", True)
    cfg.startup_delay = prefs.get("startup_delay", 30)
    return cfg


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KeepMeUp")
    app.setQuitOnLastWindowClosed(False)  # keep running in tray

    # single-instance guard
    lock = QSharedMemory("KeepMeUp-SingleInstance-Lock")
    if not lock.create(1):
        QMessageBox.information(None, "KeepMeUp", "KeepMeUp is already running.")
        return 0

    app.setStyleSheet(build_stylesheet())
    app.setFont(QFont("Inter", 10))

    storage = Storage()
    resolver = make_content_resolver(storage)
    config = build_config(storage)

    controller = EngineController(config, resolver)
    scheduler = Scheduler()

    window = MainWindow(controller, storage, scheduler, resolver)
    window.show()

    exit_code = app.exec()
    controller.stop()
    lock.detach()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

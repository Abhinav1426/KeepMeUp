"""
Schedule view — automated execution windows. Configures the Scheduler service
which auto starts/stops the engine on the chosen days and time window.
"""

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTimeEdit, QPushButton, QButtonGroup,
)

from ..components import Card, ToggleSwitch, Color


DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class ScheduleView(QWidget):
    def __init__(self, storage, scheduler, on_changed, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.scheduler = scheduler
        self._on_changed = on_changed
        sched = storage.data["schedule"]

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        head = QVBoxLayout()
        head.setSpacing(2)
        title = QLabel("Schedule")
        title.setObjectName("Headline")
        sub = QLabel("Automate when the engine runs.")
        sub.setObjectName("SubHeadline")
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        card = Card("Recurring Schedule", "◷")

        enable_row = QHBoxLayout()
        enable_lbl = QLabel("Enable schedule")
        enable_lbl.setStyleSheet("font-weight: 600;")
        self.enable = ToggleSwitch(sched["enabled"])
        self.enable.toggled.connect(lambda _: self._apply())
        enable_row.addWidget(enable_lbl)
        enable_row.addStretch()
        enable_row.addWidget(self.enable)
        card.body_layout().addLayout(enable_row)

        time_row = QHBoxLayout()
        time_row.setSpacing(16)
        start_col = QVBoxLayout()
        start_col.addWidget(self._caps("START TIME"))
        self.start_time = QTimeEdit(QTime.fromString(sched["start"], "HH:mm"))
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.timeChanged.connect(lambda _: self._apply())
        start_col.addWidget(self.start_time)
        end_col = QVBoxLayout()
        end_col.addWidget(self._caps("STOP TIME"))
        self.end_time = QTimeEdit(QTime.fromString(sched["end"], "HH:mm"))
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.timeChanged.connect(lambda _: self._apply())
        end_col.addWidget(self.end_time)
        time_row.addLayout(start_col)
        time_row.addLayout(end_col)
        time_row.addStretch()
        card.body_layout().addLayout(time_row)

        card.add(self._caps("DAYS OF WEEK"))
        days_row = QHBoxLayout()
        days_row.setSpacing(8)
        self.day_buttons = []
        for i, name in enumerate(DAYS):
            b = QPushButton(name)
            b.setObjectName("Choice")
            b.setCheckable(True)
            b.setChecked(i in sched["days"])
            b.clicked.connect(lambda _: self._apply())
            self.day_buttons.append(b)
            days_row.addWidget(b)
        days_row.addStretch()
        card.body_layout().addLayout(days_row)

        self.summary = QLabel()
        self.summary.setStyleSheet(f"color: {Color.PRIMARY_LIGHT}; font-size: 13px;")
        card.add(self.summary)

        root.addWidget(card)
        root.addStretch()
        self._update_summary()

    def _caps(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("LabelCaps")
        return lbl

    def _apply(self):
        sched = self.storage.data["schedule"]
        sched["enabled"] = self.enable.isChecked()
        sched["start"] = self.start_time.time().toString("HH:mm")
        sched["end"] = self.end_time.time().toString("HH:mm")
        sched["days"] = [i for i, b in enumerate(self.day_buttons) if b.isChecked()]
        self.storage.save()
        self.scheduler.configure(sched["enabled"], sched["start"], sched["end"], sched["days"])
        self._update_summary()
        self._on_changed()

    def _update_summary(self):
        self.summary.setText("⏱  " + self.scheduler.summary())

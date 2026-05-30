"""Reusable card / tile / indicator widgets for the Precision Utility theme."""

from PySide6.QtCore import Qt, QPropertyAnimation, Property, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy,
)

from .theme import Color, FONT_MONO


class Card(QFrame):
    """A surface container with an optional caps-styled header strip."""

    def __init__(self, title: str = None, icon: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        if title:
            header = QFrame()
            header.setObjectName("CardHeader")
            h = QHBoxLayout(header)
            h.setContentsMargins(16, 10, 16, 10)
            label = QLabel(f"{icon + '  ' if icon else ''}{title.upper()}")
            label.setObjectName("LabelCaps")
            label.setStyleSheet(f"color: {Color.PRIMARY_LIGHT};")
            h.addWidget(label)
            h.addStretch()
            self._header_layout = h
            outer.addWidget(header)

        self.body = QWidget()
        self._body_layout = QVBoxLayout(self.body)
        self._body_layout.setContentsMargins(16, 16, 16, 16)
        self._body_layout.setSpacing(14)
        outer.addWidget(self.body)

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def add(self, widget):
        self._body_layout.addWidget(widget)
        return widget

    def header_layout(self):
        return getattr(self, "_header_layout", None)


class StatTile(QFrame):
    """A small metric tile: caption + big mono value."""

    def __init__(self, caption: str, value: str = "—", accent: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("StatTile")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)

        self.caption = QLabel(caption.upper())
        self.caption.setObjectName("LabelCaps")
        self.value = QLabel(value)
        self.value.setObjectName("Mono")
        col = accent or Color.PRIMARY_LIGHT
        self.value.setStyleSheet(
            f"font-family: {FONT_MONO}; font-size: 22px; font-weight: 600; color: {col};")
        lay.addWidget(self.caption)
        lay.addWidget(self.value)

    def set_value(self, text: str):
        self.value.setText(text)


class StatusDot(QWidget):
    """A small glowing status indicator dot."""

    def __init__(self, color: str = Color.ON_SURFACE_DIM, diameter: int = 10, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._d = diameter
        self.setFixedSize(diameter + 6, diameter + 6)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # soft glow
        glow = QColor(self._color)
        glow.setAlpha(70)
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect())
        # core
        p.setBrush(QBrush(self._color))
        m = 3
        p.drawEllipse(self.rect().adjusted(m, m, -m, -m))


class ToggleSwitch(QWidget):
    """A pill-style animated on/off switch (track + thumb)."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._offset = 1.0 if checked else 0.0
        self.setFixedSize(42, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)

    def isChecked(self):
        return self._checked

    def setChecked(self, value: bool):
        value = bool(value)
        if value == self._checked:
            return
        self._checked = value
        self._animate()

    def _animate(self):
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if self._checked else 0.0)
        self._anim.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate()
            self.toggled.emit(self._checked)

    def get_offset(self):
        return self._offset

    def set_offset(self, v):
        self._offset = v
        self.update()

    offset = Property(float, get_offset, set_offset)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(0, 0, -1, -1)
        track_on = QColor(Color.PRIMARY)
        track_off = QColor(Color.SURFACE_HIGHEST)
        track = QColor(
            int(track_off.red() + (track_on.red() - track_off.red()) * self._offset),
            int(track_off.green() + (track_on.green() - track_off.green()) * self._offset),
            int(track_off.blue() + (track_on.blue() - track_off.blue()) * self._offset),
        )
        p.setBrush(QBrush(track))
        border = QColor(Color.PRIMARY if self._checked else Color.OUTLINE_VARIANT)
        p.setPen(border)
        p.drawRoundedRect(QRectF(r), r.height() / 2, r.height() / 2)

        # thumb
        d = r.height() - 6
        x = 3 + self._offset * (r.width() - d - 6)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#ffffff" if self._checked else Color.OUTLINE)))
        p.drawEllipse(QRectF(x, 3, d, d))


def hline(color: str = Color.OUTLINE_VARIANT) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {color}; border: none;")
    return line

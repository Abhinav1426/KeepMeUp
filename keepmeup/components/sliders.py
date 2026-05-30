"""Labeled slider control — a row with a caption label and a live value readout."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider

from .theme import Color, FONT_MONO


class LabeledSlider(QWidget):
    """Label + value readout above a horizontal slider.

    Works in integer steps internally; an optional `scale` and `fmt` map the
    integer to the displayed value so floats are supported.
    """

    valueChanged = Signal(float)

    def __init__(self, label, minimum, maximum, value, step=1,
                 scale=1.0, suffix="", fmt=None, parent=None):
        super().__init__(parent)
        self._scale = scale
        self._suffix = suffix
        self._fmt = fmt

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        top = QHBoxLayout()
        self.label = QLabel(label)
        self.label.setStyleSheet(f"color: {Color.ON_SURFACE}; font-size: 12px; font-weight: 500;")
        self.readout = QLabel()
        self.readout.setStyleSheet(
            f"font-family: {FONT_MONO}; color: {Color.PRIMARY_LIGHT}; font-size: 12px;")
        top.addWidget(self.label)
        top.addStretch()
        top.addWidget(self.readout)
        lay.addLayout(top)

        self.slider = QSlider(Qt.Horizontal)
        self._imin = int(round(minimum / scale))
        self._imax = int(round(maximum / scale))
        self.slider.setRange(self._imin, self._imax)
        self.slider.setSingleStep(max(1, int(round(step / scale))))
        self.slider.setValue(int(round(value / scale)))
        self.slider.valueChanged.connect(self._on_change)
        lay.addWidget(self.slider)

        self._update_readout(self.slider.value())

    def _display(self, ivalue):
        real = ivalue * self._scale
        if self._fmt:
            return self._fmt(real)
        if self._scale == 1.0:
            return f"{int(real)}{self._suffix}"
        return f"{real:.2f}{self._suffix}"

    def _update_readout(self, ivalue):
        self.readout.setText(self._display(ivalue))

    def _on_change(self, ivalue):
        self._update_readout(ivalue)
        self.valueChanged.emit(ivalue * self._scale)

    def value(self) -> float:
        return self.slider.value() * self._scale

    def setValue(self, real_value: float):
        self.slider.setValue(int(round(real_value / self._scale)))

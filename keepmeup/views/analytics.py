"""
Analytics view — live session telemetry, an activity-density graph and
persisted lifetime statistics.
"""

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout

from ..components import Card, StatTile, Color
from ..services import State
from ..services.telemetry import Telemetry


pg.setConfigOptions(antialias=True)


class AnalyticsView(QWidget):
    def __init__(self, controller, storage, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.storage = storage

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        head = QVBoxLayout()
        head.setSpacing(2)
        title = QLabel("Analytics")
        title.setObjectName("Headline")
        sub = QLabel("Session tracking and statistics.")
        sub.setObjectName("SubHeadline")
        head.addWidget(title)
        head.addWidget(sub)
        root.addLayout(head)

        # session metrics
        session = Card("Current Session", "▣")
        grid = QGridLayout()
        grid.setSpacing(12)
        self.t_runtime = StatTile("Runtime", "00:00:00")
        self.t_chars = StatTile("Characters typed", "0")
        self.t_words = StatTile("Words typed", "0")
        self.t_dist = StatTile("Mouse distance", "0 px")
        self.t_moves = StatTile("Mouse movements", "0")
        self.t_wpm = StatTile("Average WPM", "0")
        for i, tile in enumerate([self.t_runtime, self.t_chars, self.t_words,
                                  self.t_dist, self.t_moves, self.t_wpm]):
            grid.addWidget(tile, i // 3, i % 3)
        session.body_layout().addLayout(grid)
        root.addWidget(session)

        # graph
        graph_card = Card("Activity Density (last 60s)", "📈")
        self.plot = pg.PlotWidget()
        self.plot.setBackground(Color.SURFACE_LOWEST)
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.plot.getPlotItem().showGrid(x=False, y=True, alpha=0.15)
        self.plot.getAxis("left").setPen(Color.OUTLINE_VARIANT)
        self.plot.getAxis("bottom").setPen(Color.OUTLINE_VARIANT)
        self.plot.getAxis("left").setTextPen(Color.ON_SURFACE_VARIANT)
        self.plot.getAxis("bottom").setTextPen(Color.ON_SURFACE_VARIANT)
        self.plot.setMinimumHeight(180)
        self._bars = pg.BarGraphItem(x=range(60), height=[0] * 60, width=0.8, brush=Color.PRIMARY)
        self.plot.addItem(self._bars)
        graph_card.add(self.plot)
        root.addWidget(graph_card, 1)

        # lifetime
        lifetime = Card("Lifetime Totals", "∑")
        lgrid = QGridLayout()
        lgrid.setSpacing(12)
        self.l_runtime = StatTile("Total runtime", "0h", accent=Color.PRIMARY_LIGHT)
        self.l_chars = StatTile("Total characters", "0", accent=Color.PRIMARY_LIGHT)
        self.l_dist = StatTile("Total distance", "0 px", accent=Color.PRIMARY_LIGHT)
        self.l_moves = StatTile("Total movements", "0", accent=Color.PRIMARY_LIGHT)
        for i, tile in enumerate([self.l_runtime, self.l_chars, self.l_dist, self.l_moves]):
            lgrid.addWidget(tile, 0, i)
        lifetime.body_layout().addLayout(lgrid)
        root.addWidget(lifetime)

        self.controller.tick.connect(self.refresh)
        self.controller.telemetry.updated.connect(self.refresh)
        self.refresh()

    def refresh(self):
        t: Telemetry = self.controller.telemetry
        self.t_runtime.set_value(Telemetry.fmt_duration(t.runtime_seconds))
        self.t_chars.set_value(f"{t.chars_typed:,}")
        self.t_words.set_value(f"{t.words_typed:,}")
        self.t_dist.set_value(f"{int(t.pixels_moved):,} px")
        self.t_moves.set_value(f"{t.mouse_movements:,}")
        self.t_wpm.set_value(f"{t.average_wpm:.0f}")

        buf = t.activity_buffer()
        self._bars.setOpts(x=range(len(buf)), height=buf)

        lt = self.storage.lifetime
        # include the in-progress session live
        live = 1 if self.controller.state != State.STOPPED else 0
        total_runtime = lt["total_runtime_seconds"] + (t.runtime_seconds if live else 0)
        self.l_runtime.set_value(f"{total_runtime / 3600:.1f}h")
        self.l_chars.set_value(f"{lt['total_chars_typed'] + t.chars_typed:,}")
        self.l_dist.set_value(f"{int(lt['total_pixels_moved'] + t.pixels_moved):,} px")
        self.l_moves.set_value(f"{lt['total_mouse_movements'] + t.mouse_movements:,}")

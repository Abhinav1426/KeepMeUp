"""
Behavior view — Simple Mode and Power User Mode configuration.

Simple Mode exposes friendly concepts (Mouse Style, Typing Style, Activity,
Randomness). Power User Mode exposes the full kinematic / keystroke controls.
Internal variable names are never shown to the user.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QButtonGroup,
)

from ..components import Card, LabeledSlider, Color, hline
from ..services import profiles


class SegmentedControl(QWidget):
    """A row of mutually-exclusive choice buttons."""

    def __init__(self, options, current, on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._buttons = {}
        for opt in options:
            b = QPushButton(opt)
            b.setObjectName("Choice")
            b.setCheckable(True)
            b.setChecked(opt == current)
            b.clicked.connect(lambda _=False, o=opt: self._select(o))
            self.group.addButton(b)
            self._buttons[opt] = b
            lay.addWidget(b)

    def _select(self, opt):
        self._buttons[opt].setChecked(True)
        self._on_change(opt)

    def set_current(self, opt):
        if opt in self._buttons:
            self._buttons[opt].setChecked(True)


class BehaviorView(QWidget):
    def __init__(self, controller, storage, on_config_changed, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.storage = storage
        self._on_config_changed = on_config_changed
        self._mode = storage.prefs.get("mode", "simple")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        head = QHBoxLayout()
        head_col = QVBoxLayout()
        head_col.setSpacing(2)
        title = QLabel("Behavior")
        title.setObjectName("Headline")
        sub = QLabel("Configure how the activity simulation feels.")
        sub.setObjectName("SubHeadline")
        head_col.addWidget(title)
        head_col.addWidget(sub)
        head.addLayout(head_col)
        head.addStretch()

        self.mode_toggle = SegmentedControl(
            ["Simple", "Power User"],
            "Simple" if self._mode == "simple" else "Power User",
            self._switch_mode)
        head.addWidget(self.mode_toggle)
        root.addLayout(head)

        # profile selector row
        prof_row = QHBoxLayout()
        prof_lbl = QLabel("Profile")
        prof_lbl.setStyleSheet("font-weight: 600;")
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(profiles.profile_names())
        self.profile_combo.setCurrentText(storage.prefs.get("current_profile", profiles.DEFAULT_PROFILE))
        self.profile_combo.currentTextChanged.connect(self._apply_profile)
        self.profile_combo.setMinimumWidth(200)
        self.profile_desc = QLabel(profiles.profile_description(self.profile_combo.currentText()))
        self.profile_desc.setStyleSheet(f"color: {Color.ON_SURFACE_VARIANT}; font-size: 13px;")
        prof_row.addWidget(prof_lbl)
        prof_row.addWidget(self.profile_combo)
        prof_row.addWidget(self.profile_desc)
        prof_row.addStretch()
        root.addLayout(prof_row)

        # scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 8, 0)
        self.body_layout.setSpacing(20)
        scroll.setWidget(self.body)
        root.addWidget(scroll, 1)

        self.simple_panel = self._build_simple()
        self.power_panel = self._build_power()
        self.body_layout.addWidget(self.simple_panel)
        self.body_layout.addWidget(self.power_panel)
        self.body_layout.addStretch()

        self._apply_mode_visibility()

    # --- Simple Mode -----------------------------------------------------

    def _build_simple(self):
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        mouse = Card("Mouse", "🖱")
        m_lbl = QLabel("Movement Style")
        m_lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.mouse_style = SegmentedControl(
            list(profiles.MOUSE_STYLES.keys()), "Programmer", self._simple_mouse_style)
        mouse.add(m_lbl)
        mouse.add(self.mouse_style)
        lay.addWidget(mouse)

        kbd = Card("Keyboard", "⌨")
        k_lbl = QLabel("Typing Style")
        k_lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.typing_style = SegmentedControl(
            list(profiles.TYPING_STYLES.keys()), "Normal", self._simple_typing_style)
        kbd.add(k_lbl)
        kbd.add(self.typing_style)
        lay.addWidget(kbd)

        activity = Card("Activity", "📊")
        self.activity_slider = LabeledSlider("Activity Level", 1, 10, 6, suffix="")
        self.activity_slider.valueChanged.connect(self._simple_activity)
        self.randomness_slider = LabeledSlider("Randomness", 1, 10, 5, suffix="")
        self.randomness_slider.valueChanged.connect(self._simple_randomness)
        activity.add(self.activity_slider)
        activity.add(self.randomness_slider)
        lay.addWidget(activity)
        return wrap

    def _simple_mouse_style(self, style):
        params = profiles.MOUSE_STYLES[style]
        m = self.controller.config.mouse
        m.max_idle = params["mouse_idle"]
        m.min_distance = params["min_dist"]
        m.max_distance = params["max_dist"]
        m.duration_scale = params["duration_scale"]
        self._mark_custom()

    def _simple_typing_style(self, style):
        wpm = profiles.TYPING_STYLES[style]
        self.controller.config.set_typing_wpm(wpm)
        self._mark_custom()

    def _simple_activity(self, level):
        # higher activity -> shorter idle caps
        m = self.controller.config.mouse
        m.max_idle = max(20.0, 110.0 - level * 9.0)
        self.controller.config.keyboard.chunk_pause_max = max(15.0, 90.0 - level * 7.0)
        self._mark_custom()

    def _simple_randomness(self, level):
        m = self.controller.config.mouse
        m.jitter = 0.2 + level * 0.12
        self.controller.config.keyboard.long_think_prob = 0.02 + level * 0.012
        self._mark_custom()

    # --- Power User Mode -------------------------------------------------

    def _build_power(self):
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)
        cfg = self.controller.config

        # Mouse kinematics
        mouse = Card("Mouse Kinematics", "🖱")
        traj_lbl = QLabel("Trajectory Algorithm")
        traj_lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
        self.traj = SegmentedControl(
            ["Bezier", "Linear", "Random"],
            cfg.mouse.trajectory.capitalize(), self._set_trajectory)
        mouse.add(traj_lbl)
        mouse.add(self.traj)
        mouse.add(hline())

        self.p_speed = self._pslider(mouse, "Speed Multiplier", 0.2, 3.0, cfg.mouse.speed_multiplier,
                                     0.1, suffix="x", setter=self._set_mouse_attr("speed_multiplier"))
        self.p_min = self._pslider(mouse, "Min Distance", 5, 400, cfg.mouse.min_distance,
                                   5, suffix=" px", setter=self._set_mouse_attr("min_distance"))
        self.p_max = self._pslider(mouse, "Max Distance", 100, 1500, cfg.mouse.max_distance,
                                   50, suffix=" px", setter=self._set_mouse_attr("max_distance"))
        self.p_dur = self._pslider(mouse, "Movement Duration", 0.3, 2.5, cfg.mouse.duration_scale,
                                   0.1, suffix="x", setter=self._set_mouse_attr("duration_scale"))
        self.p_curv = self._pslider(mouse, "Bezier Curvature", 0.0, 2.5, cfg.mouse.curvature,
                                    0.1, suffix="x", setter=self._set_mouse_attr("curvature"))
        self.p_jit = self._pslider(mouse, "Jitter", 0.0, 3.0, cfg.mouse.jitter,
                                   0.1, suffix=" px", setter=self._set_mouse_attr("jitter"))
        self.p_idle = self._pslider(mouse, "Idle Time (cap)", 10, 180, cfg.mouse.max_idle,
                                    5, suffix=" s", setter=self._set_mouse_attr("max_idle"))
        lay.addWidget(mouse)

        # Keyboard
        kbd = Card("Keystroke Injection", "⌨")
        self.p_dmin = self._pslider(kbd, "Minimum Delay", 0.02, 0.5, cfg.keyboard.type_delay_min,
                                    0.01, suffix=" s", setter=self._set_kbd_attr("type_delay_min"))
        self.p_dmax = self._pslider(kbd, "Maximum Delay", 0.05, 0.8, cfg.keyboard.type_delay_max,
                                    0.01, suffix=" s", setter=self._set_kbd_attr("type_delay_max"))
        self.p_typo = self._pslider(kbd, "Typo Chance", 0.0, 0.10, cfg.keyboard.typo_prob,
                                    0.005, fmt=lambda v: f"{v*100:.1f}%",
                                    setter=self._set_kbd_attr("typo_prob"))
        self.p_think = self._pslider(kbd, "Think Pause Chance", 0.0, 0.5, cfg.keyboard.long_think_prob,
                                     0.01, fmt=lambda v: f"{v*100:.0f}%",
                                     setter=self._set_kbd_attr("long_think_prob"))
        self.p_chunk = self._pslider(kbd, "Chunk Pause (max)", 5, 180, cfg.keyboard.chunk_pause_max,
                                     5, suffix=" s", setter=self._set_kbd_attr("chunk_pause_max"))
        self.p_punct = self._pslider(kbd, "Punctuation Delay (max)", 0.0, 1.0, cfg.keyboard.punct_extra_max,
                                     0.05, suffix=" s", setter=self._set_kbd_attr("punct_extra_max"))
        lay.addWidget(kbd)
        return wrap

    def _pslider(self, card, label, lo, hi, value, step, scale=None,
                 suffix="", fmt=None, setter=None):
        scale = step if scale is None else scale
        s = LabeledSlider(label, lo, hi, value, step, scale=scale, suffix=suffix, fmt=fmt)
        if setter:
            s.valueChanged.connect(setter)
        card.add(s)
        return s

    def _set_mouse_attr(self, attr):
        def apply(v):
            setattr(self.controller.config.mouse, attr, v)
            self._mark_custom()
        return apply

    def _set_kbd_attr(self, attr):
        def apply(v):
            setattr(self.controller.config.keyboard, attr, v)
            self._mark_custom()
        return apply

    def _set_trajectory(self, name):
        self.controller.config.mouse.trajectory = name.lower()
        self._mark_custom()

    # --- profiles / modes ------------------------------------------------

    def _apply_profile(self, name):
        self.profile_desc.setText(profiles.profile_description(name))
        if name == "Custom":
            self._commit()
            return
        cfg = profiles.get_profile_config(name)
        # preserve content + countdown, but adopt the profile's peripheral set
        # (e.g. Reader / Meeting Mode intentionally disable the keyboard).
        cfg.content_file = self.controller.config.content_file
        cfg.startup_delay = self.controller.config.startup_delay
        self.controller.set_config(cfg)
        self.storage.prefs["current_profile"] = name
        self.storage.prefs["mouse_enabled"] = cfg.mouse_enabled
        self.storage.prefs["keyboard_enabled"] = cfg.keyboard_enabled
        self._sync_power_widgets()
        self._commit()

    def _mark_custom(self):
        if self.profile_combo.currentText() != "Custom":
            self.profile_combo.blockSignals(True)
            self.profile_combo.setCurrentText("Custom")
            self.profile_combo.blockSignals(False)
            self.profile_desc.setText(profiles.profile_description("Custom"))
            self.storage.prefs["current_profile"] = "Custom"
        self._commit()

    def _commit(self):
        self.storage.set(self.controller.config.to_dict(), "engine_config")
        self.storage.save()
        self._on_config_changed()

    def _switch_mode(self, label):
        self._mode = "simple" if label == "Simple" else "power"
        self.storage.prefs["mode"] = self._mode
        self.storage.save()
        self._apply_mode_visibility()

    def _apply_mode_visibility(self):
        self.simple_panel.setVisible(self._mode == "simple")
        self.power_panel.setVisible(self._mode == "power")

    def _sync_power_widgets(self):
        cfg = self.controller.config
        for slider, attr, obj in [
            (self.p_speed, "speed_multiplier", cfg.mouse),
            (self.p_min, "min_distance", cfg.mouse),
            (self.p_max, "max_distance", cfg.mouse),
            (self.p_dur, "duration_scale", cfg.mouse),
            (self.p_curv, "curvature", cfg.mouse),
            (self.p_jit, "jitter", cfg.mouse),
            (self.p_idle, "max_idle", cfg.mouse),
            (self.p_dmin, "type_delay_min", cfg.keyboard),
            (self.p_dmax, "type_delay_max", cfg.keyboard),
            (self.p_typo, "typo_prob", cfg.keyboard),
            (self.p_think, "long_think_prob", cfg.keyboard),
            (self.p_chunk, "chunk_pause_max", cfg.keyboard),
            (self.p_punct, "punct_extra_max", cfg.keyboard),
        ]:
            slider.slider.blockSignals(True)
            slider.setValue(getattr(obj, attr))
            slider.slider.blockSignals(False)
        self.traj.set_current(cfg.mouse.trajectory.capitalize())

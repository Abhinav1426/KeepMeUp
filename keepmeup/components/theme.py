"""
Visual design system — "Precision Utility" dark theme.

Colour tokens and a global Qt Style Sheet (QSS) translated from the Stitch
design export. Centralising tokens here keeps every view visually consistent
and avoids hard-coded colours in widgets.
"""


class Color:
    # surfaces (background darkest -> containers lighten toward the user)
    BG = "#0d1117"
    SURFACE = "#101419"
    SURFACE_LOWEST = "#0a0e14"
    SURFACE_LOW = "#111418"
    SURFACE_CONTAINER = "#171c23"
    SURFACE_HIGH = "#22272e"
    SURFACE_HIGHEST = "#2d333b"

    # text
    ON_SURFACE = "#e6edf3"
    ON_SURFACE_VARIANT = "#8b949e"
    ON_SURFACE_DIM = "#6e7681"

    # structure
    OUTLINE = "#30363d"
    OUTLINE_VARIANT = "#434653"

    # accents
    PRIMARY = "#3366cc"            # Scholarly Blue — primary actions / active
    PRIMARY_HOVER = "#4477dd"
    PRIMARY_LIGHT = "#b1c5ff"      # light accent for text/icons on dark
    ON_PRIMARY = "#ffffff"
    PRIMARY_CONTAINER = "#112244"

    # state
    SUCCESS = "#3fb950"            # emerald — running / active indicator
    WARNING = "#fbbc01"            # amber — paused / standby
    ERROR = "#f85149"             # red — stop / abort
    ON_ERROR = "#ffffff"


FONT_SANS = "Inter, 'Segoe UI', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Code', Consolas, monospace"


def build_stylesheet() -> str:
    c = Color
    return f"""
    * {{
        font-family: {FONT_SANS};
        color: {c.ON_SURFACE};
        font-size: 14px;
    }}
    QMainWindow, QWidget#Root {{ background-color: {c.SURFACE}; }}
    QWidget {{ background-color: transparent; }}

    /* ---- Sidebar ---- */
    QFrame#Sidebar {{
        background-color: {c.SURFACE_CONTAINER};
        border-right: 1px solid {c.OUTLINE_VARIANT};
    }}
    QPushButton#NavItem {{
        background-color: transparent;
        color: {c.ON_SURFACE_VARIANT};
        border: none;
        border-left: 3px solid transparent;
        text-align: left;
        padding: 9px 14px;
        border-radius: 0px;
        font-size: 14px;
    }}
    QPushButton#NavItem:hover {{
        background-color: {c.SURFACE_HIGH};
        color: {c.ON_SURFACE};
    }}
    QPushButton#NavItem:checked {{
        background-color: {c.SURFACE_HIGHEST};
        color: {c.PRIMARY_LIGHT};
        border-left: 3px solid {c.PRIMARY};
        font-weight: 600;
    }}

    /* ---- Top bar / footer ---- */
    QFrame#TopBar {{
        background-color: {c.SURFACE};
        border-bottom: 1px solid {c.OUTLINE_VARIANT};
    }}
    QFrame#Footer {{
        background-color: {c.SURFACE_LOWEST};
        border-top: 1px solid {c.OUTLINE_VARIANT};
    }}

    /* ---- Cards ---- */
    QFrame#Card {{
        background-color: {c.SURFACE_LOW};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 8px;
    }}
    QFrame#CardHeader {{
        background-color: {c.SURFACE_CONTAINER};
        border: none;
        border-bottom: 1px solid {c.OUTLINE_VARIANT};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QFrame#StatTile {{
        background-color: {c.SURFACE_CONTAINER};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 6px;
    }}

    /* ---- Labels ---- */
    QLabel#LabelCaps {{
        color: {c.ON_SURFACE_VARIANT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#Headline {{ font-size: 24px; font-weight: 700; color: {c.ON_SURFACE}; }}
    QLabel#SubHeadline {{ font-size: 13px; color: {c.ON_SURFACE_VARIANT}; }}
    QLabel#Mono {{ font-family: {FONT_MONO}; }}
    QLabel#Muted {{ color: {c.ON_SURFACE_VARIANT}; }}

    /* ---- Buttons ---- */
    QPushButton#Primary {{
        background-color: {c.PRIMARY};
        color: {c.ON_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 9px 18px;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background-color: {c.PRIMARY_HOVER}; }}
    QPushButton#Primary:disabled {{
        background-color: {c.SURFACE_HIGHEST};
        color: {c.ON_SURFACE_DIM};
    }}
    QPushButton#Secondary {{
        background-color: {c.SURFACE_HIGH};
        color: {c.ON_SURFACE};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 4px;
        padding: 9px 18px;
    }}
    QPushButton#Secondary:hover {{ background-color: {c.SURFACE_HIGHEST}; border-color: {c.OUTLINE}; }}
    QPushButton#Secondary:disabled {{ color: {c.ON_SURFACE_DIM}; }}
    QPushButton#Danger {{
        background-color: {c.SURFACE_HIGH};
        color: {c.ERROR};
        border: 1px solid rgba(248,81,73,0.35);
        border-radius: 4px;
        padding: 9px 18px;
        font-weight: 600;
    }}
    QPushButton#Danger:hover {{ background-color: rgba(248,81,73,0.12); border-color: {c.ERROR}; }}
    QPushButton#Danger:disabled {{ color: {c.ON_SURFACE_DIM}; border-color: {c.OUTLINE_VARIANT}; }}

    /* segmented / choice buttons */
    QPushButton#Choice {{
        background-color: {c.SURFACE_CONTAINER};
        color: {c.ON_SURFACE_VARIANT};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 4px;
        padding: 8px 12px;
    }}
    QPushButton#Choice:hover {{ color: {c.ON_SURFACE}; }}
    QPushButton#Choice:checked {{
        background-color: {c.SURFACE_HIGHEST};
        color: {c.PRIMARY_LIGHT};
        border: 1px solid {c.PRIMARY};
    }}

    /* ---- Inputs ---- */
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTimeEdit {{
        background-color: {c.SURFACE_LOWEST};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 4px;
        padding: 6px 10px;
        color: {c.ON_SURFACE};
        selection-background-color: {c.PRIMARY};
    }}
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QTimeEdit:focus {{
        border: 1px solid {c.PRIMARY};
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {c.SURFACE_CONTAINER};
        border: 1px solid {c.OUTLINE_VARIANT};
        selection-background-color: {c.PRIMARY};
        color: {c.ON_SURFACE};
        outline: none;
    }}
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; }}

    /* ---- Sliders ---- */
    QSlider::groove:horizontal {{
        height: 4px; background: {c.SURFACE_HIGHEST}; border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{ background: {c.PRIMARY}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        background: {c.PRIMARY_LIGHT}; width: 14px; height: 14px;
        margin: -6px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: #ffffff; }}

    /* ---- CheckBox as a label row ---- */
    QCheckBox {{ spacing: 8px; color: {c.ON_SURFACE}; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; }}

    /* ---- Scrollbars ---- */
    QScrollArea {{ border: none; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {c.OUTLINE_VARIANT}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {c.OUTLINE}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    /* ---- Tooltip ---- */
    QToolTip {{
        background-color: {c.SURFACE_HIGHEST};
        color: {c.ON_SURFACE};
        border: 1px solid {c.OUTLINE_VARIANT};
        padding: 4px 8px;
    }}

    QMenu {{
        background-color: {c.SURFACE_CONTAINER};
        border: 1px solid {c.OUTLINE_VARIANT};
        padding: 4px;
    }}
    QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; }}
    QMenu::item:selected {{ background-color: {c.SURFACE_HIGHEST}; color: {c.PRIMARY_LIGHT}; }}
    QMenu::separator {{ height: 1px; background: {c.OUTLINE_VARIANT}; margin: 4px 8px; }}
    """

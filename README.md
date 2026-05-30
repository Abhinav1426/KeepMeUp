# KeepMeUp

A professional cross-platform desktop application that wraps the original
`keepmeup_cli.py` activity-simulation engines (human-like mouse movement + natural
typing) in a polished PySide6 UI — built on the **Precision Utility** dark
design system.

The original Bezier mouse algorithm and the human-cadence keyboard typer are
**preserved unchanged**; this project adds a UX, settings, orchestration and
packaging layer around them.

## Run

```bash
pip install -r requirements.txt        # from the repo root
python -m keepmeup.main
```

On Windows you can double-click `run_pro.bat`.

## Architecture (MVVM-inspired, decoupled threads)

```
keepmeup/
├── main.py                # bootstrap, single-instance lock, config loading
├── core/                  # simulation engines (preserved logic)
│   ├── engine_config.py   # EngineConfig dataclass (friendly <-> raw tunables)
│   ├── mouse.py           # MouseWorker(QThread) — Bezier movement
│   ├── keyboard.py        # KeyboardWorker(QThread) — streaming typist
│   └── generator.py       # content generation with presets
├── services/              # business logic / ViewModel layer
│   ├── engine_controller.py  # owns the workers + run state (the ViewModel)
│   ├── telemetry.py       # live metric aggregator
│   ├── profiles.py        # named presets -> EngineConfig
│   ├── storage.py         # JSON settings + lifetime stats persistence
│   └── scheduler.py       # wall-clock auto start/stop windows
├── components/            # reusable widgets + design tokens
│   ├── theme.py           # colour tokens + global QSS
│   ├── cards.py           # Card, StatTile, StatusDot, ToggleSwitch
│   └── sliders.py         # LabeledSlider
└── views/                 # PySide6 sections
    ├── main_window.py     # shell: sidebar, top bar, stacked content, footer
    ├── dashboard.py       # session control center + focus timer
    ├── behavior.py        # Simple / Power User configuration
    ├── content.py         # content file management + generation
    ├── analytics.py       # live telemetry + activity graph + lifetime totals
    ├── schedule.py        # recurring schedule editor
    ├── settings.py        # preferences + launch targets
    ├── safe_start.py      # pre-run confirmation dialog
    └── tray.py            # system tray manager
```

### Threading

The UI thread only renders. `MouseWorker` and `KeyboardWorker` are `QThread`s
that run the simulation loops and report telemetry back through Qt signals.
Pause/stop are honoured instantly via thread-safe flags.

## Features

- **Dashboard** — Start / Pause / Stop, live runtime timer, mouse/keyboard
  target toggles, current WPM / profile / schedule, quick preferences.
- **Behavior** — Simple Mode (Movement Style, Typing Style, Activity,
  Randomness) and Power User Mode (full kinematic + keystroke sliders).
  Built-in profiles: Programmer, Active Worker, Reader, Meeting Mode, Custom.
- **Content** — select/reload a content file, generate new content from
  Programming / Business / Mixed presets, see char/line/word counts and an
  estimated typing duration.
- **Analytics** — live session metrics, a 60-second activity-density graph
  (PyQtGraph) and persisted lifetime totals.
- **Schedule** — recurring day + time windows that auto start/stop the engine.
- **Settings** — startup countdown, launch target (Notepad / VS Code / Cursor /
  Sublime / custom), tray behaviour, config folder access.
- **Safe Start** — a confirmation dialog summarising peripherals, target and
  typing speed before automation takes over.
- **System Tray** — minimise-to-tray with Show / Start / Pause / Resume / Stop /
  Quit and a live state-coloured icon.

Settings and lifetime statistics persist to `config.json` in your OS config
directory (`%APPDATA%\KeepMeUp` on Windows).

## Packaging

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "KeepMeUp" ^
    --add-data "content.txt;." keepmeup/main.py
```

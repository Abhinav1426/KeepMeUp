<div align="center">

# KeepMeUp

**Keep your computer awake and your status active — the natural way.**

A polished, cross-platform desktop app that simulates lifelike mouse movement and
human-cadence typing, so your machine never goes idle, sleeps, or flips your chat
status to *away* while you're stepping out, reading, presenting, or waiting on a
long-running job.

![Version](https://img.shields.io/badge/version-1.0.0-6C8EFF)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-2dd4bf)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Built with PySide6](https://img.shields.io/badge/built%20with-PySide6-41cd52)
![License](https://img.shields.io/badge/license-MIT-orange)

</div>

---

## Why KeepMeUp?

Most "mouse jigglers" twitch the cursor a pixel every few seconds — obvious,
robotic, and easy to spot. **KeepMeUp** is different. It moves the pointer along
smooth, randomized **Bézier curves** and types using a **human typing cadence**
(variable key delays, natural pauses, realistic bursts). The result feels like a
real person at the keyboard, wrapped in a clean dark UI you actually want to
look at.

Great for:

- ⏰ Keeping the screen awake during downloads, builds, renders, or backups.
- 🟢 Staying "active" while you read a long document, take notes on paper, or
  step away briefly.
- 🎤 Presentations and screen shares where the screensaver must never kick in.
- 🧪 Demos, kiosks, and test rigs that need continuous on-screen activity.

> **Use it responsibly.** KeepMeUp is a productivity and convenience tool. Make
> sure your use complies with your employer's policies and any applicable terms
> of service. You are responsible for how you use it.

---

## Download (v1.0.0)

Grab a ready-to-run build — **no Python required**, everything is bundled. The
latest binaries for all three platforms are on the
[**Releases page**](../../releases/latest).

| OS | File | How to run |
|----|------|-----------|
| 🪟 **Windows** 10/11 (x64) | [`KeepMeUp-1.0.0-windows.exe`](release/KeepMeUp-1.0.0-windows.exe) | Double-click. On the SmartScreen prompt: **More info → Run anyway** (the app is unsigned). |
| 🍎 **macOS** (Apple Silicon / Intel) | `KeepMeUp-1.0.0-macos.zip` | Unzip → drag `KeepMeUp.app` to Applications → **right-click → Open** the first time. Grant **Accessibility** permission so it can move the mouse/type. |
| 🐧 **Linux** (x64) | `KeepMeUp-1.0.0-linux.tar.gz` | `tar -xzf KeepMeUp-1.0.0-linux.tar.gz` then `./KeepMeUp-1.0.0-linux` (needs an X11/Wayland desktop). |


---

## Features

- **Dashboard** — Start / Pause / Stop, a live runtime timer, mouse & keyboard
  toggles, and at-a-glance WPM, active profile, and next schedule.
- **Behavior** — a **Simple Mode** (Movement Style, Typing Style, Activity,
  Randomness) and a **Power User Mode** with full kinematic and keystroke
  sliders. Built-in profiles: *Programmer, Active Worker, Reader, Meeting Mode,
  Custom*.
- **Content** — pick any text file to "type", or generate fresh content from
  Programming / Business / Mixed presets, with live char/line/word counts and an
  estimated typing duration.
- **Analytics** — live session metrics, a rolling 60-second activity-density
  graph, and persisted lifetime totals.
- **Schedule** — recurring day + time windows that auto start and stop the
  engine for you.
- **Settings** — startup countdown, launch target (Notepad / VS Code / Cursor /
  Sublime / custom), tray behavior, and one-click access to the config folder.
- **Safe Start** — a confirmation dialog that summarizes peripherals, target app,
  and typing speed before automation takes over.
- **System Tray** — minimize to tray with Show / Start / Pause / Resume / Stop /
  Quit and a live, state-colored icon.

Settings and lifetime statistics persist to `config.json` in your OS config
directory (`%APPDATA%\KeepMeUp` on Windows, `~/.config/KeepMeUp` on Linux,
`~/Library/Application Support/KeepMeUp` on macOS).

---

## Run from source

Requires **Python 3.9+**.

```bash
git clone https://github.com/Abhinav1426/KeepMeUp.git
cd KeepMeUp
pip install -r requirements.txt
python -m keepmeup.main
```

On Windows you can simply double-click **`run_pro.bat`**, which sets up a virtual
environment, installs dependencies, and launches the app for you.

---

## How it works

KeepMeUp is built on **PySide6 (Qt for Python)** with a decoupled, thread-safe
architecture so the interface always stays responsive:

- The **UI thread** only renders.
- A **MouseWorker** thread drives the cursor along randomized Bézier paths.
- A **KeyboardWorker** thread streams keystrokes with human-like timing.
- Pause and Stop are honored instantly through thread-safe flags, and every
  worker reports live telemetry back to the UI via Qt signals.

```
keepmeup/
├── main.py                # bootstrap, single-instance lock, config loading
├── core/                  # simulation engines
│   ├── engine_config.py   # EngineConfig dataclass (friendly <-> raw tunables)
│   ├── mouse.py           # MouseWorker(QThread) — Bézier movement
│   ├── keyboard.py        # KeyboardWorker(QThread) — streaming typist
│   └── generator.py       # content generation with presets
├── services/              # business logic / ViewModel layer
│   ├── engine_controller.py  # owns the workers + run state
│   ├── telemetry.py       # live metric aggregator
│   ├── profiles.py        # named presets -> EngineConfig
│   ├── storage.py         # JSON settings + lifetime stats persistence
│   └── scheduler.py       # wall-clock auto start/stop windows
├── components/            # reusable widgets + design tokens
└── views/                 # PySide6 screens (dashboard, behavior, analytics, …)
```

---

## Customizing what it types

The typing engine reads from a plain-text **content file** (`content.txt` ships
with the app). Point it at any `.txt` file in **Content → Select file**, or
generate new content from a preset. Anything in the file — prose, notes, code,
checklists — is what gets typed, so you can tailor it to look like whatever work
you'd normally be doing.

---

## Building releases

Builds are produced with [PyInstaller](https://pyinstaller.org) from the
checked-in [`KeepMeUp.spec`](KeepMeUp.spec). **PyInstaller cannot cross-compile**
— each binary must be built on its own operating system.

### Locally (per OS)

| OS | Command | Output |
|----|---------|--------|
| Windows | `scripts\build_windows.bat` | `release\KeepMeUp-1.0.0-windows.exe` |
| macOS | `bash scripts/build_macos.sh` | `release/KeepMeUp-1.0.0-macos.zip` |
| Linux | `bash scripts/build_linux.sh` | `release/KeepMeUp-1.0.0-linux.tar.gz` |

Each script creates a `.venv`, installs the dependencies plus PyInstaller, runs
the spec, and drops the artifact into `release/`.

### All platforms at once — GitHub Actions

The [`Build & Release`](.github/workflows/release.yml) workflow builds Windows,
macOS **and** Linux on native runners and publishes them to a GitHub Release.
Push a version tag to trigger it:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The binaries then appear on the repo's **Releases** page, ready to download. You
can also trigger the workflow manually from the **Actions** tab.

---

## Contributing

Issues and pull requests are welcome! If you're filing a bug, please include your
OS, how you launched the app (binary or source), and the steps to reproduce.

---

## License

Released under the **MIT License** — see [`LICENSE`](LICENSE) for details.

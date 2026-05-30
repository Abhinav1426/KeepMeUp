# KeepMeUp — Releases

Download the build for your operating system and run it. No Python install
required — everything is bundled.

| OS | File | How to run |
|----|------|-----------|
| **Windows** 10/11 (x64) | `KeepMeUp-1.0.0-windows.exe` | Double-click. If SmartScreen warns, click **More info → Run anyway** (the app is unsigned). |
| **macOS** (Apple Silicon/Intel) | `KeepMeUp-1.0.0-macos.zip` | Unzip, drag `KeepMeUp.app` to Applications. First launch: **right-click → Open** (unsigned). Grant **Accessibility** permission so it can move the mouse/type. |
| **Linux** (x64) | `KeepMeUp-1.0.0-linux.tar.gz` | `tar -xzf KeepMeUp-1.0.0-linux.tar.gz` then `./KeepMeUp-1.0.0-linux`. Needs a desktop session (X11/Wayland). |

> The latest signed-off binaries for **all three** platforms are published on the
> [GitHub Releases page](../../releases). The Windows build is also committed here
> for convenience.

## Why only the Windows binary is in this folder

PyInstaller cannot cross-compile — each binary must be built on its own OS.
The Windows `.exe` was built on Windows and committed here. The macOS `.app`
and Linux binary are produced by the GitHub Actions **Build & Release** workflow
(which runs on real macOS and Linux runners) and attached to the GitHub Release.

To produce them yourself, run the matching script on that OS:
`scripts/build_macos.sh` or `scripts/build_linux.sh` (see the main README).

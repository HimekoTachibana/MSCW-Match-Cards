# MSCW Match Card Solver

A standalone desktop helper that observes the visible MapleStory Classic World Match Cards minigame and reconstructs the initial card layout. It does not inject into, hook, or read memory from MapleStory.

## Safety and scope

- Uses ordinary desktop window discovery and screen capture only.
- Does not inject code, install hooks, inspect process memory, automate inputs, or modify game files.
- The user remains responsible for all in-game actions.

## Status

Initial implementation scaffold. Screen/window discovery and image-based board recognition are an MVP; game-specific layout calibration may be required for different resolutions or UI scaling.

## Supported build targets

- **Windows x64:** standalone folder packaged as a ZIP; intended for Windows 10/11.
- **Linux x64:** standalone folder packaged as a tar.gz, built on Ubuntu 22.04 (glibc 2.35). Intended for Debian 12/13, current Fedora, Bazzite, Arch, and CachyOS systems with glibc 2.35 or newer. Not guaranteed for Debian 11 or older.
- Linux monitoring currently requires an **X11 session** and `wmctrl`. Wayland sessions are not supported yet. On Debian/Ubuntu install `wmctrl` and Qt/XCB runtime libraries (`libxcb-cursor0`, `libxkbcommon-x11-0`, `libegl1`, `libgl1`). Fedora-family packages: `wmctrl libxcb xcb-util-cursor libxkbcommon-x11 mesa-libGL`. Arch-family packages: `wmctrl libxcb xcb-util-cursor libxkbcommon-x11 mesa`.

## Build locally

Install requirements and PyInstaller, then run:

```bash
python -m pip install -r requirements.txt pyinstaller
python -m unittest discover -s tests -v
pyinstaller --noconfirm --clean MSCW-Match-Card-Solver.spec
```

The standalone folder is written to `dist/MSCW-Match-Card-Solver/`. GitHub Actions builds Windows and Linux x64 archives and publishes a prerelease for testing when this feature branch is updated. Linux builds use Ubuntu 22.04 as the compatibility baseline.

## Run from source (Windows 10/11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Optional OCR: install Tesseract OCR and ensure `tesseract.exe` is on PATH. OCR is used only as a secondary minigame-window signal; card identity comes from captured card pixels.

## Controls

- **Start monitoring**: finds the MapleStory game window and watches its visible client area.
- **Stop monitoring**: stops capture.
- **Clear results**: clears the current board and detected mode.
- **Auto-detect**: looks for a regular grid of card-shaped regions and supports 4×3, 5×4, and 6×5 layouts.

The initial reveal is time-limited. Keep the game window visible and unobstructed while the reveal is on screen. The app samples frames continuously and renders a candidate solution as soon as a complete grid is found.

### Board layout reference

The [user-provided 6×5 gameplay video](https://www.youtube.com/watch?v=xqS7pS4uSZE) is the visual reference for the largest supported grid. The 4×3 and 5×4 variants are expected to occupy the same overall board area, with fewer rows and columns and proportionally larger cards. The result view should preserve a consistent overall board footprint: 4×3 cards largest, 5×4 intermediate, and 6×5 smallest. These dimensions are assumptions to validate against actual captures from each mode.

## Limitations

The game UI can vary with resolution, scaling, and window placement. Automatic card detection is best-effort and reports incomplete/uncertain captures rather than inventing card identities. This MVP does not click cards or play the game. Linux Wayland capture is not implemented.

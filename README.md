# MSCW Match Card Solver

A standalone Windows desktop helper that observes the visible MapleStory Classic World Match Cards minigame and reconstructs the initial card layout. It does not inject into, hook, or read memory from MapleStory.

## Safety and scope

- Uses Windows window enumeration and ordinary screen capture only.
- Does not inject code, install hooks, inspect process memory, automate inputs, or modify game files.
- The user remains responsible for all in-game actions.

## Status

Initial implementation scaffold. Screen/window discovery and image-based board recognition are implemented as a conservative MVP; game-specific layout calibration may be required for different resolutions or UI scaling.

## Run (Windows 10/11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Optional OCR: install Tesseract OCR and ensure `tesseract.exe` is on PATH. OCR is used only as a secondary minigame-window signal; card identity comes from captured card pixels.

## Controls

- **Start monitoring**: finds the MapleStory.exe window and watches its visible client area.
- **Stop monitoring**: stops capture.
- **Clear results**: clears the current board and detected mode.
- **Auto-detect**: looks for a regular grid of card-shaped regions and supports 4x3, 5x4, and 6x5 layouts.

The initial reveal is time-limited. Keep the game window visible and unobstructed while the reveal is on screen. The app samples frames continuously and renders a candidate solution as soon as a complete grid is found.

### Board layout reference

The [user-provided 6×5 gameplay video](https://www.youtube.com/watch?v=xqS7pS4uSZE) is the visual reference for the largest supported grid. The 4×3 and 5×4 variants are expected to occupy the same overall board area, with fewer rows and columns and proportionally larger cards. The result view should preserve a consistent overall board footprint: 4×3 cards largest, 5×4 intermediate, and 6×5 smallest. These dimensions are a layout assumption to validate against actual captures from each mode, not a claim that all game resolutions are identical.

## Limitations

The game UI can vary with resolution, scaling, and window placement. Automatic card detection is best-effort and the UI reports incomplete/uncertain captures rather than inventing card identities. This MVP does not click cards or play the game.

"""Read-only game-window discovery and capture for Windows and Linux/X11.

Linux currently requires an X11 session and wmctrl. Wayland window discovery
is intentionally not attempted because compositor capture permissions/APIs vary.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass

import numpy as np
import psutil

try:
    import win32gui
    import win32process
except ImportError:
    win32gui = None
    win32process = None

try:
    import mss
except ImportError:
    mss = None


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    title: str
    process_id: int
    left: int
    top: int
    width: int
    height: int


def _find_windows_windows() -> GameWindow | None:
    if win32gui is None or win32process is None:
        return None
    matches: list[GameWindow] = []

    def visit(hwnd: int, _extra: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        try:
            _thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            if psutil.Process(pid).name().lower() != "maplestory.exe":
                return True
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
            width, height = right - left, bottom - top
            if width > 300 and height > 250:
                matches.append(GameWindow(hwnd, win32gui.GetWindowText(hwnd), pid,
                                          screen_left, screen_top, width, height))
        except (psutil.Error, OSError):
            pass
        return True

    win32gui.EnumWindows(visit, None)
    return max(matches, key=lambda w: w.width * w.height) if matches else None


def _find_windows_linux() -> GameWindow | None:
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return None
    if not shutil.which("wmctrl"):
        return None
    try:
        result = subprocess.run(
            ["wmctrl", "-lpG"], check=True, capture_output=True, text=True, timeout=3
        )
    except (OSError, subprocess.SubprocessError):
        return None

    matches: list[GameWindow] = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        try:
            window_id = int(parts[0], 16)
            pid = int(parts[2])
            left, top, width, height = map(int, parts[3:7])
            title = parts[7].strip()
            if width <= 300 or height <= 250:
                continue
            title_match = "maplestory" in title.lower()
            try:
                process_name = psutil.Process(pid).name().lower()
            except psutil.Error:
                process_name = ""
            process_match = process_name in {"maplestory.exe", "maplestory"}
            # Wine may own the process, so require the recognizable game window title.
            if title_match or process_match:
                matches.append(GameWindow(window_id, title, pid, left, top, width, height))
        except (ValueError, psutil.Error):
            continue
    return max(matches, key=lambda w: w.width * w.height) if matches else None


def find_maplestory_window() -> GameWindow | None:
    """Find a visible game window without opening or inspecting process memory."""
    if os.name == "nt":
        return _find_windows_windows()
    if os.name == "posix":
        return _find_windows_linux()
    return None


def capture_window(window: GameWindow) -> np.ndarray | None:
    """Capture the visible window rectangle using ordinary desktop screen capture."""
    if mss is None:
        return None
    try:
        with mss.mss() as sct:
            shot = sct.grab({
                "left": window.left, "top": window.top,
                "width": window.width, "height": window.height,
            })
        return np.asarray(shot, dtype=np.uint8)[:, :, :3].copy()
    except Exception:
        return None


def monitor_frames(stop_event, on_frame, on_status, interval: float = 0.075) -> None:
    """Poll the visible game window. No input is sent to the game."""
    while not stop_event.is_set():
        window = find_maplestory_window()
        if window is None:
            if os.name == "posix" and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
                on_status("Linux Wayland is not supported yet; start an X11 session.")
            elif os.name == "posix" and not shutil.which("wmctrl"):
                on_status("Install wmctrl and use an X11 session to monitor the game.")
            else:
                on_status("Waiting for a visible MapleStory game window…")
            stop_event.wait(0.8)
            continue
        frame = capture_window(window)
        if frame is None:
            on_status("Unable to capture the game window. Check that it is visible.")
        else:
            on_status(f"Monitoring game window · {window.width} × {window.height}")
            on_frame(frame)
        stop_event.wait(interval)

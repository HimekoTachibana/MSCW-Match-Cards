"""Safe, read-only window discovery and screen capture for Windows."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import numpy as np
import psutil

try:
    import win32gui
    import win32process
except ImportError:  # Allows imports/tests on non-Windows hosts.
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


def find_maplestory_window() -> GameWindow | None:
    """Find a visible MapleStory.exe top-level window without opening its process."""
    if win32gui is None or win32process is None:
        return None

    matches: list[GameWindow] = []

    def visit(hwnd: int, _extra: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        try:
            _thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name().lower()
            if proc_name != "maplestory.exe":
                return True
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
            width, height = right - left, bottom - top
            if width > 300 and height > 250:
                matches.append(GameWindow(
                    hwnd=hwnd,
                    title=win32gui.GetWindowText(hwnd),
                    process_id=pid,
                    left=screen_left,
                    top=screen_top,
                    width=width,
                    height=height,
                ))
        except (psutil.Error, OSError):
            pass
        return True

    win32gui.EnumWindows(visit, None)
    if not matches:
        return None
    # Prefer the largest visible client area if multiple MapleStory windows exist.
    return max(matches, key=lambda w: w.width * w.height)


def capture_window(window: GameWindow) -> np.ndarray | None:
    """Capture the visible client rectangle using ordinary desktop screen capture."""
    if mss is None:
        return None
    try:
        with mss.mss() as sct:
            shot = sct.grab({
                "left": window.left,
                "top": window.top,
                "width": window.width,
                "height": window.height,
            })
        # mss returns BGRA; OpenCV expects BGR.
        return np.asarray(shot, dtype=np.uint8)[:, :, :3].copy()
    except Exception:
        return None


def monitor_frames(stop_event, on_frame, on_status, interval: float = 0.075) -> None:
    """Poll the visible game window. No input is sent to the game."""
    while not stop_event.is_set():
        window = find_maplestory_window()
        if window is None:
            on_status("Waiting for a visible MapleStory.exe window…")
            stop_event.wait(0.8)
            continue
        frame = capture_window(window)
        if frame is None:
            on_status("Unable to capture the game window. Check that it is visible.")
        else:
            on_status(f"Monitoring MapleStory.exe · {window.width} × {window.height}")
            on_frame(frame)
        stop_event.wait(interval)

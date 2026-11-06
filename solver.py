"""Card-grid detection and visual matching; all recognition is screen-image based."""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import math

import cv2
import numpy as np


SUPPORTED_MODES = {(4, 3): "4×3", (5, 4): "5×4", (6, 5): "6×5"}


@dataclass
class Card:
    row: int
    col: int
    image: np.ndarray
    match_id: int | None = None
    confidence: float = 0.0


@dataclass
class Board:
    columns: int
    rows: int
    cards: list[Card]
    complete: bool
    message: str


def _iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def _rectangles(frame: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Card borders are strong rectangular edges. A few thresholds improve
    # tolerance to the pale card backgrounds and different desktop scaling.
    found: list[tuple[int, int, int, int]] = []
    for low, high in ((35, 110), (55, 150), (75, 190)):
        edges = cv2.Canny(gray, low, high)
        edges = cv2.morphologyEx(
            edges, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=2
        )
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            ratio = w / max(h, 1)
            if 42 <= w <= frame.shape[1] * 0.28 and 58 <= h <= frame.shape[0] * 0.45 and 0.58 <= ratio <= 0.98:
                found.append((x, y, w, h))

    # Prefer larger outer card borders and suppress nested duplicates.
    found.sort(key=lambda r: r[2] * r[3], reverse=True)
    unique: list[tuple[int, int, int, int]] = []
    for rect in found:
        if not any(_iou(rect, prior) > 0.72 for prior in unique):
            unique.append(rect)
    return unique


def _cluster(values: list[float], tolerance: float) -> list[float]:
    groups: list[list[float]] = []
    for value in sorted(values):
        if not groups or abs(value - float(np.mean(groups[-1]))) > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [float(np.mean(group)) for group in groups]


def _dhash(image: np.ndarray) -> int:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = resized[:, 1:] > resized[:, :-1]
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return value


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def _similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Compare normalized card interiors, avoiding border/shadow variation.
    ah, aw = a.shape[:2]
    bh, bw = b.shape[:2]
    a = a[int(ah * .12):int(ah * .88), int(aw * .12):int(aw * .88)]
    b = b[int(bh * .12):int(bh * .88), int(bw * .12):int(bw * .88)]
    a = cv2.resize(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (48, 56))
    b = cv2.resize(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), (48, 56))
    # Mean absolute difference is stable for repeated, identical in-game artwork.
    diff = float(np.mean(cv2.absdiff(a, b))) / 255.0
    return max(0.0, 1.0 - diff)


def _looks_like_face(image: np.ndarray) -> bool:
    """Reject nearly uniform blank/back cards; do not assign a false monster."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    interior = gray[int(gray.shape[0] * .15):int(gray.shape[0] * .85),
                    int(gray.shape[1] * .15):int(gray.shape[1] * .85)]
    return float(np.std(interior)) > 12.0


def detect_board(frame: np.ndarray) -> Board | None:
    """Find a regular 4x3, 5x4, or 6x5 card grid in a captured game frame."""
    rects = _rectangles(frame)
    if len(rects) < 12:
        return None

    # Use dominant dimensions to discard unrelated rectangles from the game UI.
    widths = np.array([r[2] for r in rects])
    heights = np.array([r[3] for r in rects])
    med_w, med_h = float(np.median(widths)), float(np.median(heights))
    candidates = [
        r for r in rects
        if abs(r[2] - med_w) <= max(12, med_w * .24)
        and abs(r[3] - med_h) <= max(14, med_h * .24)
    ]
    if len(candidates) < 12:
        candidates = rects

    best = None
    best_score = -1.0
    for columns, rows in SUPPORTED_MODES:
        for tolerance_scale in (.28, .38, .48):
            xs = _cluster([x + w / 2 for x, y, w, h in candidates], med_w * tolerance_scale)
            ys = _cluster([y + h / 2 for x, y, w, h in candidates], med_h * tolerance_scale)
            if len(xs) != columns or len(ys) != rows:
                continue
            selected = []
            for row, cy in enumerate(ys):
                for col, cx in enumerate(xs):
                    nearby = [
                        r for r in candidates
                        if abs((r[0] + r[2] / 2) - cx) <= med_w * .42
                        and abs((r[1] + r[3] / 2) - cy) <= med_h * .42
                    ]
                    if nearby:
                        selected.append((row, col, max(nearby, key=lambda r: r[2] * r[3])))
            count = len(selected)
            score = count / (columns * rows)
            if count >= columns * rows * .85 and score > best_score:
                best = (columns, rows, selected)
                best_score = score

    if best is None:
        return None

    columns, rows, selected = best
    cards: list[Card] = []
    for row, col, (x, y, w, h) in selected:
        # Crop a small margin to avoid card frames dominating the comparison.
        margin_x, margin_y = max(2, int(w * .07)), max(2, int(h * .07))
        crop = frame[y + margin_y:y + h - margin_y, x + margin_x:x + w - margin_x].copy()
        if crop.size:
            cards.append(Card(row=row, col=col, image=crop))

    # Group exact/near-exact duplicates. dHash narrows candidates; pixel similarity
    # confirms them so different monsters with similar silhouettes are less likely
    # to be merged.
    next_id = 1
    assigned: set[int] = set()
    hashes = [_dhash(card.image) for card in cards]
    for i, card in enumerate(cards):
        if i in assigned:
            continue
        card.match_id = next_id
        card.confidence = 1.0
        assigned.add(i)
        for j in range(i + 1, len(cards)):
            if j in assigned:
                continue
            if _hamming(hashes[i], hashes[j]) <= 13:
                sim = _similarity(card.image, cards[j].image)
                if sim >= .91:
                    cards[j].match_id = next_id
                    cards[j].confidence = sim
                    assigned.add(j)
        next_id += 1

    expected = columns * rows
    complete = len(cards) == expected and all(_looks_like_face(c.image) for c in cards)
    message = (
        f"Captured {len(cards)}/{expected} cards · {SUPPORTED_MODES[(columns, rows)]}"
        if complete else
        f"Partial or obscured reveal: {len(cards)}/{expected} cards. Keep the board visible."
    )
    return Board(columns, rows, cards, complete, message)


def recognize_minigame_text(frame: np.ndarray) -> bool | None:
    """Optional OCR signal for the MAPLE MINIGAME header; None if OCR unavailable."""
    try:
        import pytesseract
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        header = gray[:max(60, int(gray.shape[0] * .09)), :int(gray.shape[1] * .7)]
        text = pytesseract.image_to_string(header, config="--psm 6").upper()
        normalized = "".join(ch for ch in text if ch.isalnum())
        return "MAPLEMINIGAME" in normalized or ("MAPLE" in normalized and "MINIGAME" in normalized)
    except Exception:
        return None

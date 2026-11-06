"""MSCW Match Card Solver desktop application."""
from __future__ import annotations

import sys
import threading
from collections import deque

import cv2
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from capture import monitor_frames
from solver import Board, detect_board, recognize_minigame_text


class MonitorThread(QThread):
    frame_ready = Signal(object)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def run(self):
        monitor_frames(self.stop_event, self.frame_ready.emit, self.status_changed.emit)

    def stop(self):
        self.stop_event.set()
        self.wait(2000)


def to_pixmap(bgr, max_width=112, max_height=126):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, channels = rgb.shape
    qimage = QImage(rgb.data, w, h, channels * w, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimage).scaled(
        max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSCW Match Card Solver")
        self.resize(940, 760)
        self.monitor: MonitorThread | None = None
        self.last_frame = None
        self.last_capture_signature = None
        self.board: Board | None = None
        self.frame_history = deque(maxlen=4)

        root = QWidget()
        outer = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("MSCW MATCH CARD SOLVER")
        title.setStyleSheet("font-size: 19px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        self.status = QLabel("Stopped")
        self.status.setStyleSheet("color: #64748b; font-weight: 600;")
        header.addWidget(self.status)
        outer.addLayout(header)

        controls = QHBoxLayout()
        self.start_button = QPushButton("Start monitoring")
        self.start_button.clicked.connect(self.toggle_monitor)
        self.clear_button = QPushButton("Clear results")
        self.clear_button.clicked.connect(self.clear_results)
        controls.addWidget(self.start_button)
        controls.addWidget(self.clear_button)
        controls.addStretch()
        self.mode_label = QLabel("Mode: —")
        self.mode_label.setStyleSheet("font-weight: 600;")
        controls.addWidget(self.mode_label)
        outer.addLayout(controls)

        self.message = QLabel("Start monitoring, then keep the initial card reveal visible.")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("padding: 8px; background: #eef3f8; border-radius: 5px;")
        outer.addWidget(self.message)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.board_widget = QWidget()
        self.grid = QGridLayout(self.board_widget)
        self.grid.setSpacing(7)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.board_widget)
        outer.addWidget(self.scroll, 1)

        note = QLabel(
            "Read-only screen monitoring. No game input, memory access, hooks, or injection. "
            "Leave the game window visible and unobstructed during the reveal."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #64748b; font-size: 11px;")
        outer.addWidget(note)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow { background: #f7f9fc; }
            QPushButton { padding: 9px 14px; font-weight: 600; }
            QScrollArea { background: white; border: 1px solid #cbd5e1; }
            QLabel#card { background: #fff; border: 1px solid #aab6c5; border-radius: 5px; }
        """)

    def toggle_monitor(self):
        if self.monitor and self.monitor.isRunning():
            self.monitor.stop()
            self.monitor = None
            self.start_button.setText("Start monitoring")
            self.status.setText("Stopped")
            return
        self.monitor = MonitorThread()
        self.monitor.frame_ready.connect(self.on_frame)
        self.monitor.status_changed.connect(self.status.setText)
        self.monitor.start()
        self.start_button.setText("Stop monitoring")
        self.status.setText("Starting…")

    def on_frame(self, frame):
        self.last_frame = frame
        # Avoid re-running the contour detector on every frame. The reveal usually
        # remains stable across multiple samples; process about 4 frames/second.
        self.frame_history.append(frame)
        if len(self.frame_history) < 2 or self.board and self.board.complete:
            return
        board = detect_board(frame)
        if board is None:
            return
        self.message.setText(board.message)
        self.mode_label.setText(f"Mode: {board.columns}×{board.rows}")
        self.render_board(board)
        if board.complete:
            self.board = board
            self.status.setText("Reveal captured · solution ready")

    def render_board(self, board: Board):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        by_position = {(c.row, c.col): c for c in board.cards}
        for row in range(board.rows):
            for col in range(board.columns):
                card = by_position.get((row, col))
                cell = QFrame()
                cell.setObjectName("card")
                cell.setFrameShape(QFrame.Shape.StyledPanel)
                layout = QVBoxLayout(cell)
                layout.setContentsMargins(3, 3, 3, 3)
                image = QLabel()
                image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image.setMinimumSize(104, 116)
                if card:
                    image.setPixmap(to_pixmap(card.image))
                else:
                    image.setText("Not\ncaptured")
                layout.addWidget(image)
                label = QLabel(
                    f"R{row + 1} C{col + 1}" +
                    (f"  ·  #{card.match_id}" if card and card.match_id else "")
                )
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("font-size: 10px; color: #475569;")
                layout.addWidget(label)
                if not card:
                    cell.setStyleSheet("background: #fff7ed; border: 1px dashed #d97706;")
                self.grid.addWidget(cell, row, col)

    def clear_results(self):
        self.board = None
        self.last_capture_signature = None
        self.mode_label.setText("Mode: —")
        self.message.setText("Results cleared. Waiting for the next initial reveal.")
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def closeEvent(self, event):
        if self.monitor and self.monitor.isRunning():
            self.monitor.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

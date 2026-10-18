"""Minimal PySide6 main window. Foundation only, no chat/mood/voice."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from config.settings import EXPRESSIONS_DIR, WINDOW_SIZE, WINDOW_TITLE
from core.assets import available_expressions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(*WINDOW_SIZE)
        root = QWidget()
        lay = QVBoxLayout(root)
        self.label = QLabel("GOJO V2 foundation ready")
        self.label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.label)
        self.pic = QLabel()
        self.pic.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.pic)
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.status)
        self.setCentralWidget(root)
        self._show_idle()

    def _show_idle(self):
        try:
            names = available_expressions()
            if "idle" in names:
                pm = QPixmap(str(EXPRESSIONS_DIR / "idle.png"))
                if not pm.isNull():
                    self.pic.setPixmap(pm.scaledToHeight(160, Qt.SmoothTransformation))
                    self.status.setText(f"expressions: {len(names)} found")
                    return
            self.status.setText(f"expressions: {len(names)} found (idle missing)")
        except Exception as e:
            self.status.setText(f"asset error: {e}")

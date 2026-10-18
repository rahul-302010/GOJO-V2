"""Floating GOJO avatar window. Frameless, transparent, bottom-right, clickable stub."""
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from core.assets import expression_path

AVATAR_NAME = "idle"  # most neutral existing asset, full legs
AVATAR_PX = 150
MARGIN_X = 14
MARGIN_ABOVE_TASKBAR = 56


class AvatarWindow(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("GOJO")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent; border: none;")
        try:
            pm = QPixmap(str(expression_path(AVATAR_NAME)))
            if pm.isNull():
                raise FileNotFoundError(AVATAR_NAME)
            pm = pm.scaled(AVATAR_PX, AVATAR_PX, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(pm)
            self.resize(pm.size())
        except Exception as e:
            self.label.setText(f"GOJO\n{e}")
            self.resize(AVATAR_PX, AVATAR_PX)
        self._press_pos = None
        self._press_global = None
        self._place_bottom_right()

    def _place_bottom_right(self):
        try:
            screen = self.screen().availableGeometry() if self.screen() else None
        except Exception:
            screen = None
        if screen is None:
            self.move(900, 500)
            return
        x = screen.x() + screen.width() - self.width() - MARGIN_X
        y = screen.y() + screen.height() - self.height() - MARGIN_ABOVE_TASKBAR
        self.move(max(screen.x(), x), max(screen.y(), y))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.position().toPoint()
            self._press_global = e.globalPosition().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        # Light drag to reposition; no timers/animations.
        if self._press_pos is not None:
            try:
                delta: QPoint = e.globalPosition().toPoint() - self._press_global
                if delta.manhattanLength() > 6:
                    self.move(self.pos() + delta)
                    self._press_global = e.globalPosition().toPoint()
            except Exception:
                pass
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        try:
            if e.button() == Qt.LeftButton and self._press_global is not None:
                moved = (e.globalPosition().toPoint() - self._press_global).manhattanLength()
                self._press_pos = None
                self._press_global = None
                if moved <= 6:
                    self.on_avatar_clicked()
                    return
        except Exception:
            pass
        self._press_pos = None
        super().mouseReleaseEvent(e)

    def on_avatar_clicked(self):
        """Stub for future chat window. Log only for now."""
        print("[GOJO] avatar clicked (chat coming later)", flush=True)
        self.clicked.emit()

    def closeEvent(self, e):
        super().closeEvent(e)

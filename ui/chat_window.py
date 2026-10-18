"""GOJO chat window. Anime HUD glass design. AI via Gemini worker thread."""
from PySide6.QtCore import QObject, QRect, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QPalette, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.gemini_service import GojoAI

CYAN = (159, 216, 255)
HUD_CUT = 10
THINKING_TEXT = "GOJO is thinking..."


def _hud_path(r: QRect, cut: int) -> QPainterPath:
    p = QPainterPath()
    p.moveTo(r.left() + cut, r.top())
    p.lineTo(r.right() - cut, r.top())
    p.lineTo(r.right(), r.top() + cut)
    p.lineTo(r.right(), r.bottom() - cut)
    p.lineTo(r.right() - cut, r.bottom())
    p.lineTo(r.left() + cut, r.bottom())
    p.lineTo(r.left(), r.bottom() - cut)
    p.lineTo(r.left(), r.top() + cut)
    p.closeSubpath()
    return p


class _AIWorkerSignals(QObject):
    done = Signal(str)
    failed = Signal(str)


class _AIWorker(QRunnable):
    """Runs GojoAI.send() on a pool thread - never on the Qt UI thread."""

    def __init__(self, ai: GojoAI, text: str):
        super().__init__()
        self._ai = ai
        self._text = text
        self.signals = _AIWorkerSignals()

    def run(self):
        try:
            reply = self._ai.send(self._text)
        except Exception as e:  # GojoAIError (friendly) or unexpected
            self.signals.failed.emit(str(e))
        else:
            self.signals.done.emit(reply)


class ChatWindow(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("GOJO chat")
        self.setMinimumSize(320, 420)
        self.resize(340, 440)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        f = QFont("Bahnschrift")
        if not f.exactMatch():
            f = QFont("Segoe UI")
        f.setPointSizeF(10.0)
        self.setFont(f)
        self.setStyleSheet(
            "ChatWindow { color: #edf6ff; }"
            "QLabel { background: transparent; color: #edf6ff; }"
        )
        self._ai = GojoAI()
        self._busy = False
        self._status = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        # Header: title + custom window controls
        head = QHBoxLayout()
        head.setSpacing(6)
        brand = QLabel("GOJO")
        brand.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #dff1ff; word-spacing: 3px;"
        )
        head.addWidget(brand)
        head.addStretch(1)
        mini = QPushButton("\u2013")
        mini.setFixedSize(26, 24)
        mini.setStyleSheet(self._ctrl_qss())
        mini.clicked.connect(self.showMinimized)
        head.addWidget(mini)
        close = QPushButton("\u2715")
        close.setFixedSize(26, 24)
        close.setStyleSheet(self._ctrl_qss() + "QPushButton:hover { color: #ffd9d9; border-color: rgba(255,140,150,180); background: rgba(120,30,45,140); }")
        close.clicked.connect(self.hide)
        head.addWidget(close)
        lay.addLayout(head)
        self._drag_pos = None
        # Hairline divider under header
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(159, 216, 255, 55); border: none;")
        lay.addWidget(div)
        # Conversation panel: soft glass, integrated look
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { border: 1px solid rgba(159, 216, 255, 38); border-radius: 8px;"
            " background: rgba(13, 26, 46, 110); }"
            "QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }"
            "QScrollBar::handle:vertical { background: rgba(159,216,255,80); border-radius: 4px; min-height: 30px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )
        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.thread = QVBoxLayout(self.body)
        self.thread.setContentsMargins(8, 8, 8, 8)
        self.thread.setSpacing(6)
        self.thread.addStretch(1)
        self.scroll.setWidget(self.body)
        lay.addWidget(self.scroll, 1)
        # Input row: HUD field + compact send
        row = QHBoxLayout()
        row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Talk to GOJO...")
        self.input.setStyleSheet(
            "QLineEdit { background: rgba(9, 18, 34, 180); color: #edf6ff; font-size: 13.5px;"
            " font-weight: 500; border: 1px solid rgba(159, 216, 255, 95); border-radius: 8px;"
            " padding: 9px 11px; selection-background-color: rgba(46, 104, 196, 160); }"
            "QLineEdit:focus { border: 1px solid rgba(159, 216, 255, 235);"
            " background: rgba(12, 26, 50, 200); }"
            "QLineEdit:hover { border: 1px solid rgba(159, 216, 255, 150); }"
        )
        pal = self.input.palette()
        pal.setColor(QPalette.PlaceholderText, QColor(143, 163, 187))
        self.input.setPalette(pal)
        self.input.returnPressed.connect(self.send)
        row.addWidget(self.input, 1)
        send = QPushButton("SEND")
        send.setFixedSize(56, 38)
        self.send_btn = send
        send.setStyleSheet(
            "QPushButton { background: rgba(46, 104, 196, 200); color: #eef6ff; font-weight: 600;"
            " font-size: 11px; border: 1px solid rgba(159, 216, 255, 110); border-radius: 8px; }"
            "QPushButton:hover { background: rgba(159, 216, 255, 215); color: #0b1526; }"
            "QPushButton:pressed { background: rgba(30, 74, 150, 220); }"
        )
        send.clicked.connect(self.send)
        row.addWidget(send)
        lay.addLayout(row)

    @staticmethod
    def _ctrl_qss() -> str:
        return (
            "QPushButton { background: rgba(18, 35, 60, 140); color: #9fb3cc; font-size: 11px;"
            " font-weight: 500; border: 1px solid rgba(159, 216, 255, 60); border-radius: 6px; }"
            "QPushButton:hover { color: #eaf6ff; border-color: rgba(159, 216, 255, 200);"
            " background: rgba(46, 104, 196, 130); }"
        )

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        outer = self.rect().adjusted(1, 1, -1, -1)
        path = _hud_path(outer, HUD_CUT)
        p.fillPath(path, QColor(11, 21, 38, 205))
        p.setPen(QPen(QColor(CYAN[0], CYAN[1], CYAN[2], 150), 1))
        p.drawPath(path)
        inner = _hud_path(outer.adjusted(4, 4, -4, -4), max(4, HUD_CUT - 4))
        p.setPen(QPen(QColor(CYAN[0], CYAN[1], CYAN[2], 42), 1))
        p.drawPath(inner)
        # Accent marks parallel to each cut corner (inside, no glow)
        import math
        p.setPen(QPen(QColor(CYAN[0], CYAN[1], CYAN[2], 210), 2, Qt.SolidLine, Qt.RoundCap))
        c, o, seg = HUD_CUT, 4.0, 9.0
        k = math.sqrt(0.5) * seg
        L, T, R, B = outer.left(), outer.top(), outer.right(), outer.bottom()
        marks = (
            (L + c + o, T + o, -k, k),
            (R - c - o, T + o, k, k),
            (L + c + o, B - o, -k, -k),
            (R - c - o, B - o, k, -k),
        )
        for sx, sy, dx, dy in marks:
            p.drawLine(int(sx), int(sy), int(sx + dx), int(sy + dy))
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            try:
                self.move(e.globalPosition().toPoint() - self._drag_pos)
            except Exception:
                pass
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def _insert(self, lab: QLabel):
        self.thread.insertWidget(self.thread.count() - 1, lab)
        try:
            bar = self.scroll.verticalScrollBar()
            bar.setValue(bar.maximum())
        except Exception:
            pass

    def _bubble(self, text: str, mine: bool, error: bool = False):
        lab = QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if error:
            lab.setAlignment(Qt.AlignLeft)
            lab.setStyleSheet(
                "QLabel { background: rgba(90, 40, 50, 175); color: #ffeef0; font-size: 13px;"
                " font-weight: 400; border: 1px solid rgba(255, 150, 160, 90);"
                " border-radius: 8px; padding: 9px 11px; }"
            )
        elif mine:
            lab.setAlignment(Qt.AlignRight)
            lab.setStyleSheet(
                "QLabel { background: rgba(28, 74, 140, 165); color: #edf6ff; font-size: 13px;"
                " font-weight: 400; border: 1px solid rgba(159, 216, 255, 85);"
                " border-radius: 8px; padding: 9px 11px; }"
            )
        else:
            lab.setAlignment(Qt.AlignLeft)
            lab.setStyleSheet(
                "QLabel { background: rgba(18, 38, 72, 175); color: #edf6ff; font-size: 13px;"
                " font-weight: 400; border: 1px solid rgba(96, 160, 255, 75);"
                " border-radius: 8px; padding: 9px 11px; }"
            )
        self._insert(lab)

    def send(self):
        if self._busy:
            return
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._bubble(text, mine=True)
        self._start_ai(text)

    def _start_ai(self, text: str):
        self._busy = True
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self._status = QLabel(THINKING_TEXT)
        self._status.setStyleSheet(
            "QLabel { background: transparent; color: #8fa3bb; font-size: 12.5px;"
            " font-style: italic; border: none; padding: 2px 4px; }"
        )
        self._insert(self._status)
        worker = _AIWorker(self._ai, text)
        worker.signals.done.connect(self._on_reply)
        worker.signals.failed.connect(self._on_error)
        QThreadPool.globalInstance().start(worker)

    def _end_status(self):
        if self._status is not None:
            self.thread.removeWidget(self._status)
            self._status.deleteLater()
            self._status = None

    def _restore_controls(self):
        self._busy = False
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()

    def _on_reply(self, reply: str):
        self._end_status()
        self._bubble(reply, mine=False)
        self._restore_controls()

    def _on_error(self, message: str):
        self._end_status()
        self._bubble(message, mine=False, error=True)
        self._restore_controls()

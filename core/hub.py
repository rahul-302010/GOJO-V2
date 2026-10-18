"""Shared Qt signals hub. No polling, no threads in foundation."""
from PySide6.QtCore import QObject, Signal


class Hub(QObject):
    ready = Signal()
    error = Signal(str)

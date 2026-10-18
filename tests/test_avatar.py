import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.avatar_window import AVATAR_NAME, AvatarWindow


def test_avatar_loads():
    from core.assets import expression_path
    assert expression_path(AVATAR_NAME).is_file()


def test_avatar_window_flags():
    from PySide6.QtCore import Qt
    app = QApplication.instance() or QApplication([])
    w = AvatarWindow()
    flags = w.windowFlags()
    assert flags & Qt.FramelessWindowHint
    assert flags & Qt.WindowStaysOnTopHint
    assert w.label.pixmap() is not None and not w.label.pixmap().isNull()
    w.close()

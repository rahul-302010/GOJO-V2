"""App lifecycle: init, run, clean shutdown."""
import sys

from PySide6.QtWidgets import QApplication

from core.hub import Hub
from ui.avatar_window import AvatarWindow
from ui.chat_window import ChatWindow


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        app.setQuitOnLastWindowClosed(True)
    except Exception:
        pass
    hub = Hub()
    chat = None
    try:
        win = AvatarWindow()
    except Exception as e:
        hub.error.emit(str(e))
        return 1

    def show_chat():
        nonlocal chat
        try:
            if chat is None:
                chat = ChatWindow()
            if chat.isHidden():
                # Place left of avatar, keep inside available screen.
                try:
                    ag = win.frameGeometry()
                    scr = win.screen().availableGeometry() if win.screen() else None
                    if scr is not None:
                        cx = max(scr.x() + 8, ag.x() - chat.width() - 12)
                        cy = max(scr.y() + 8, ag.y() - 60)
                        chat.move(cx, cy)
                except Exception:
                    pass
                chat.show()
            chat.raise_()
            chat.activateWindow()
            try:
                chat.input.setFocus()
            except Exception:
                pass
        except Exception as e:
            hub.error.emit(str(e))

    try:
        win.clicked.connect(show_chat)
    except Exception:
        pass
    win.show()
    hub.ready.emit()
    try:
        return app.exec()
    finally:
        try:
            if chat is not None:
                chat.close()
        except Exception:
            pass
        try:
            win.close()
        except Exception:
            pass

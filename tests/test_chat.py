import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from ui.chat_window import THINKING_TEXT, ChatWindow


class FakeAI:
    def __init__(self):
        self.calls = []

    def send(self, text):
        self.calls.append(text)
        return "mock reply: " + text


class FailAI:
    def send(self, text):
        raise RuntimeError("friendly failure")


def _drain():
    QThreadPool.globalInstance().waitForDone(5000)
    app = QApplication.instance()
    for _ in range(20):
        app.processEvents()
        time.sleep(0.005)


def _texts(w):
    out = []
    for i in range(w.thread.count() - 1):
        it = w.thread.itemAt(i)
        wdg = it.widget() if it else None
        if wdg is not None:
            out.append(wdg.text())
    return out


def test_chat_ai_send_flow():
    app = QApplication.instance() or QApplication([])
    w = ChatWindow()
    fake = FakeAI()
    w._ai = fake
    w.show()
    assert w.isVisible()
    w.input.setText("hello gojo")
    w.send()
    # busy state while worker pending
    assert w._busy and not w.input.isEnabled() and not w.send_btn.isEnabled()
    _drain()
    texts = _texts(w)
    assert texts == ["hello gojo", "mock reply: hello gojo"], texts
    assert fake.calls == ["hello gojo"]
    assert w._status is None
    assert w.input.isEnabled() and w.send_btn.isEnabled() and not w._busy
    # empty send ignored
    w.input.setText("   ")
    w.send()
    _drain()
    assert _texts(w) == texts
    # hidden thinking status text constant exists and is honest
    assert THINKING_TEXT == "GOJO is thinking..."
    w.hide()
    w.show()
    assert w.isVisible()
    w.close()


def test_chat_error_path():
    app = QApplication.instance() or QApplication([])
    w = ChatWindow()
    w._ai = FailAI()
    w.show()
    w.input.setText("boom")
    w.send()
    _drain()
    texts = _texts(w)
    assert texts == ["boom", "friendly failure"], texts
    assert w.input.isEnabled() and not w._busy
    w.close()


def test_chat_busy_blocks_duplicate():
    app = QApplication.instance() or QApplication([])
    w = ChatWindow()
    fake = FakeAI()
    w._ai = fake
    w.show()
    w.input.setText("first")
    w.send()
    w._busy = True  # simulate in-flight
    w.input.setText("second")
    w.input.setEnabled(True)  # bypass UI disable to prove guard
    w.send()
    _drain()
    w._busy = False
    assert fake.calls == ["first"], fake.calls
    w.close()

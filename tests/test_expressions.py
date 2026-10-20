import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QApplication

from core.expressions import DEFAULT_STATE, classify, resolve_asset
from ui.avatar_window import AvatarWindow
from ui.chat_window import ChatWindow


class FakeAI:
    def send(self, text):
        return "Hehe nice one macha, semma try da"


class FailAI:
    def send(self, text):
        from core.gemini_service import GojoAIError

        raise GojoAIError("friendly failure")


def _drain():
    QThreadPool.globalInstance().waitForDone(5000)
    app = QApplication.instance()
    for _ in range(20):
        app.processEvents()
        time.sleep(0.005)


# --- 1-5, 7 classifier table tests ---
def test_classify_jolly():
    assert classify("haha that was funny da", "loL") == "jolly"


def test_classify_serious():
    assert classify("I am stressed and worried about my exams tomorrow") == "serious"


def test_classify_surprised():
    assert classify("I can't believe I cleared the interview!!") == "surprised"


def test_classify_angry():
    assert classify("This stupid app keeps crashing, I am so mad and angry") == "angry"


def test_classify_frustrated_prefers_serious_support():
    # Frustration + request for help -> supportive SERIOUS beats ANGRY.
    assert classify("I'm frustrated with this error, please help me fix it", "") == "serious"


def test_classify_neutral_default():
    assert classify("ok") == DEFAULT_STATE


def test_classify_sleepy():
    assert classify("good night da, going to sleep") == "sleepy"


def test_listening_never_from_text():
    # No mic feature exists -> classifier must never claim listening.
    for msg in ("hello", "listening test", "say something", "mic check"):
        assert classify(msg) != "listening"


# --- 9 missing PNG fallback ---
def test_resolve_asset_fallbacks():
    assert resolve_asset("jolly") == "jolly"
    assert resolve_asset("bogus_state_xyz") == DEFAULT_STATE


# --- 6, 7, 8, 12 chat lifecycle with worker thread ---
def test_chat_expression_lifecycle_success():
    app = QApplication.instance() or QApplication([])
    w = ChatWindow()
    w._ai = FakeAI()
    seen = []
    w.expression_changed.connect(seen.append)
    w.show()
    w.input.setText("haha semma joke da")
    w.send()
    assert seen and seen[0] == "thinking", seen  # 6: THINKING on request start
    _drain()
    assert seen[-1] == "jolly", seen  # 7: final expression from classify(user, reply)
    assert not w._busy and w.input.isEnabled()
    w.close()


def test_chat_expression_error_recovery():
    app = QApplication.instance() or QApplication([])
    w = ChatWindow()
    w._ai = FailAI()
    seen = []
    w.expression_changed.connect(seen.append)
    w.show()
    w.input.setText("boom")
    w.send()
    assert seen == ["thinking"]
    _drain()
    assert seen[-1] == "serious", seen  # 8: error -> serious, never stuck thinking
    assert "thinking" not in seen[1:]
    w.close()


# --- 10 no-reload, 11 UI-thread safe, 12 transparency/click intact ---
def test_avatar_expression_no_reload_and_transparency():
    app = QApplication.instance() or QApplication([])
    a = AvatarWindow()
    a.show()
    assert a.testAttribute(Qt.WA_TranslucentBackground)
    a.set_expression("jolly")
    pm1 = a.label.pixmap()
    assert pm1 is not None and not pm1.isNull()
    a.set_expression("jolly")  # same state again
    pm2 = a.label.pixmap()
    assert pm1.cacheKey() == pm2.cacheKey(), "same-state must not reload image"
    a.set_expression("serious")
    pm3 = a.label.pixmap()
    assert pm3.cacheKey() != pm2.cacheKey()
    assert a._current == "serious"
    a.set_expression("not_a_state")
    assert a._current == DEFAULT_STATE  # 9: missing -> idle fallback
    a.close()


def test_avatar_click_still_works():
    app = QApplication.instance() or QApplication([])
    a = AvatarWindow()
    a.show()
    hits = []
    a.clicked.connect(lambda: hits.append(1))
    a.on_avatar_clicked()
    assert hits == [1]
    a.close()

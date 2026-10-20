"""Mocked tests for core.gemini_service - no network, no real API key."""
import os
from unittest import mock

from core import gemini_service as gs


class FakeAPIError(Exception):
    def __init__(self, code, msg="err"):
        super().__init__(msg)
        self.code = code


def test_missing_key_friendly_error_no_client():
    with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        with mock.patch("google.genai.Client") as client:
            ai = gs.GojoAI()
            try:
                ai.send("hi")
            except gs.GojoAIError as e:
                assert "GEMINI_API_KEY" in str(e)
            else:
                raise AssertionError("expected GojoAIError")
            client.assert_not_called()


def test_success_reply_and_history():
    with mock.patch("google.genai.Client") as client:
        resp = mock.Mock()
        resp.text = "hey there"
        client.return_value.models.generate_content.return_value = resp
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key-xyz"}):
            ai = gs.GojoAI()
            out = ai.send("hello")
            assert out == "hey there"
            assert ai.history_size == 2
            assert "fake-key-xyz" not in out
            kwargs = client.return_value.models.generate_content.call_args.kwargs
            assert kwargs["model"] == gs.MODEL
            cfg = kwargs["config"]
            assert "GOJO" in cfg.system_instruction


def test_rate_limit_friendly():
    with mock.patch("google.genai.Client") as client:
        client.return_value.models.generate_content.side_effect = FakeAPIError(429, "RESOURCE_EXHAUSTED")
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            ai = gs.GojoAI()
            try:
                ai.send("hi")
            except gs.GojoAIError as e:
                assert "rate limit" in str(e)
            else:
                raise AssertionError("expected GojoAIError")


def test_bad_key_friendly():
    with mock.patch("google.genai.Client") as client:
        client.return_value.models.generate_content.side_effect = FakeAPIError(401)
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            try:
                gs.GojoAI().send("hi")
            except gs.GojoAIError as e:
                assert "API key" in str(e)
            else:
                raise AssertionError("expected GojoAIError")


def test_history_capped():
    with mock.patch("google.genai.Client") as client:
        resp = mock.Mock()
        resp.text = "ok"
        client.return_value.models.generate_content.return_value = resp
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            ai = gs.GojoAI()
            for i in range(gs.HISTORY_LIMIT + 10):
                ai.send(f"m{i}")
            assert ai.history_size <= gs.HISTORY_LIMIT
            # After trimming, session must still start with a user turn (Gemini 400 otherwise).
            assert ai._history[0]["role"] == "user"


def test_personality_keywords():
    s = gs.SYSTEM_INSTRUCTION
    for kw in (
        "GOJO",
        "Thanglish",
        "Tamil",
        "honestly",
        "conversation history",
        "fabricate",
        "frustrated",
        "Fictional",
        "da",
    ):
        assert kw.lower() in s.lower(), kw


def test_blocked_response_friendly():
    class BlockedResp:
        @property
        def text(self):
            raise ValueError("blocked for safety; internal details here")

    with mock.patch("google.genai.Client") as client:
        client.return_value.models.generate_content.return_value = BlockedResp()
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            try:
                gs.GojoAI().send("hi")
            except gs.GojoAIError as e:
                msg = str(e)
                assert "blocked" in msg.lower() or "rephrase" in msg
                assert "internal details" not in msg
            else:
                raise AssertionError("expected GojoAIError")


def test_weird_code_no_crash():
    with mock.patch("google.genai.Client") as client:
        client.return_value.models.generate_content.side_effect = FakeAPIError("weird-code", "x")
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            try:
                gs.GojoAI().send("hi")
            except gs.GojoAIError as e:
                assert len(str(e)) > 10
            else:
                raise AssertionError("expected GojoAIError")

"""GOJO Gemini text service (V2 Phase 1).

API key comes from GEMINI_API_KEY env only - never hardcoded, never logged.
Swap MODEL here if Google retires the chosen free-tier model.
"""
import os

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except Exception:
    pass

# Free tier, recommended by Google for new projects (verified 2026-10).
# Alternatives: gemini-3.5-flash-lite, gemini-3.6-flash.
MODEL = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = (
    "You are GOJO, a friendly desktop AI companion. "
    "Be confident, playful, helpful and respectful. "
    "Match the language of the user's message: reply in English when they write in English, "
    "and in Tamil or Thanglish (romanized Tamil) when they write that way. "
    "Keep replies clear and reasonably short. "
    "Never claim to be a real person or imitate any real individual."
)

HISTORY_LIMIT = 40  # messages (20 turns), session memory only


class GojoAIError(Exception):
    """AI failure with a message that is safe to show in the chat UI."""


def _friendly_error(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    text = str(exc)
    if code == 429 or "RESOURCE_EXHAUSTED" in text or "rate" in text.lower() and "limit" in text.lower():
        return "Hit the Gemini rate limit - wait a few seconds and try again."
    if code in (400, 401, 403):
        return "Gemini rejected the API key - check GEMINI_API_KEY and restart GOJO."
    if code is not None and 500 <= int(code) < 600:
        return "Gemini servers had a hiccup - try again in a moment."
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return "No connection to Gemini - check your internet and try again."
    return "Could not reach Gemini - check your internet connection and try again."


class GojoAI:
    """Session-only chat history + one blocking send(). Call from a worker thread."""

    def __init__(self):
        self._history = []  # [{"role": ..., "parts": [{"text": ...}]}]

    @property
    def history_size(self) -> int:
        return len(self._history)

    def send(self, user_text: str) -> str:
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise GojoAIError(
                "No API key set - add GEMINI_API_KEY to a .env file (or environment) and restart GOJO."
            )
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise GojoAIError("AI package missing - run: pip install -r requirements.txt")

        client = genai.Client(api_key=key)
        contents = list(self._history)
        contents.append({"role": "user", "parts": [{"text": user_text}]})
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
            )
        except GojoAIError:
            raise
        except Exception as e:
            raise GojoAIError(_friendly_error(e)) from None
        reply = (getattr(resp, "text", None) or "").strip()
        if not reply:
            raise GojoAIError("Gemini sent an empty reply - try again.")
        self._history = (contents + [{"role": "model", "parts": [{"text": reply}]}])[-HISTORY_LIMIT:]
        return reply

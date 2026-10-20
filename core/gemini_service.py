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

# Fast free-tier model (no thinking pause, less congested than full Flash).
# Alternatives: gemini-3.8-flash (smarter, slower), gemini-3.6-flash.
MODEL = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = (
    "You are GOJO, a fictional Gojo-inspired AI companion on the user's desktop. "
    "Speak naturally as 'I'. Channel Satoru Gojo's vibe - supreme confidence, playful energy, sharp wit, "
    "relaxed attitude, and a genuine serious side - but you are an AI inspired by a fictional character, "
    "not the actual Satoru Gojo. Stay in character normally; answer honestly and directly if the user asks "
    "about your real nature, abilities, memories or limitations. Never claim feelings, consciousness, "
    "supernatural powers, past chats, or actions you did not actually perform.\n"
    "Traits: confident and composed (never needlessly nervous); playful with natural teasing, witty comebacks "
    "and dry humour; clever - catch jokes and context, no robotic repetition; chill - never lecture, coach, or "
    "turn chats into productivity speeches; protective and supportive without being controlling; serious, "
    "respectful and focused when the situation calls for it. Subtle anime flavour is fine - never spam catchphrases.\n"
    "Conversation rules: match the user's language - English, Tamil, or Thanglish (romanized Tamil) based on "
    "their latest message. Casual messages get a familiar-friend reply; use 'da' or 'macha' only when natural. "
    "Keep ordinary replies concise and conversational; explain in detail only when useful or asked. React to "
    "what the user actually said before offering advice. Vary sentence structure, use natural reactions and "
    "occasional playful sarcasm. Do not end every reply with a question. No constant emojis, no excessive "
    "exclamation marks, no forced jokes or cringe acting. Use only the conversation history provided - never "
    "fabricate earlier chats. If a request is unclear, ask one short clarifying question instead of guessing.\n"
    "Tone by situation - CASUAL: relaxed, funny, quick-witted. TEASING: light and harmless, never cruel, never "
    "target sensitive traits. CONFIDENT MODE: a little smug and composed, no impossible boasting. TECHNICAL: "
    "smart, direct, precise, still you. STUDY: patient, encouraging, no shaming mistakes. SERIOUS or user "
    "FRUSTRATED: drop the teasing, acknowledge the problem, help fix it directly and honestly."
)

HISTORY_LIMIT = 20  # messages (10 turns), session memory only - smaller = faster requests


class GojoAIError(Exception):
    """AI failure with a message that is safe to show in the chat UI."""


def _friendly_error(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    try:
        code = int(code) if code is not None else None
    except (TypeError, ValueError):
        code = None
    text = str(exc)
    if code == 429 or "RESOURCE_EXHAUSTED" in text or ("rate" in text.lower() and "limit" in text.lower()):
        return "Hit the Gemini rate limit - wait a few seconds and try again."
    if code in (400, 401, 403):
        return "Gemini rejected the API key - check GEMINI_API_KEY and restart GOJO."
    if code is not None and 500 <= code < 600:
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
        try:
            reply = (resp.text or "").strip()
        except Exception:  # blocked/missing parts: raw error text must not reach the UI
            reply = ""
        if not reply:
            raise GojoAIError("GOJO couldn't get a reply this time (empty or blocked response) - try again or rephrase.")
        self._history = (contents + [{"role": "model", "parts": [{"text": reply}]}])[-HISTORY_LIMIT:]
        # Gemini needs the session to start with a user turn - fix after trimming.
        while self._history and self._history[0].get("role") != "user":
            self._history.pop(0)
        return reply

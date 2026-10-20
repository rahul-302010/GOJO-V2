"""Local conversation-aware expression classifier (no API calls, UI-thread safe, pure).

Returns a semantic state string; asset resolution is separate (resolve_asset).
LISTENING is reserved for a real microphone feature - never emitted by this classifier.
"""
import re

# Semantic states supported by the app.
STATES = ("jolly", "serious", "thinking", "listening", "surprised", "angry", "sleepy", "idle")

# Semantic state -> existing PNG stem in assets/expressions (verified on disk).
STATE_TO_ASSET = {
    "jolly": "jolly",
    "serious": "serious",
    "thinking": "thinking",
    "listening": "listening",  # unused until a real mic feature exists
    "surprised": "surprised",
    "angry": "angry",
    "sleepy": "sleepy",
    "idle": "idle",  # default/neutral
}
DEFAULT_STATE = "idle"


def resolve_asset(state: str) -> str:
    """Map a semantic state to an existing PNG stem; fall back to idle if missing/unknown."""
    stem = STATE_TO_ASSET.get(state, DEFAULT_STATE)
    try:
        from core.assets import available_expressions

        if stem not in available_expressions():
            return DEFAULT_STATE
    except Exception:
        return DEFAULT_STATE
    return stem


# Multi-signal patterns (intent phrases + context), not single bare keywords.
_SERIOUS_RE = re.compile(
    r"\b(stress(ed)?|anxious|worried?|depress\w*|sad|scared?|afraid|death|died|break ?up|"
    r"pressure|serious|sick|ill|help me|can'?t sleep|troubleshoot\w*)\b"
    r"|\bimportant\b.{0,25}\b(talk|question|issue|problem)\b"
    r"|\bnot working\b.{0,35}\b(help|fix|issue)\b"
    r"|\b(stress|kovam illa| tension) aagudhu\b",
    re.IGNORECASE,
)
_ANGER_RE = re.compile(
    r"\b(angry|furious|hate|hating|pissed|raging|mad at|so mad|annoy\w*|irritat\w*|"
    r"damn it|wtf|trash|garbage app|stupid (app|code|bug|laptop|phone))\b|"
    r"\bkovam\b.{0,10}\b(iruk|varu|podu)",
    re.IGNORECASE,
)
_EMPathY_REPLY_RE = re.compile(
    r"\b(sorry|here for you|take it easy|ennaachu|understand|listen|breathe|"
    r"it'?s okay|we can fix|let'?s fix)\b",
    re.IGNORECASE,
)
_SURPRISE_RE = re.compile(
    r"\b(can'?t believe|unexpected|shocked|shocking|no way|first time|won|winner|"
    r"topped|cleared|selected|accepted|surprise\w*|impressive|whoa|what\?)\b",
    re.IGNORECASE,
)
_JOLLY_RE = re.compile(
    r"\b(haha+|lol|lmao|rofl|funny|joke|jokes|lol da|maja|semma|super|nice one|"
    r"good one|tease|kidding|epdi da|thalaivane)\b|[:;]-?[)D]",
    re.IGNORECASE,
)
_SLEEPY_RE = re.compile(
    r"\b(good ?night|going to sleep|sleep pøduven|nelavu|zzz|off to bed|"
    r"sleep agudhu|tired and sleep)\b",
    re.IGNORECASE,
)
_INTENSITY_RE = re.compile(r"!!!|([\w])\1{3,}|\bSOOO+\b")


def _shouty_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 8:
        return 0.0
    upper = [c for c in letters if c.isupper()]
    return len(upper) / len(letters)


def classify(user_text: str, reply: str = "") -> str:
    """Pick a semantic expression state from the user message + GOJO's reply.

    Priority: serious/sensitive > anger (unless supportive reply) > surprised >
    jolly > sleepy > idle (neutral/uncertain).
    """
    u = (user_text or "").strip()
    r = (reply or "").strip()
    if not u:
        return DEFAULT_STATE

    # 1) Serious / sensitive / support-needing context wins first.
    serious = bool(_SERIOUS_RE.search(u))
    if serious:
        return "serious"

    # 2) Anger - but if GOJO's reply is empathetic/supportive, prefer serious support.
    angry = bool(_ANGER_RE.search(u)) or _shouty_ratio(u) > 0.5 or bool(_INTENSITY_RE.search(u))
    if angry:
        if _EMPathY_REPLY_RE.search(r):
            return "serious"
        return "angry"

    # 3) Surprise / unexpected achievement.
    if _SURPRISE_RE.search(u):
        return "surprised"

    # 4) Playful / happy banter (also if reply is clearly joking back).
    if _JOLLY_RE.search(u):
        return "jolly"
    if r and _JOLLY_RE.search(r) and len(u) < 80 and not _SLEEPY_RE.search(u):
        return "jolly"

    # 5) Sleep talk only.
    if _SLEEPY_RE.search(u):
        return "sleepy"

    # 6) Neutral / uncertain -> default (never listening; mic feature does not exist).
    return DEFAULT_STATE

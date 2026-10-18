# GOJO V2 — Phase 1 Foundation (PySide6)

Lightweight Windows desktop companion foundation. V1 backup untouched.

## Setup
```
cd GOJO_V2
pip install -r requirements.txt
python main.py
```

## Structure
- `main.py` entry
- `app/lifecycle.py` init/run/shutdown
- `ui/main_window.py` minimal window + idle art
- `core/assets.py` lazy cached expression loader + `core/hub.py` signals
- `assets/expressions/` 8 PNGs (from V1, preserved) + `assets/icons/gojo.png`
- `config/settings.py` no secrets
- `tests/test_assets.py`

## Notes
- No mood/voice/wake/startup control yet. Chat UI + Gemini text AI live (Phase 1 below).
- No polling/threads/animations on timers. AI runs only inside a Qt thread-pool worker while a message is pending.

## Phase 1: Gemini AI chat
1. Create a free API key at https://aistudio.google.com/apikey
2. Create `.env` in this folder (git-ignored) with one line:
   ```
   GEMINI_API_KEY=your_key_here
   ```
   Or set the `GEMINI_API_KEY` environment variable instead.
3. `pip install -r requirements.txt` then `python main.py`.

- Model: `gemini-3.8-flash` (free tier, Google-recommended for new projects, verified 2026-10).
  Change it in `core/gemini_service.py` -> `MODEL` if Google retires it.
- Personality: confident/playful/helpful/respectful, replies English or Tamil/Thanglish per user's message.
- History: current chat session only (capped at 40 messages). No persistence.
- Errors (missing key / offline / quota / API) show friendly messages; the key is never printed.

## Tests
```
python -c "from tests.test_assets import *; from tests.test_avatar import *; from tests.test_chat import *; from tests.test_gemini_service import *; test_expressions_found(); test_avatar_loads(); test_avatar_window_flags(); test_chat_ai_send_flow(); test_chat_error_path(); test_chat_busy_blocks_duplicate(); test_missing_key_friendly_error_no_client(); test_success_reply_and_history(); test_rate_limit_friendly(); test_bad_key_friendly(); test_history_capped(); print('ALL PASSED')"
```
AI tests use mocks - no network or real key needed.

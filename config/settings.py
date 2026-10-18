"""Non-secret app config."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXPRESSIONS_DIR = BASE / "assets" / "expressions"
ICONS_DIR = BASE / "assets" / "icons"
WINDOW_TITLE = "GOJO V2"
WINDOW_SIZE = (420, 300)

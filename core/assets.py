"""Expression asset loader. Preserves originals, lazy + cached, no full-res preload."""
from functools import lru_cache
from pathlib import Path

from config.settings import EXPRESSIONS_DIR


def available_expressions():
    """Scan actual files. No assumed mood list."""
    try:
        return sorted(p.stem for p in EXPRESSIONS_DIR.glob("*.png") if p.is_file())
    except Exception:
        return []


def expression_path(name: str) -> Path:
    p = (EXPRESSIONS_DIR / f"{name}.png").resolve()
    base = EXPRESSIONS_DIR.resolve()
    if base not in p.parents and p.parent != base:
        raise ValueError("Blocked path outside expressions dir")
    if not p.is_file():
        raise FileNotFoundError(f"Missing expression: {name}")
    return p


@lru_cache(maxsize=16)
def expression_bytes(name: str) -> bytes:
    return expression_path(name).read_bytes()

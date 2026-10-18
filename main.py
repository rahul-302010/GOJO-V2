"""GOJO V2 entry point."""
from app.lifecycle import run


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())

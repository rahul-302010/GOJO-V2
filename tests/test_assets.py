from core.assets import available_expressions, expression_path


def test_expressions_found():
    names = available_expressions()
    assert "idle" in names, f"idle missing, got {names}"
    assert len(names) >= 8, f"expected 8 moods, got {names}"


def test_expression_paths_inside_dir():
    p = expression_path("idle")
    assert p.is_file()

def test_main_parses():
    import ast
    from pathlib import Path

    src = Path("main.py").read_text(encoding="utf-8")
    ast.parse(src)

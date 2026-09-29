import ast
from pathlib import Path


def launcher_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "bootstrap_dev_users.py"


def test_bootstrap_launcher_changes_to_backend_before_app_import() -> None:
    source = launcher_path().read_text(encoding="utf-8")
    tree = ast.parse(source)

    main_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )

    calls = [
        node
        for node in ast.walk(main_function)
        if isinstance(node, ast.Call)
    ]

    assert any(
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "os"
        and call.func.attr == "chdir"
        for call in calls
    )

    imports_inside_main = [
        node
        for node in ast.walk(main_function)
        if isinstance(node, ast.ImportFrom)
    ]

    assert any(
        node.module == "app.cli.bootstrap_dev_users"
        for node in imports_inside_main
    )


def test_bootstrap_launcher_has_no_module_level_app_imports() -> None:
    source = launcher_path().read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("app")
        elif isinstance(node, ast.Import):
            assert all(not alias.name.startswith("app") for alias in node.names)

import ast
from pathlib import Path


def launcher_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scripts" / "manage_user_role.py"


def test_role_launcher_has_no_module_level_app_imports() -> None:
    source = launcher_path().read_text()
    tree = ast.parse(source)

    module_level_imports = [
        node
        for node in tree.body
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        )
    ]

    imported_modules: list[str] = []

    for node in module_level_imports:
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            imported_modules.append(node.module or "")
        else:
            imported_modules.extend(alias.name for alias in node.names)

    assert all(not module.startswith("app") for module in imported_modules)


def test_role_launcher_does_not_spawn_child_process() -> None:
    source = launcher_path().read_text()

    forbidden_calls = {
        "os.execv(",
        "os.execve(",
        "subprocess.",
        "os.system(",
    }

    assert all(marker not in source for marker in forbidden_calls)


def test_role_launcher_imports_backend_cli_inside_main() -> None:
    source = launcher_path().read_text()
    tree = ast.parse(source)

    main_function = next(
        node
        for node in tree.body
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name == "main"
        )
    )

    imports_inside_main = [
        node
        for node in ast.walk(main_function)
        if isinstance(
            node,
            ast.ImportFrom,
        )
    ]

    assert any(node.module == "app.cli.manage_user_role" for node in imports_inside_main)


def test_backend_role_cli_exists() -> None:
    command_module = Path(__file__).resolve().parents[1] / "app" / "cli" / "manage_user_role.py"

    assert command_module.is_file()

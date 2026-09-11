# D'Acqua Dolce — Python Dependency and Rebuild Policy

## Authority

`backend/pyproject.toml` defines direct runtime and development dependencies.

`backend/constraints-known-good.txt` pins the currently validated transitive
dependency resolution for reproducible rebuilds.

Do not replace these with an independently maintained `requirements.txt`.

## HTTP client split

D'Acqua Dolce intentionally keeps both HTTP client packages.

Runtime:

- `httpx`
- imported directly by `backend/app/integrations/postmark.py`;
- therefore required in production.

Development/test:

- `httpx2`
- used by the current Starlette/FastAPI `TestClient` integration;
- installed through the `dev` extra;
- not required by the production application runtime.

Do not replace runtime `httpx` with `httpx2`, and do not remove `httpx`
merely because the test suite uses `httpx2`.

## Warning policy

Pytest treats unexpected warnings as errors.

There is one narrowly scoped exception for the current upstream
Starlette/AnyIO `BlockingPortal` deprecation warning.

The exception must be removed when the installed Starlette release no longer
emits that warning.

Do not replace the narrow exception with a blanket suppression of
`DeprecationWarning`.

## Development installation

From `backend/`, a normal online development installation is:

    .venv/bin/python -m pip install       -c constraints-known-good.txt       -e '.[dev]'

A local offline rebuild uses the preserved macOS-compatible wheelhouse:

    .venv/bin/python -m pip install       --no-index       --find-links "$HOME/Desktop/dacqua-dolce_build-assets/python-wheels"       -c constraints-known-good.txt       -e '.[dev]'

The local wheelhouse contains platform-specific binaries and must be treated
as a local development artifact.

## Python package discovery

The backend uses a flat repository layout containing both `app/` and
`alembic/`.

Setuptools package discovery is therefore configured explicitly in
`backend/pyproject.toml`:

    [tool.setuptools.packages.find]
    where = ["."]
    include = ["app", "app.*"]
    exclude = ["alembic", "alembic.*", "tests", "tests.*"]

Do not remove this configuration.

Without explicit discovery, setuptools sees multiple top-level directories
and refuses to build or install the backend distribution.

`app` is the Python application package. Alembic migrations and tests remain
repository/runtime-support files rather than Python distribution packages.

## Production installation

Production installs the project without the `dev` extra:

    python -m pip install       -c constraints-known-good.txt       .

This installs runtime `httpx` but does not install test-only `httpx2`,
pytest, Ruff, Bandit, or pip-audit.

If production must install offline, create and validate a separate wheelhouse
for the production operating system, CPU architecture, and Python version.

Do not copy the macOS/Apple-Silicon wheelhouse to a Debian production host and
assume its binary wheels are compatible.

The production deployment script may use a server-side compatible wheelhouse
through:

    DACQUA_PYTHON_WHEELHOUSE=/path/to/python-wheels

## Preserved build assets

Local downloaded/build dependencies are retained outside Git under:

    ~/Desktop/dacqua-dolce_build-assets/

Python assets live under:

    ~/Desktop/dacqua-dolce_build-assets/python-wheels/

The archive should contain:

- direct and transitive wheels needed by the validated local environment;
- the build-system `setuptools` wheel;
- the current D'Acqua Dolce backend wheel;
- a known-good `pip freeze --all` snapshot.

## Updating dependencies

Change dependency pins deliberately.

After any dependency change:

1. preserve newly required wheels;
2. install the proposed environment;
3. run `python -m pip check`;
4. run the full pytest suite with strict warning handling;
5. run Ruff/security validation;
6. refresh `constraints-known-good.txt`;
7. rebuild the preserved D'Acqua Dolce backend wheel;
8. refresh the known-good `pip freeze --all` snapshot.

Do not refresh the known-good artifacts from an environment that has not
passed validation.

BigBrotherBot (B3) packaging documentation
==========================================

B3 is distributed as a Python package (wheel) and a source distribution. The
former cx_Freeze/InnoSetup frozen-build path is not maintained for the 2.0.0
port; packaging is standard `pyproject.toml` based (see `pyproject.toml` for the
single source of truth for metadata and dependencies).

# Bumping the version number

Release tooling lives in the `build` extra of `pyproject.toml`:

```bash
pip install -e ".[build]"
bump2version patch     # 2.0.0 -> 2.0.1
bump2version minor     # 2.0.0 -> 2.1.0
bump2version major     # 2.0.0 -> 3.0.0
```

`.bumpversion.cfg` updates `b3/__init__.py`; update the `version` field in
`pyproject.toml` in the same change.

# Packaging B3

Requirements: Python 3.11+ and `git` in the PATH.

```bash
git clone https://github.com/BigBrotherBot/big-brother-bot.git
cd big-brother-bot
python -m venv .venv
.venv/bin/pip install -e ".[build]"
```

## Source and wheel distribution

```bash
.venv/bin/python -m build
```

The built `sdist` and `wheel` are written to `dist/`.

## Verifying a package

```bash
.venv/bin/pip install dist/b3-<version>-py3-none-any.whl
.venv/bin/b3_run --help
```

## Database scripts

Storage schema creation scripts for MySQL, PostgreSQL and SQLite ship inside the
package (`b3/sql/`) and are also used by the test fixtures.

## Windows

Windows uses the same pip/wheel packaging path as every other platform. If a
self-contained executable is ever needed, use `cx_Freeze` 7 or `pyinstaller` in
a separate build job — do not add it to the runtime dependency set.

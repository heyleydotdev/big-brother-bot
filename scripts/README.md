# B3 scripts

## b3.sh

Bash management wrapper for starting, stopping and checking the status of a B3
instance on Linux/macOS hosts that do not use systemd (containers, shared
hosts). It uses `screen` and PID files.

```
./scripts/b3.sh start   [config]
./scripts/b3.sh stop    [config]
./scripts/b3.sh status  [config]
./scripts/b3.sh restart [config]
./scripts/b3.sh clean
```

The interpreter is auto-detected: `B3_PYTHON` if set, else the project
virtualenv (`.venv/bin/python`), else `python3`, else `python` — Python 3.11+
is required.

Configuration knobs are environment variables documented at the top of the
script (`B3_AUTORESTART`, `B3_LOG`, `B3_DEV`, `B3_PYTHON`, `CONFIG_DIR`, ...).

## systemd (recommended on modern Linux servers)

`scripts/b3@.service` is a template unit: `b3@myinstance` runs
`conf/b3_myinstance.ini` under systemd supervision (no screen, no PID files,
`Restart=on-failure`). See the comments at the top of the unit file for the
install steps.

## Removed scripts

The TravisCI-era `install-deps-*.sh`, `start-tests-*.sh` and `test_watchdog.py`
helpers were removed during the Python 3 port: dependencies and test tooling now
live in `pyproject.toml` extras (`postgresql`, `sftp`, `test`, `build`) and CI
runs `pytest` directly.


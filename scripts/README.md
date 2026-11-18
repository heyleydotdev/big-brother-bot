# B3 scripts

## b3.sh

Bash management wrapper for starting, stopping and checking the status of a B3
instance on Linux/macOS hosts.

```
./scripts/b3.sh start   [config]
./scripts/b3.sh stop    [config]
./scripts/b3.sh status  [config]
./scripts/b3.sh restart [config]
```

Configuration knobs are environment variables documented at the top of the
script (`B3_AUTORESTART`, `B3_LOG`, `B3_DEV`, `CONFIG_DIR`, ...).

## Removed scripts

The TravisCI-era `install-deps-*.sh`, `start-tests-*.sh` and `test_watchdog.py`
helpers were removed during the Python 3 port: dependencies and test tooling now
live in `pyproject.toml` extras (`postgresql`, `sftp`, `test`, `build`) and CI
runs `pytest` directly.

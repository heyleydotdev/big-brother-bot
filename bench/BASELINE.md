# B3 performance baseline

First measurements of the python 3 port core, taken right after the storage
port milestone (M5) on 2026-11-18. Produced by `bench/replay.py` — see that
file for what each number means. **Update this file at every milestone that
claims a performance change.**

## Environment

- python 3.11.1, Windows, branch `py3-port` after M5, 10000 events
- runtime deps: pymysql 1.2.4, python-dateutil 4.0.0, feedparser 6.0.14, requests 2.34.2
- stdout/stderr writes are silenced inside the measured regions (see replay.py);
  the string building and logging call overhead stay in the measured path

## Results

| metric | value |
|---|---|
| `import b3.fake` (module import + first console boot) | 133 ms |
| dedicated console boot (config + sqlite storage + admin plugin) | 4 ms |
| RSS after boot | 29.2 MB |
| event throughput (admin plugin `parseEvent`, synchronous) | 20,654 events/sec |
| RSS after 10k events | 30.3 MB |
| tracemalloc peak during the event loop | 0.52 MB |

Top allocation site during the loop is `b3/fake.py:241` — the FakeConsole
message history, i.e. test-harness bookkeeping, not the production hot path.

## Reading of the baseline

- A busy game server produces tens of log lines per second: the core is
  already ~3 orders of magnitude faster than realtime demand. The M11
  optimization work should therefore target **startup time, idle RSS/CPU
  and pathological load (spam floods)** rather than raw events/sec.
- 29 MB RSS after boot includes the interpreter, b3 core, sqlite storage and
  the admin plugin. Remaining M11 levers: `__slots__` on clients/penalties/
  groups (hundreds of live objects per server), parameterized SQL, and
  `Event.wait` in polling threads.

## M11 targets (from the port plan)

- event processing: at least 25% faster than this baseline
- idle RSS with 10 plugins loaded: at most 100 MB
- startup: at most 3 s

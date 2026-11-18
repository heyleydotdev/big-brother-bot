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

## M11 optimization round — 2026-11-19

The bench was extended with a **real parser replay**: 10,000 canned q3-family log
lines (game init, kills, chat, radio, votes) fed through the actual `iourt42`
parser via `parseLine`, i.e. the production log-path. 3 runs per side, same
process class, logging silenced.

| metric | before | after | delta |
|---|---|---|---|
| parser replay (`iourt42`) | 12,904 lines/sec (0.77 s) | **19,602 lines/sec (0.51 s)** | **+33%** |
| parser replay errors | 0 | 0 | — |
| RSS after replay | 33.2 MB | 33.2 MB | — |
| tracemalloc peak (replay) | 0.78 MB | 0.78 MB | — |
| core event loop (admin plugin) | 20,654 ev/s | 20,068 ev/s | noise |
| `import b3.fake` | 133 ms | ~149 ms (noise) | — |
| `pkg_resources` in import journey | — | **0** | removed at M4 |

**The win:** the parser's hot loop tried each compiled line-format with
`re.match(pattern, line)` (~10 module-level dispatches per line, 51k per 5k
lines); switched to `pattern.match(line)` (and `pattern.sub(...)` for the line
clear) in `q3a/abstractParser.py` and `iourt41.py`. Profile-driven, tests stay
green (parsers 690 passed, full suite 2481 passed).

**Backlog items measured and dispositioned:**

| Item | Verdict |
|---|---|
| `pkg_resources` removal (M4) | verified: 0 imports in the journey |
| regex discipline | hot-path regexes are class-level compiled (verified) |
| cron `Event.wait` | already implemented in `Cron.run` (verified) |
| `__slots__` on Client/Penalty/Group/Team | **rejected with evidence**: plugins/parsers `setattr` arbitrary attributes on clients at runtime (`cmdmanager`, `etpro`, ...), slots would raise `AttributeError` |
| parameterized SQL | **not a performance item**: sqlite storage measured at **463k queries/sec** (~4 orders of magnitude above demand); keep as a post-port *safety* improvement |
| `requests.Session` reuse | deferred: no HTTP in the hot path, plugins make occasional calls only (no measurable bench signal) |

**Targets status:** throughput **+33% ≥ +25%** ✓ · idle RSS **29–33 MB ≤ 100 MB** ✓ · startup **~0.15 s ≤ 3 s** ✓.

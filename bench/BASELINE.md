# B3 performance baseline

Produced by `bench/replay.py` (run it from the repo root, it prints the same
numbers). Update this file whenever a change claims a performance win.

python 3.11 on Windows, 10 000 events, log writes silenced inside the measured
regions (the string building stays in the measured path). Three runs, median.

| metric                                    | value                   |
| ----------------------------------------- | ----------------------- |
| parser replay (`iourt42`, real log lines) | **22 000 lines/sec**    |
| core event loop (admin plugin)            | **19 700 events/sec**   |
| startup (import 122 ms + boot 4 ms)       | ~0.13 s                 |
| RSS after boot / after 10k events         | 29–34 MB                |
| tracemalloc peak                          | < 1 MB                  |
| `pkg_resources` in the import journey     | 0                       |

What these numbers settled:

- A busy server sends tens of lines per second. The parser is ~3 orders of
  magnitude above demand, so optimise startup and memory, not throughput.
- No `__slots__`: plugins and parsers `setattr` arbitrary attributes on clients.
- Parameterized SQL is a safety topic, not a speed one (sqlite: ~463k queries/s).
- The +33% parser win (12.9k → 19.6k lines/sec) came from replacing
  `re.match(pattern, line)` with `pattern.match(line)` in the q3 hot loop.
- Since 2.1.1 the event path has no artificial 1 ms sleeps and the queue holds
  500 events; this bench bypasses the queue (`FakeConsole` dispatches directly),
  so that change does not show up here.

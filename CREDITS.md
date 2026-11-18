# Credits

**B3 ran on game servers for over a decade because of these people.**

This file lists the developers behind Big Brother Bot (B3) — the original
Python 2 project and the Python 3 continuation — plus the vendored libraries
and the license they are distributed under.

## Project leads (original B3 team)

- Michael "ThorN" Thornton — founder (2005); author of B3 1.x
- Mark "xlr8or" Weirath
- Thomas "Courgette" LÉVEIL
- Daniele "Fenix" Pantaleone
- James "Bakes" Baker
- Tim "ttlogic" ter Laak

## Python 3 continuation (2.0)

- Raveen (heyleydotdev) — Python 3 port, packaging, test suite, performance work

## Code contributors

82ndab-Bravo17 · Ansa89 · bdgrell · Combro2k · cron410 · dahool · durzo ·
EHDSpoon · eire.32 · Gammelbob · grosbedo · Harry Gabriel · Hedayat Vatankhah ·
Isala Piyarisi · Ismael · IzNoGoD · Jonas Keunecke · Just a baka · Luar Roji ·
mindriot · Ozon · Rafał Mirończyk · Sander Nilsen · spacepig · Stephano2000 ·
Stephen L · tanka8 · Thomaxius · Tim Rowland · timnboys · veiled-bird ·
Özgür Uysal (Freelander)

Several early commits were made under local, unnamed identities (e.g.
`<Thomas@.(none)>`, `<mark@.(none)>`, `<Spacepig@.(none)>`) before the authors
configured git; they have been folded into the names above where possible.

## Vendored libraries

| Component | Location | License |
|---|---|---|
| Source RCON / query / log helpers (sourcelib) | `b3/lib/sourcelib/` | MIT (per-file headers) |
| SimpleXMLWriter | `b3/lib/SimpleXMLWriter.py` | © 2001–2004 Fredrik Lundh (effbot permissive license, per-file header) |
| MaxMind GeoIP Python API | `b3/plugins/geolocation/lib/geoip/` | LGPL 2.1 |
| netblock | `b3/plugins/netblocker/netblock/` | GPL v3 (see its README) |

The old profiling helpers `statlib` and `runsnakerun` were vendored for the
Python 2 era and were removed during the port (replaced by `cProfile`,
`tracemalloc` and `bench/replay.py`).

## Community

Thanks to the B3 forum and community members who reported issues, wrote
third-party plugins, tested releases and kept the game servers running. An
incidental snippet or a well-written bug report is as valuable as a patch —
thank you.

## License

This project is distributed under the **GNU General Public License, version 2
or (at your option) any later version** (`GPL-2.0-or-later`). The full text is
in [`LICENSE`](LICENSE). Every source file carries the GPL header block.

Note: the bundled netblock component is GPL v3; redistributions must comply
with the GPL v3 terms for that part, which the "or later" grant permits.

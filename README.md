![BigBrotherBot](https://github.com/BigBrotherBot/ArtWork/blob/master/layered-png/logo.png)

**********

> [!IMPORTANT]
> **B3 2.0 runs on Python 3.11+.** This is the Python 3 continuation of the
> project: the Python 2 code base was ported to a single Python 3 code base,
> the dependency stack was brought to maintained releases, and the test suite
> runs on Python 3.11, 3.12 and 3.13.

Big Brother Bot (B3) is a complete and total server administration package for online games. It is the prefered ingame
RCON Tool currently available. B3 is designed primarily to keep your server free from the derelicts of online gaming,
but offers more, much more. With the stock configuration files, B3 will keep your server free from offensive language,
and team killers alike. A completely automated and customizable warning system will warn the offending players that this
type of behavior is not allowed on your server, and ultimately kick, and or ban them for a predetermined time limit.

Game servers supported:

- Altitude
- Arma II / Arma III
- Battlefield 3 / Battlefield 4 / Battlefield Hardline / Battlefield Bad Company 2
- Chivalry Medieval Warfare
- Call of Duty 1 / 2 / 4 (iw3) / 4x / 4 GameRanger / 5 / 6 (iw5) / 7 (t6) / 8 (iw5)
- Counter-Strike: Global Offensive
- Enemy Territory / Enemy Territory Pro
- Insurgency
- Urban Terror 4.1 / 4.2 / 4.3
- Medal of Honor 2010 / Medal of Honor Warfighter
- Open Arena
- Red Orchestra 2
- Smokin' Guns
- Soldier of Fortune 2
- World of Padman

## Installation

Requirements: **Python 3.11 or newer** and a database (SQLite ships with Python;
MySQL/MariaDB or PostgreSQL are optional).

```bash
python -m venv .venv
.venv/bin/pip install b3                 # or: pip install -e ".[postgresql,test]"
```

Optional extras:

- `postgresql` — PostgreSQL storage support (psycopg 3)
- `sftp` — SFTP log tailing (paramiko 3)

## Running

```bash
b3_run -c b3.ini          # start B3 with the given main config
b3_run --help             # all options
```

`b3_debug.py` provides the profiling entry points (`--memory*`, `--profile*`).

## Development

See `CONTRIBUTING.md`. Quick start:

```bash
pip install -e ".[postgresql,test]"
pytest                     # whole suite (xdist, ~40 s)
ruff check b3 tests        # lint
```

## Previous and Current Developers (Hall of Fame)

_[ThorN], [xlr8or], ttlogic, [Courgette], [Fenix], [Bakes], [spacepig], [Durzo], eire.32, [grosbedo], [Freelander], [82ndAB.Bravo17],
[Just a baka], [Ozon]_ and a big thanks to you, who has offered us snippets of code and improvements on an
incidental basis. Without you B3 wouldn't be this intelligent!

[ThorN]: https://github.com/six8
[xlr8or]: https://github.com/markweirath
[Courgette]: https://github.com/thomasleveil
[Bakes]: https://github.com/j-baker
[spacepig]: https://github.com/spacepig
[Durzo]: https://github.com/durzo
[grosbedo]: https://github.com/grosbedo
[Freelander]: https://github.com/ozguruysal
[82ndAB.Bravo17]: https://github.com/82ndab-Bravo17
[Just a baka]: https://github.com/justabaka
[Fenix]: https://github.com/danielepantaleone
[Ozon]: https://github.com/ozon

## Credits & Thanks

B3 ran on game servers for over a decade because of these people: see
[CREDITS.md](CREDITS.md) for the full list of developers, the vendored
libraries and their licenses.

## Derivative work

This is a community continuation of Big Brother Bot, originally created by
Michael "ThorN" Thornton and the B3 team (upstream:
https://github.com/BigBrotherBot/big-brother-bot). It is not affiliated with or
endorsed by the original project; the name is used descriptively.

## License

GNU General Public License, version 2 or later (`GPL-2.0-or-later`) — the full
text is in [LICENSE](LICENSE). Every source file carries the GPL header block.

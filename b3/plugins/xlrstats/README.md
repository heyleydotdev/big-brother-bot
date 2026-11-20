# XLRstats 3.0.0

XLRstats is the BigBrotherBot statistics plugin. It stores kills, deaths,
teamkills, weapon and map usage, body parts and action stats, computes an ELO
skill for every player, and exposes the usual `!xlrstats` in-game commands.

Version 3.0.0 is the first stable release of the plugin on Python 3. It runs
on MySQL, PostgreSQL and SQLite.

## Requirements

- BigBrotherBot 3.0.0 or later (Python 3.11+).
- A writable database: MySQL, PostgreSQL or SQLite.
- Optional: an XLRstats webfront (v2 or v3) for the top list settings and the
  webfront player pages.

## Installation

1. Enable the plugin in the `[plugins]` section of your main config:

   ```ini
   xlrstats: @b3/conf/plugin_xlrstats.ini
   ```

2. The shipped `plugin_xlrstats.ini` contains all settings and their defaults.
3. Start B3. Missing `xlr_*` tables are created automatically.
4. Optionally set `webfronturl` and `servernumber`; see below.

The plugin needs the database account to be able to create tables and indexes
on the first start. Grant `CREATE` (and `ALTER`) for that database.

## Configuration

### Settings (`[settings]`)

| Setting | Default | Description |
|---|---|---|
| `minplayers` | `3` | Minimum players before stats are collected. |
| `minlevel` | `guest` | Minimum group level for a player to be tracked. `guest` tracks everyone. |
| `defaultskill` | `1000` | Skill a new player starts with. |
| `steepness` | `600` | ELO steepness; higher means skill changes more slowly. |
| `Kfactor_high` | `16` | Skill transferred by a kill until the player has played `Kswitch_confrontations` games. |
| `Kfactor_low` | `4` | Skill transferred after that many confrontations. |
| `Kswitch_confrontations` | `50` | Games before the low K-factor applies. |
| `suicide_penalty_percent` | `0.05` | Skill lost on a suicide, as a fraction of current skill. |
| `tk_penalty_percent` | `0.1` | Skill lost on a teamkill, as a fraction of current skill. |
| `prematch_maxtime` | `70` | Seconds of warm-up during which kills do not count. |
| `onemaponly` | `no` | Keep stats for the current map only. |
| `provisional_ranking` | `yes` | Do not change opponents' skill during a new player's first confrontations. |
| `announce` | `no` | Announce points gained/lost after each confrontation. |
| `keep_history` | `yes` | Keep weekly and monthly snapshots. |
| `keep_time` | `yes` | Track time played (`ctime` table). |
| `auto_correct` | `yes` | Rescale the skill pool every two hours to keep it healthy. |
| `auto_purge` | `no` | Delete players and their stats after `_purge_player_days` of inactivity. Cannot be undone. |
| `hide_bots` | `yes` | Hide bots from the webfront list. |
| `exclude_bots` | `yes` | Do not count kills and damage involving bots. |
| `silent` | `no` | Do not announce when stats collection is enabled or disabled. |
| `webfrontversion` | `2` | `2` or `3`; selects the webfront request format. |
| `webfronturl` | empty | Base URL of the webfront. Empty means no webfront. |
| `servernumber` | `0` | Server number in the webfront configuration. |
| `damage_assist_release` | `10` | Seconds before death during which damage still awards an assist (CoD series). |
| `assist_timespan` | `2` | Same for games without damage information. |

Two settings are internal and not in the shipped file: `_auto_correct_ignore_days`
(60) and `_purge_player_days` (365).

### Commands (`[commands]`)

| Command | Default level | Description |
|---|---|---|
| `!xlrstats [name]` | `user` | Show a player's stats. |
| `!xlrtopstats [n]` | `reg` | Show the top players of the last 14 days. |
| `!xlrhide <player> <on/off>` | `fulladmin` | Hide or unhide a player from the webfront. |
| `!xlrid <token>` | `guest` | Save a webfront v3 player token. |
| `!xlrstatus` | `user` | Show whether stats are being collected. |
| `!xlrinit yes` | `superadmin` | Truncate every XLRstats table and recreate missing ones. Destructive. |

### Database tables

`xlr_playerstats`, `xlr_weaponstats`, `xlr_weaponusage`, `xlr_bodyparts`,
`xlr_playerbody`, `xlr_opponents`, `xlr_mapstats`, `xlr_playermaps`,
`xlr_actionstats`, `xlr_playeractions`, `xlr_history_monthly`,
`xlr_history_weekly`, `ctime`.

The names can be overridden with an optional `[tables]` section; every table
must then exist or be creatable.

### Webfront

- v2: `webfrontversion: 2`, `webfronturl: http://yoursite/xlrstats`,
  `servernumber: 0`. The plugin requests
  `/?config=0&func=pluginreq` and receives `minKills,minRounds,maxDays`.
- v3: `webfrontversion: 3`, `webfronturl: http://xlrstats.example`,
  `servernumber: 1`. The request is `/1/pluginreq/index`; the plugin also
  uses `id_token` for the player pages.

The webfront request runs in a daemon thread with a 5 second timeout; a
frontend that is down does not block B3 startup or shutdown.

## Upgrading from 2.x / beta.17

1. Back up the database.
2. Keep the default `xlr_*` table names (or keep your `[tables]` overrides).
3. Start B3. Missing tables are created, and the schema update adds
   `id_token` where needed on MySQL, SQLite and PostgreSQL.
4. The old `recreate-xlrstats.sql` script is obsolete. `!xlrinit yes` is the
   in-game way to reset everything, and it is intentionally destructive.
5. `auto_correct` is enabled by default and may rescale skills after the
   first start. Check `!xlrstatus` and the log before enabling `auto_purge`.

If a schema update cannot run (read-only account or missing `ALTER` rights), the
plugin logs an explicit error instead of silently collecting stats with a
missing column.

## How skill is computed

The plugin uses an ELO-like pool. A kill transfers skill from the victim to the
killer; the K-factor depends on experience, the skill difference and the
`Kfactor_*` settings. Suicides and teamkills subtract a percentage. The
provisional phase protects new players. `auto_correct` keeps the active pool's
average near `defaultskill + 100`.

## Troubleshooting

- `!xlrstatus` says stats are disabled: check `minplayers` and the current
  player count.
- No stats for a player: check `minlevel`, and that the player is not a bot.
- `database schema update failed: missing column id_token`: give the database
  account `ALTER` rights, or add the column manually.
- `could not create schema ... missing SQL script`: the install is incomplete;
  reinstall the package (the `sql/` directory must ship with the plugin).
- Enable `log_level: 10` and look for `XlrstatsPlugin` and `Query failed`
  lines; the failing query is logged with the player/stat context.

## Credits

xlr8or, ttlogic, Mark Weirath, 82ndab-Bravo17, Fenix, Courgette and the B3
contributors. See the repository `CREDITS.md` and the plugin `CHANGELOG`.

## License

GNU General Public License v2 or later, the same as BigBrotherBot.

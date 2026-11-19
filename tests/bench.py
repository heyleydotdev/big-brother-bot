#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

"""
B3 core benchmark.

Measures what the py3 port must not regress:

  * import time (includes the module level fake console boot)
  * dedicated console boot time (config + storage + admin plugin)
  * RSS memory after boot and after the event loop
  * synchronous event processing throughput through the admin plugin,
    which is B3's real hot path (config parsing, command routing)
  * tracemalloc top allocation sites during the loop
  * a replay of canned q3-family log lines through the real iourt42 parser

Run from the repository root:

    python tests/bench.py [number_of_events]     (default 10000)

CI runs it after the tests on python 3.11 and writes the numbers to the job
summary. When a change claims a performance win, put the before/after numbers
in the commit message (this file is not collected by pytest).
"""

import sys
import time
import io
import contextlib
import tracemalloc

EVENTS = ['regular chat line: nothing to see here',
          '!help',
          'another regular line: hello world',
          '!b3',
          'regular say: benchmarking the port']

# representative q3-family log lines: game init, kills, chat, radio and votes
PARSER_LINES = [
    'InitGame: \\sv_hostname\\bench\\mapname\\ut4_casa',
    'Kill: 0 1 38: Patate killed psyp by UT_MOD_GLOCK',
    'say: 2 BenchPlayer: hello there',
    'say: 6 ^5Marcel^2[^6CZARMY^2]: !help',
    'Radio: 0 - 7 - 2 - "New Alley" - "I\'m going for the flag"',
    'Callvote: 1 - "map dressingroom"',
    'Vote: 0 - 2',
    'VotePassed: 1 - 0 - "reload"',
]


def bench_parser(n_lines):
    """
    Replay canned q3-family log lines through the real iourt42 parser, the
    same way the game log pump feeds it in production.
    """
    from b3.config import XmlConfigParser
    from b3.fake import FakeConsole
    from b3.parsers.q3a.abstractParser import AbstractParser

    # same mounting trick the tests use: run the q3 parser on the fake console
    AbstractParser.__bases__ = (FakeConsole,)
    from b3.parsers.iourt42 import Iourt42Parser

    conf = XmlConfigParser()
    conf.loadFromString('<configuration><settings name="server">'
                        '<set name="game_log"/></settings></configuration>')
    parser = Iourt42Parser(conf)

    errors = 0
    tracemalloc.start()
    t0 = time.perf_counter()
    for i in range(n_lines):
        try:
            parser.parseLine(PARSER_LINES[i % len(PARSER_LINES)])
        except Exception:
            errors += 1
    loop_time = time.perf_counter() - t0
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return loop_time, peak, errors



def main():
    n_events = int(sys.argv[1]) if len(sys.argv) > 1 else 10000

    print('== B3 core benchmark ==')
    print('python          : %s' % sys.version.split()[0])
    print('events          : %s' % n_events)

    # FakeConsole prints every message it routes: keep the real string
    # building work but swallow the terminal writes, they would otherwise
    # dominate the measurements
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):

        # -- import + first console boot (b3.fake builds one at import time)
        t0 = time.perf_counter()
        import b3.fake
        import_time = time.perf_counter() - t0

        import logging
        # keep the logging calls in the measured path but drop the stderr
        # writes, they would otherwise dominate the timings
        logging.disable(logging.CRITICAL)

        from b3.fake import FakeConsole
        from b3.plugins.admin import AdminPlugin

        # -- dedicated console boot (same path the tests use)
        t0 = time.perf_counter()
        console = FakeConsole('@b3/conf/b3.distribution.ini')
        admin = AdminPlugin(console, '@b3/conf/plugin_admin.ini')
        admin.onLoadConfig()
        admin.onStartup()
        boot_time = time.perf_counter() - t0

        # -- a few authed players, like a real server
        players = []
        for cid, name in (('1', 'bench1'), ('2', 'bench2'), ('3', 'bench3'), ('4', 'bench4')):
            client = console.clients.newClient(cid, name=name, guid='bench_guid_%s' % cid)
            client.authed = True
            players.append(client)

        import psutil
        rss_boot = psutil.Process().memory_info().rss

        # -- synchronous event flood through the admin plugin: B3's hot path
        get_event = console.getEvent
        handle_event = admin.parseEvent
        say_events = [get_event('EVT_CLIENT_SAY', text, player)
                      for text in EVENTS for player in players]

        tracemalloc.start()
        t0 = time.perf_counter()
        for i in range(n_events):
            handle_event(say_events[i % len(say_events)])
        loop_time = time.perf_counter() - t0
        peak_tracemalloc = tracemalloc.get_traced_memory()[1]
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()

        rss_after = psutil.Process().memory_info().rss

        # -- parser replay: the real game-log hot path
        parser_time, parser_peak, parser_errors = bench_parser(n_events)
        rss_after_parser = psutil.Process().memory_info().rss

        logging.disable(logging.NOTSET)

    print('import b3.fake  : %8.0f ms (module import + default console boot)' % (import_time * 1000))
    print('console boot    : %8.0f ms (config + sqlite storage + admin plugin)' % (boot_time * 1000))
    print('rss after boot  : %8.1f MB' % (rss_boot / 1048576.0))
    print('event loop      : %8.2f s  => %8.0f events/sec' % (loop_time, n_events / loop_time))
    print('rss after loop  : %8.1f MB' % (rss_after / 1048576.0))
    print('tracemalloc peak: %8.2f MB during the event loop' % (peak_tracemalloc / 1048576.0))
    print('parser replay   : %8.2f s  => %8.0f lines/sec (iourt42, parser errors: %s)'
          % (parser_time, n_events / parser_time, parser_errors))
    print('rss after replay: %8.1f MB' % (rss_after_parser / 1048576.0))
    print('tracemalloc peak: %8.2f MB during the parser replay' % (parser_peak / 1048576.0))
    print('top allocations during the loop:')
    for stat in snapshot.statistics('lineno')[:5]:
        print('    %6.2f MB  %s' % (stat.size / 1048576.0, stat.traceback.format()[0].strip()))


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Watchdog wrapper for nosetests: if the test run exceeds the given number of
# seconds, dump the stack of every thread to stdout and exit non-zero.
# Pure standard library (Python 2/3), cross platform.
#
# USAGE: python test_watchdog.py 300 <regular nosetests arguments>

import os
import sys
import threading
import traceback

LIMIT_SECONDS = int(sys.argv[1])
del sys.argv[1]


def _dump_and_exit():
    print('')
    print('=== TEST WATCHDOG: run exceeded %s seconds, dumping all thread stacks ===' % LIMIT_SECONDS)
    for thread_id, stack_frame in sys._current_frames().items():
        print('--- thread 0x%x ---' % thread_id)
        traceback.print_stack(stack_frame)
    print('=== TEST WATCHDOG: exiting ===')
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(9)


watchdog = threading.Timer(LIMIT_SECONDS, _dump_and_exit)
watchdog.daemon = True
watchdog.start()

import nose
result = nose.run(argv=sys.argv)
sys.exit(0 if result else 1)


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

import functools
import http.server
import os
import shutil
import tempfile
import threading
import time
import urllib.request

from b3.config import CfgConfigParser
from b3.functions import splitDSN
from b3.plugins.httpytail import HttpytailPlugin
from tests import B3TestCase


class _QuietHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, *args):
        pass


class Test_httpytail_update(B3TestCase):
    """the remote log is mirrored locally as bytes (this broke in the 2.0.0 port)"""

    def setUp(self):
        B3TestCase.setUp(self)
        self.dir = tempfile.mkdtemp()
        self.remote = os.path.join(self.dir, 'game.log')
        with open(self.remote, 'wb') as f:
            f.write(b'say: one\nsay: two\n')

        handler = functools.partial(_QuietHandler, directory=self.dir)
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

        self.mirror = os.path.join(self.dir, 'mirror.log')
        self.plugin = HttpytailPlugin(self.console, CfgConfigParser())

    def tearDown(self):
        self.plugin.stop_event.set()
        self.server.shutdown()
        self.server.server_close()
        urllib.request.install_opener(None)   # update() installs a global opener
        shutil.rmtree(self.dir, ignore_errors=True)
        B3TestCase.tearDown(self)

    def _mirror_content(self):
        try:
            with open(self.mirror, 'rb') as f:
                return f.read()
        except OSError:
            return b''

    def test_remote_log_is_mirrored(self):
        url = f'http://127.0.0.1:{self.server.server_address[1]}/game.log'
        self.plugin.lgame_log = self.mirror
        self.plugin.httpconfig = splitDSN(url)

        thread = threading.Thread(target=self.plugin.update, daemon=True)
        thread.start()

        # the first cycle only records the current end of the remote file
        time.sleep(0.6)
        with open(self.remote, 'ab') as f:
            f.write(b'say: three\n')

        deadline = time.time() + 5
        while time.time() < deadline and b'say: three' not in self._mirror_content():
            time.sleep(0.05)
        self.plugin.stop_event.set()
        thread.join(5)

        content = self._mirror_content()
        self.assertIn(b'B3 has been restarted', content)
        self.assertIn(b'say: three', content)
        self.assertNotIn(b"b'", content)   # a bytes repr would mean a str/bytes mixup

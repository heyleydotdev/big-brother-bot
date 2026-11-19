
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

import logging
import unittest
from unittest.mock import Mock, call

from b3.clients import Client
from b3.config import XmlConfigParser
from b3.parsers.cod4x import Cod4XParser

log = logging.getLogger("test")
log.setLevel(logging.INFO)

# keep a reference to unpatch core B3 stuff to restore them at the end of tests
original_client_auth = Client.auth


def tearDownModule():
    Client.auth = original_client_auth


# CoD4x non-legacy status output: the map line is not guaranteed to be first
STATUS = '''\
Status
map     : mp_crash
num score ping playerid steamid name lastmsg address qport rate
--- ----- ---- -------- ------- ---------------- ------- ------- ----- -----
  0    10   42 76561198000000001 76561197960287930 BenchPlayer^7 0 11.22.33.44:28960 1234 25000
  1     5   12 76561198000000002 76561197960287930 Other Player^7 0 22.33.44.55:-10803 -23569 25000
'''


class Cod4XTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from b3.parsers.q3a.abstractParser import AbstractParser
        from b3.fake import FakeConsole
        AbstractParser.__bases__ = (FakeConsole,)

    def setUp(self):
        self.parser_conf = XmlConfigParser()
        self.parser_conf.loadFromString("""<configuration>
                <settings name="server">
                    <set name="game_log"/>
                </settings>
            </configuration>""")
        self.console = Cod4XParser(self.parser_conf)
        self.console.PunkBuster = None
        self.console.write = Mock(side_effect=lambda cmd, *a, **kw: STATUS if cmd == 'status' else '')

    def tearDown(self):
        del self.console.clients
        self.console.working = False


class Test_status_parsing(Cod4XTestCase):

    def test_getMap_reads_padded_label(self):
        self.assertEqual('mp_crash', self.console.getMap())

    def test_getPlayerList(self):
        players = self.console.getPlayerList()
        self.assertEqual(['0', '1'], sorted(players))
        self.assertEqual('76561198000000001', players['0']['guid'])
        self.assertEqual('76561197960287930', players['0']['steam'])
        self.assertEqual('BenchPlayer', players['0']['name'])
        self.assertEqual('11.22.33.44', players['0']['ip'])
        self.assertEqual('Other Player', players['1']['name'])

    def test_getPlayerPings(self):
        self.assertDictEqual({'0': 42, '1': 12}, self.console.getPlayerPings())

    def test_getPlayerScores(self):
        self.assertDictEqual({'0': 10, '1': 5}, self.console.getPlayerScores())


class Test_commands(Cod4XTestCase):

    def test_unban_uses_the_guid(self):
        self.console.unban(Client(guid='76561198000000001'))
        self.assertIn(call('unban 76561198000000001'), self.console.write.mock_calls)

    def test_tempban_by_cid(self):
        self.console.tempban('2', reason='cheating', duration=5)
        self.assertIn(call('tempban 2 5m cheating'), self.console.write.mock_calls)

    def test_startup_keeps_the_base_initialisation(self):
        self.console.startup()
        # the cod parser creates the world client and reads the map
        self.assertIn('-1', self.console.clients)
        self.assertEqual('mp_crash', self.console.game.mapName)
        # then the server is switched to 64 bit ids
        self.assertIn(call('sv_usesteam64id  1', maxRetries=3), self.console.write.mock_calls)

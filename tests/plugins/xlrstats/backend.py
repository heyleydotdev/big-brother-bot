
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

from unittest.mock import Mock

from b3 import TEAM_BLUE
from b3 import TEAM_RED
from b3.fake import FakeClient
from tests import B3TestCase
from tests.plugins.xlrstats.test_xlrstats import XlrstatsTestCase


class XlrstatsBackendTestCase(XlrstatsTestCase):

    __test__ = False  # base class: only the backend subclasses are collected
    """
    Run the XLRstats SQL paths against a real storage backend.

    Subclasses provide the backend connection; the tests themselves are shared
    so MySQL and PostgreSQL execute exactly the same statements.
    """

    def setUp(self):
        self._create_database()
        XlrstatsTestCase.setUp(self)
        self._sqlite_storage = self.console.storage
        self.storage = self._new_storage()
        self.storage.connect()
        self.console.storage = self.storage
        self.init()
        # the fixture's world client lives in the sqlite storage and its id can
        # collide with the first client of the new backend
        self.p._world_clientid = None

    def tearDown(self):
        XlrstatsTestCase.tearDown(self)
        # stop the cron before closing the connections it may still use
        B3TestCase.tearDown(self)
        if getattr(self, 'storage', None):
            self.storage.shutdown()
        if getattr(self, '_sqlite_storage', None):
            self._sqlite_storage.shutdown()
        self._drop_database()

    def _new_storage(self):
        raise NotImplementedError

    def _create_database(self):
        raise NotImplementedError

    def _drop_database(self):
        raise NotImplementedError

    def _client(self, name, guid, slot="1", **kwargs):
        # the client row is required by the xlr_playerstats foreign key
        client = FakeClient(console=self.console, name=name, guid=guid, groupBits=1, **kwargs)
        client.id = self.storage.setClient(client)
        client.connects(slot)
        client.groupBits = 1
        client._groups = None  # drop the cached guest group from the auth pass
        return client

    def test_schema_update_adds_id_token_to_a_2x_database(self):
        self.storage.query(f"ALTER TABLE {self.p.playerstats_table} DROP COLUMN id_token")
        self.p.build_database_schema()
        self.storage.query(f"SELECT id_token FROM {self.p.playerstats_table} LIMIT 1").close()

    def test_stats_are_saved_with_a_quote_in_the_name(self):
        client = self._client("P1", "P1_GUID")
        stats = self.p.get_PlayerStats(client)
        stats.fixed_name = "O'Neil"
        self.p.save_Stat(stats)
        self.assertEqual("O'Neil", self.p.get_PlayerStats(client).fixed_name)

    def test_kill_is_saved(self):
        p1 = self._client("P1", "P1_GUID", team=TEAM_BLUE)
        p2 = self._client("P2", "P2_GUID", slot="2", team=TEAM_RED)
        self.p._xlrstats_active = True
        p1.kills(p2)
        self.assertEqual(1, self.p.get_PlayerStats(p1).kills)

        p1.clearMessageHistory()
        p1.says("!xlrstats")
        self.assertIn("XLR Stats: P1", p1.message_history[0])

    def test_teamkill_is_saved(self):
        p1 = self._client("P1", "P1_GUID", team=TEAM_RED)
        p2 = self._client("P2", "P2_GUID", slot="2", team=TEAM_RED)
        self.p._xlrstats_active = True
        p1.kills(p2)
        self.assertEqual(1, self.p.get_PlayerStats(p1).teamkills)

    def test_round_change_is_saved(self):
        client = self._client("P1", "P1_GUID")
        self.p._xlrstats_active = True
        self.p.min_players = 1
        self.p.prematch_maxtime = 0
        self.console.game.mapName = "Map1"
        map_stats = self.p.get_MapStats("Map1")
        self.p.save_Stat(map_stats)

        self.console.queueEvent(self.console.getEvent('EVT_GAME_ROUND_START'))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JOIN', client=client))
        self.console.queueEvent(self.console.getEvent('EVT_GAME_ROUND_END'))
        self.console.queueEvent(self.console.getEvent('EVT_GAME_ROUND_START'))
        self.console.queueEvent(self.console.getEvent('EVT_CLIENT_JOIN', client=client))

        self.assertEqual(2, self.p.get_PlayerStats(client).rounds)

    def test_top_list_query_runs(self):
        messages = []
        cmd = Mock()
        cmd.sayLoudOrPM.side_effect = lambda client, msg: messages.append(msg)
        self.p.doTopList(None, self._client("P1", "P1_GUID"), cmd)
        self.assertTrue(any('Qualify for the toplist' in m for m in messages))


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

from b3.clients import Client
from b3.functions import splitDSN
from mockito import when, ANY
from b3.storage.sqlite import SqliteStorage
from tests import B3TestCase
from tests.core.storage.common import StorageAPITest

SQLITE_DB = ":memory:"
#SQLITE_DB = "c:/Users/Thomas/b3.db"

class Test_sqlite(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)
        self.storage = self.console.storage = SqliteStorage('sqlite://' + SQLITE_DB, splitDSN('sqlite://' + SQLITE_DB), self.console)
        self.storage.connect()
        #self.storage.queryFromFile("@b3/sql/sqlite/b3.sql")

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.shutdown()

    def test_status_after_shutdown(self):
        self.storage.shutdown()
        self.assertFalse(self.storage.status())

    def test_getGroups_is_read_from_storage_every_time(self):
        # the group list used to be cached for the life of the process, so a
        # group added by an external tool was unknown until restart
        self.storage.getGroups()
        self.storage.query("INSERT INTO `groups` (id, name, keyword, level) VALUES (99, 'Test', 'test', 3)")
        self.assertIn('test', [g.keyword for g in self.storage.getGroups()])

    def test_getClient_does_not_fall_back_to_cache_when_the_query_fails(self):
        # the admins_cache is for a database that is down: a query error while
        # connected must not silently grant the cached level
        when(self.storage).query(ANY).thenRaise(RuntimeError('query failed'))
        when(self.console.config).has_option('admins_cache', 'someguid').thenReturn(True)
        when(self.console.config).get('admins_cache', 'someguid', raw=True).thenReturn('7, cached, 100')
        self.assertRaises(RuntimeError, self.storage.getClient, Client(guid='someguid'))

    def test_getTables(self):
        self.assertSetEqual(set(
            ['sqlite_sequence',
             'aliases',
             'ipaliases',
             'clients',
             'groups',
             'penalties',
             'data',
            ]), set(self.storage.getTables()))

if __name__ == '__main__':
    import unittest
    unittest.main()


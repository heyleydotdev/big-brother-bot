
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

import os
import unittest

from mockito import mock

from b3.functions import splitDSN
from b3.storage.postgresql import PostgresqlStorage
from tests import B3TestCase
from tests.plugins.xlrstats.test_xlrstats import XlrstatsTestCase

POSTGRESQL_TEST_HOST = os.environ.get('POSTGRESQL_TEST_HOST', 'localhost')
POSTGRESQL_TEST_USER = os.environ.get('POSTGRESQL_TEST_USER', 'b3test')
POSTGRESQL_TEST_PASSWORD = os.environ.get('POSTGRESQL_TEST_PASSWORD', 'test')
POSTGRESQL_TEST_DB = os.environ.get('POSTGRESQL_TEST_DB', 'b3_test')
# a dedicated database: the storage tests drop/recreate b3_test and may run in parallel
XLRSTATS_TEST_DB = POSTGRESQL_TEST_DB + '_xlrstats'

is_postgresql_ready = True
no_postgresql_reason = ''

try:
    import psycopg
except ImportError:
    psycopg = None
    is_postgresql_ready = False
    no_postgresql_reason = "no psycopg module available"
else:
    try:
        # same driver as b3.storage.postgresql (psycopg 3)
        psycopg.connect(host=POSTGRESQL_TEST_HOST,
                        user=POSTGRESQL_TEST_USER,
                        password=POSTGRESQL_TEST_PASSWORD,
                        dbname='postgres',
                        connect_timeout=int(os.environ.get('PGCONNECT_TIMEOUT', '2'))).close()
    except Exception as err:
        is_postgresql_ready = False
        no_postgresql_reason = "%r" % err


def _connect(dbname):
    return psycopg.connect(host=POSTGRESQL_TEST_HOST,
                           user=POSTGRESQL_TEST_USER,
                           password=POSTGRESQL_TEST_PASSWORD,
                           dbname=dbname,
                           connect_timeout=int(os.environ.get('PGCONNECT_TIMEOUT', '2')))


@unittest.skipUnless(is_postgresql_ready, no_postgresql_reason)
class Test_xlrstats_postgresql(XlrstatsTestCase):

    def setUp(self):
        self._create_database()
        XlrstatsTestCase.setUp(self)
        self._sqlite_storage = self.console.storage
        dsn = "postgresql://%s:%s@%s/%s" % (POSTGRESQL_TEST_USER, POSTGRESQL_TEST_PASSWORD,
                                            POSTGRESQL_TEST_HOST, XLRSTATS_TEST_DB)
        self.storage = PostgresqlStorage(dsn, splitDSN(dsn), self.console)
        self.storage.connect()
        self.console.storage = self.storage
        self.init()

    def tearDown(self):
        XlrstatsTestCase.tearDown(self)
        # stop the cron before closing the connections it may still use
        B3TestCase.tearDown(self)
        if getattr(self, 'storage', None):
            self.storage.shutdown()
        if getattr(self, '_sqlite_storage', None):
            self._sqlite_storage.shutdown()
        self._drop_database()

    def _create_database(self):
        connection = _connect('postgres')
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (XLRSTATS_TEST_DB,))
            cursor.execute('DROP DATABASE IF EXISTS "%s"' % XLRSTATS_TEST_DB)
            cursor.execute("CREATE DATABASE \"%s\" ENCODING 'utf8'" % XLRSTATS_TEST_DB)
        connection.close()

    def _drop_database(self):
        connection = _connect('postgres')
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (XLRSTATS_TEST_DB,))
            cursor.execute('DROP DATABASE IF EXISTS "%s"' % XLRSTATS_TEST_DB)
        connection.close()

    def test_schema_update_adds_id_token_to_a_2x_database(self):
        # a 2.x database has the table but not the column
        self.storage.query("ALTER TABLE %s DROP COLUMN id_token" % self.p.playerstats_table)
        self.p.build_database_schema()
        self.storage.query("SELECT id_token FROM %s LIMIT 1" % self.p.playerstats_table).close()

    def test_stats_are_saved_with_a_quote_in_the_name(self):
        client = mock()
        client.id = 43
        client.maxLevel = 1
        stats = self.p.get_PlayerStats(client)
        stats.fixed_name = "O'Neil"
        self.p.save_Stat(stats)
        self.assertEqual("O'Neil", self.p.get_PlayerStats(client).fixed_name)

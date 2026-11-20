
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

from b3.functions import splitDSN
from b3.storage.postgresql import PostgresqlStorage
from tests import B3TestCase
from tests.core.storage.common import StorageAPITest

"""
    NOTE: you can customize the PostgreSQL host, database and credential using the following
    environment variables :
        POSTGRESQL_TEST_HOST
        POSTGRESQL_TEST_USER
        POSTGRESQL_TEST_PASSWORD
        POSTGRESQL_TEST_DB

    Make sure to execute this query (with adjusted parameters) before running tests:
        >>> CREATE ROLE b3test WITH PASSWORD 'test' LOGIN CREATEDB;
"""

POSTGRESQL_TEST_HOST = os.environ.get('POSTGRESQL_TEST_HOST', 'localhost')
POSTGRESQL_TEST_USER = os.environ.get('POSTGRESQL_TEST_USER', 'b3test')
POSTGRESQL_TEST_PASSWORD = os.environ.get('POSTGRESQL_TEST_PASSWORD', 'test')
POSTGRESQL_TEST_DB = os.environ.get('POSTGRESQL_TEST_DB', 'b3_test')

#===============================================================================
#
# Test if we can run the PostgreSQL tests
#
#===============================================================================

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
        # probe with the same driver as b3.storage.postgresql (psycopg 3):
        # probing with psycopg2 skipped this whole class even in CI
        psycopg.connect(host=POSTGRESQL_TEST_HOST,
                        user=POSTGRESQL_TEST_USER,
                        password=POSTGRESQL_TEST_PASSWORD,
                        dbname='postgres',
                        # CI sets PGCONNECT_TIMEOUT=10; keep local runs quick
                        connect_timeout=int(os.environ.get('PGCONNECT_TIMEOUT', '2'))).close()
    except psycopg.Error as err:
        is_postgresql_ready = False
        no_postgresql_reason = "%r" % err
    except Exception as err:
        is_postgresql_ready = False
        no_postgresql_reason = "%r" % err

#===============================================================================
#
# Load the tests
#
#===============================================================================

class Test_ci_has_postgresql(unittest.TestCase):

    """A skipped backend must fail CI, not silently test only SQLite."""

    @unittest.skipUnless(os.environ.get('CI'), 'only enforced in CI')
    def test_postgresql_is_ready(self):
        self.assertTrue(is_postgresql_ready, no_postgresql_reason)


@unittest.skipIf(not is_postgresql_ready, no_postgresql_reason)
class Test_PostgreSQL(B3TestCase, StorageAPITest):

    def setUp(self):
        """this method is called before each test"""
        B3TestCase.setUp(self)

        # keep the storage errors: 'lost connection' hides the real cause
        storage_errors = []
        self.console.error = lambda msg, *a, **kw: storage_errors.append(msg % a if a else msg)
        self.console.critical = lambda msg, *a, **kw: storage_errors.append(msg % a if a else msg)

        try:
            # create a fresh database like Test_MySQL does, since the PostgreSQL server
            # may not have the test database ready (e.g., fresh CI service container)
            connection = psycopg.connect(host=POSTGRESQL_TEST_HOST,
                                         user=POSTGRESQL_TEST_USER,
                                         password=POSTGRESQL_TEST_PASSWORD,
                                         dbname='postgres')
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute('DROP DATABASE IF EXISTS "%s"' % POSTGRESQL_TEST_DB)
            cursor.execute('CREATE DATABASE "%s" ENCODING \'utf8\'' % POSTGRESQL_TEST_DB)
            connection.close()
        except psycopg.Error as e:
            self.fail("Error: %r" % e)

        try:
            dsn = "postgresql://%s:%s@%s/%s" % (POSTGRESQL_TEST_USER, POSTGRESQL_TEST_PASSWORD, POSTGRESQL_TEST_HOST, POSTGRESQL_TEST_DB)
            self.storage = self.console.storage = PostgresqlStorage(dsn, splitDSN(dsn), self.console)
            self.storage.connect()

            tables = self.storage.getTables()
            if tables:
                # dont remove the groups table since we would need it in next tests
                tables.remove('groups')
                self.storage.truncateTable(tables)
        except Exception as e:
            self.fail("Error: %s; storage log: %s" % (e, storage_errors))

    def tearDown(self):
        """this method is called after each test"""
        B3TestCase.tearDown(self)
        self.storage.shutdown()

if __name__ == '__main__':
    import unittest
    unittest.main()


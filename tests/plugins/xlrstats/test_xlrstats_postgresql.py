
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
from tests.plugins.xlrstats.backend import XlrstatsBackendTestCase

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
        no_postgresql_reason = f"{err!r}"


def _connect(dbname):
    return psycopg.connect(host=POSTGRESQL_TEST_HOST,
                           user=POSTGRESQL_TEST_USER,
                           password=POSTGRESQL_TEST_PASSWORD,
                           dbname=dbname,
                           connect_timeout=int(os.environ.get('PGCONNECT_TIMEOUT', '2')))


@unittest.skipUnless(is_postgresql_ready, no_postgresql_reason)
class Test_xlrstats_postgresql(XlrstatsBackendTestCase):

    __test__ = True

    def _new_storage(self):
        dsn = f"postgresql://{POSTGRESQL_TEST_USER}:{POSTGRESQL_TEST_PASSWORD}@{POSTGRESQL_TEST_HOST}/{XLRSTATS_TEST_DB}"
        return PostgresqlStorage(dsn, splitDSN(dsn), self.console)

    def _create_database(self):
        connection = _connect('postgres')
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (XLRSTATS_TEST_DB,))
            cursor.execute(f'DROP DATABASE IF EXISTS "{XLRSTATS_TEST_DB}"')
            cursor.execute(f"CREATE DATABASE \"{XLRSTATS_TEST_DB}\" ENCODING 'utf8'")
        connection.close()

    def _drop_database(self):
        connection = _connect('postgres')
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (XLRSTATS_TEST_DB,))
            cursor.execute(f'DROP DATABASE IF EXISTS "{XLRSTATS_TEST_DB}"')
        connection.close()

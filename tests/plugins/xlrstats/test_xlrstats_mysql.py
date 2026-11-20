
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
from b3.storage.mysql import MysqlStorage
from tests.plugins.xlrstats.backend import XlrstatsBackendTestCase

MYSQL_TEST_HOST = os.environ.get('MYSQL_TEST_HOST', 'localhost')
MYSQL_TEST_USER = os.environ.get('MYSQL_TEST_USER', 'b3test')
MYSQL_TEST_PASSWORD = os.environ.get('MYSQL_TEST_PASSWORD', 'test')
MYSQL_TEST_DB = os.environ.get('MYSQL_TEST_DB', 'b3_test')
# a dedicated database: the storage tests drop/recreate b3_test and may run in parallel
XLRSTATS_TEST_DB = MYSQL_TEST_DB + '_xlrstats_mysql'

is_mysql_ready = True
no_mysql_reason = ''

try:
    import pymysql
except ImportError:
    pymysql = None
    is_mysql_ready = False
    no_mysql_reason = "no pymysql module available"
else:
    try:
        pymysql.connect(host=MYSQL_TEST_HOST,
                        user=MYSQL_TEST_USER,
                        password=MYSQL_TEST_PASSWORD).close()
    except Exception as err:
        is_mysql_ready = False
        no_mysql_reason = f"{err!r}"


def _connect():
    return pymysql.connect(host=MYSQL_TEST_HOST,
                           user=MYSQL_TEST_USER,
                           password=MYSQL_TEST_PASSWORD)


@unittest.skipUnless(is_mysql_ready, no_mysql_reason)
class Test_xlrstats_mysql(XlrstatsBackendTestCase):

    __test__ = True

    def _new_storage(self):
        dsn = f"mysql://{MYSQL_TEST_USER}:{MYSQL_TEST_PASSWORD}@{MYSQL_TEST_HOST}/{XLRSTATS_TEST_DB}"
        return MysqlStorage(dsn, splitDSN(dsn), self.console)

    def _create_database(self):
        connection = _connect()
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{XLRSTATS_TEST_DB}`")
            cursor.execute(f"CREATE DATABASE `{XLRSTATS_TEST_DB}` CHARACTER SET utf8")
        connection.commit()
        connection.close()

    def _drop_database(self):
        connection = _connect()
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{XLRSTATS_TEST_DB}`")
        connection.commit()
        connection.close()

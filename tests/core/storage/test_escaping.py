
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

import unittest

from b3.functions import splitDSN
from b3.querybuilder import QueryBuilder, mysql_escape
from b3.storage.sqlite import SqliteStorage
from tests import B3TestCase


class Test_mysql_escape(unittest.TestCase):

    def test_number(self):
        self.assertEqual('42', mysql_escape(42))

    def test_none(self):
        self.assertEqual('"None"', mysql_escape(None))

    def test_quote(self):
        self.assertEqual('"a\\"b"', mysql_escape('a"b'))

    def test_backslash(self):
        # a trailing backslash used to escape the closing quote (broken query)
        self.assertEqual('"a\\\\b"', mysql_escape('a\\b'))


class Test_sqlite_quoting(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.storage = SqliteStorage('sqlite://:memory:', splitDSN('sqlite://:memory:'), self.console)
        self.storage.connect()
        self.storage.query('CREATE TEMP TABLE t (v text)')

    def tearDown(self):
        self.storage.shutdown()
        B3TestCase.tearDown(self)

    def test_value_with_quote_and_backslash(self):
        value = 'a"b\\c'
        self.storage.query(QueryBuilder(self.storage.db).InsertQuery({'v': value}, 't'))
        cursor = self.storage.query('SELECT v FROM t')
        self.assertEqual(value, cursor.getValue('v'))

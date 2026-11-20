
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

from b3.plugins.xlrstats import PlayerStats
from b3.querybuilder import QueryBuilder
from tests import B3TestCase


class Test_player_name_escaping(B3TestCase):

    def test_name_with_a_quote(self):
        # the name used to be escaped mysql-style (backslash), which sqlite
        # takes literally: the insert failed for a nickname containing a quote
        stats = PlayerStats()
        stats.fixed_name = "O'Neil"
        stats._qb = QueryBuilder(self.console.storage.db)

        self.assertIn("'O''Neil'", stats._insertquery())
        self.assertIn("'O''Neil'", stats._updatequery())

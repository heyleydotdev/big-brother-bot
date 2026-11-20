
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

from unittest.mock import Mock, patch

from b3.plugins.jumper import JumpRun
from tests.plugins.jumper import JumperTestCase


class TestJumpRun_update(JumperTestCase):

    def setUp(self):
        JumperTestCase.setUp(self)
        self.storage = Mock()
        self.storage.db = None
        self.console.storage = self.storage
        self.jumprun = JumpRun(self.p, client=Mock(id=42), mapname='ut4_abbey', way_id=1,
                               way_time=1000, time_add=1000, time_edit=1000, demo='/tmp/demo.dm_68')

    def test_time_edit_is_the_edit_time(self):
        # time_edit used to keep the value of time_add, so an edited run looked untouched
        with patch.object(self.console, 'time', return_value=1234567890):
            self.jumprun.update()
        query = self.storage.query.call_args[0][0]
        self.assertRegex(query, r'time_edit`?\s*=\s*1234567890')
        self.assertNotRegex(query, r'time_edit`?\s*=\s*1000')


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

import sys
import unittest

from b3.run import _autorestart_command


class Test_autorestart_command(unittest.TestCase):

    def test_paths_with_spaces_stay_one_argument(self):
        # a shell string split "C:\Program Files\b3.ini" in two
        command = _autorestart_command(['-c', r'C:\Program Files\b3\b3.ini'])
        self.assertEqual(sys.executable, command[0])
        self.assertIn('-c', command)
        self.assertIn(r'C:\Program Files\b3\b3.ini', command)
        self.assertEqual('--autorestart', command[-1])

    def test_no_args(self):
        self.assertEqual('--autorestart', _autorestart_command()[-1])

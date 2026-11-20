
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
import tempfile
import unittest

from unittest.mock import Mock

from b3.config import CfgConfigParser
from b3.plugins.cmdmanager import CmdmanagerPlugin


class Test_write_ini_config_file(unittest.TestCase):

    def test_writes_command_level(self):
        fd, path = tempfile.mkstemp(suffix='.ini')
        os.close(fd)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('[commands]' + chr(10) + 'help: user' + chr(10))
            conf = CfgConfigParser()
            conf.load(path)
            plugin = CmdmanagerPlugin(Mock(), conf)
            command = Mock()
            command.command = 'help'
            command.plugin = Mock()
            command.plugin.config = conf

            plugin.write_ini_config_file(command, {
                'command_name': 'help',
                'command_level': 'admin',
                'plugin_name': 'admin',
            })

            again = CfgConfigParser()
            again.load(path)
            self.assertEqual('admin', again.get('commands', 'help'))
        finally:
            os.unlink(path)

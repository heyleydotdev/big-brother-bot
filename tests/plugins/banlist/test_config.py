
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

from unittest.mock import Mock

from b3.config import CfgConfigParser
from b3.plugins.banlist import BanlistPlugin
from tests.plugins.banlist import BanlistTestCase


class Test_ini_config(BanlistTestCase):

    def test_ini_config(self):
        console = Mock()
        console.clients.getList.return_value = []
        conf = CfgConfigParser()
        conf.loadFromString("""
[global_settings]
immunity_level: 80
auto_update: no

[commands]
banlistinfo-blinfo: admin

[ip_banlist:ip one]
name: ip one
file: F:/temp/ip.txt
force_ip_range: yes
message: banned

[guid_banlist:guid one]
name: guid one
file: F:/temp/guid.txt

[ip_whitelist:white]
name: white
file: F:/temp/white.txt
""")
        plugin = BanlistPlugin(console, conf)
        plugin.onLoadConfig()

        self.assertEqual(80, plugin._immunity_level)
        self.assertFalse(plugin._auto_update)
        self.assertEqual(2, len(plugin._banlists))
        self.assertEqual(1, len(plugin._whitelists))
        self.assertEqual('ip one', plugin._banlists[0].name)
        self.assertTrue(plugin._banlists[0]._forceRange)
        self.assertEqual('guid one', plugin._banlists[1].name)
        self.assertEqual('white', plugin._whitelists[0].name)


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
from unittest.mock import MagicMock

from b3.config import CfgConfigParser
from b3.plugins.scheduler import SchedulerPlugin


class SchedulerTestCase(unittest.TestCase):

    def setUp(self):
        SchedulerPlugin._restart_tasks = set()
        self.console = MagicMock()
        self.console.config.get.return_value = 'UTC'
        self.console.isFrostbiteGame.return_value = False
        self.console.getPlugin.return_value = MagicMock()

    def load(self, config):
        plugin = SchedulerPlugin(self.console, config)
        plugin.onLoadConfig()
        return plugin


class Test_ini_config(SchedulerTestCase):

    def test_tasks(self):
        conf = CfgConfigParser()
        conf.loadFromString("""
[task:daily1]
type: daily
hour: 2
minutes: 41
rcon1: say hi
rcon2: bigtext hello
enable_plugin1: tk
disable_plugin1: adv

[task:every3m]
type: cron
minutes: */3
rcon1: say every3m

[task:startup]
type: restart
delay: 5m
rcon1: say started

[task:hourly]
type: hourly
minutes: 43
rcon1: say hourly
""")
        plugin = self.load(conf)

        self.assertEqual(4, len(plugin._tasks))
        daily = [t for t in plugin._tasks if t.name == 'daily1'][0]
        self.assertEqual('41', daily.minutes)
        self.assertEqual('2', daily.hour)
        self.assertEqual(2, len(daily.config.findall('rcon')))
        self.assertEqual('say hi', daily.config.findall('rcon')[0].text)
        self.assertEqual(1, len(daily.config.findall('enable_plugin')))
        self.assertEqual('tk', daily.config.findall('enable_plugin')[0].attrib['plugin'])
        self.assertEqual(1, len(plugin._restart_tasks))


class Test_shipped_ini(SchedulerTestCase):

    def test_tasks(self):
        import b3
        conf = CfgConfigParser()
        conf.load(b3.getAbsolutePath('@b3/conf/plugin_scheduler.ini'))
        plugin = self.load(conf)
        self.assertEqual(9, len(plugin._tasks))
        self.assertEqual(0, len(plugin._restart_tasks))

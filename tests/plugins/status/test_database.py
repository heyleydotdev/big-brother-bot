
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

from textwrap import dedent

from b3.config import CfgConfigParser
from b3.plugins.status import StatusPlugin
from tests import B3TestCase


class Test_storeServerinfo(B3TestCase):
    """server variables are upserted, not inserted with mysql-only syntax"""

    def setUp(self):
        B3TestCase.setUp(self)
        conf = CfgConfigParser()
        conf.loadFromString(dedent("""
            [settings]
            interval: 60
            output_file: ~/status.xml
            enableDBsvarSaving: yes
            enableDBclientSaving: no
            """))
        self.p = StatusPlugin(self.console, conf)
        self.p.onLoadConfig()
        self.p.build_schema()

    def test_same_svar_is_updated_not_duplicated(self):
        self.p.storeServerinfo('Map', 'ut4_casa')
        self.p.storeServerinfo('Map', 'ut4_abbey')

        cursor = self.console.storage.query("SELECT name, value FROM current_svars")
        self.assertEqual('Map', cursor.getValue('name'))
        self.assertEqual('ut4_abbey', cursor.getValue('value'))
        cursor.close()

        cursor = self.console.storage.query("SELECT COUNT(*) total FROM current_svars")
        self.assertEqual(1, cursor.getValue('total'))
        cursor.close()

    def test_value_with_a_quote(self):
        self.p.storeServerinfo("Name", "Bob's Server")

        cursor = self.console.storage.query("SELECT value FROM current_svars WHERE name = 'Name'")
        self.assertEqual("Bob's Server", cursor.getValue('value'))
        cursor.close()

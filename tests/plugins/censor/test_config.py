
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

import b3

from tests.plugins.censor import CensorTestCase


class Test_config(CensorTestCase):
    """
    Test different config are correctly loaded.
    """

    def assert_default_badwords_penalty(self):
        self.assertEqual("warning", self.p._defaultBadWordPenalty.type)
        self.assertEqual(0, self.p._defaultBadWordPenalty.duration)
        self.assertEqual("cuss", self.p._defaultBadWordPenalty.keyword)
        self.assertIsNone(self.p._defaultBadWordPenalty.reason)

    def assert_default_badnames_penalty(self):
        self.assertEqual("warning", self.p._defaultBadNamePenalty.type)
        self.assertEqual(0, self.p._defaultBadNamePenalty.duration)
        self.assertEqual("badname", self.p._defaultBadNamePenalty.keyword)
        self.assertIsNone(self.p._defaultBadNamePenalty.reason)

    def test_default_conf(self):
        with open(b3.getAbsolutePath('@b3/conf/plugin_censor.ini')) as default_conf:
            self.init_plugin(default_conf.read())
        self.assertEqual(40, self.p._maxLevel)
        self.assertEqual(3, self.p._ignoreLength)
        self.assertEqual(68, len(self.p._badWords))
        self.assertEqual(17, len(self.p._badNames))
        self.assert_default_badwords_penalty()
        self.assert_default_badnames_penalty()

    def test_ini_rule_with_penalty(self):
        self.init_plugin("""
[badwords]
penalty: warning
reason_keyword: cuss

[badword:test]
regexp: testword
penalty: tempban
reason: no
duration: 5m

[badnames]
penalty: warning
reason_keyword: badname

[badname:testname]
word: testname
""")
        self.assertEqual(1, len(self.p._badWords))
        self.assertEqual('tempban', self.p._badWords[0].penalty.type)
        self.assertEqual(5, self.p._badWords[0].penalty.duration)
        self.assertEqual('no', self.p._badWords[0].penalty.reason)
        self.assertEqual(1, len(self.p._badNames))
        self.assertEqual('warning', self.p._badNames[0].penalty.type)
        self.assertEqual('badname', self.p._badNames[0].penalty.keyword)

    def test_broken_conf__emtpy_conf(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
            </configuration>
        """)
        self.assertEqual(0, self.p._maxLevel)
        self.assertEqual(3, self.p._ignoreLength)
        self.assertEqual(0, len(self.p._badWords))
        self.assertEqual(0, len(self.p._badNames))
        self.assert_default_badwords_penalty()
        self.assert_default_badnames_penalty()

    def test_broken_conf__max_level_missing(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._maxLevel)

    def test_broken_conf__max_level_empty(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
		            <set name="max_level"></set>
                </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._maxLevel)

    def test_broken_conf__max_level_NaN(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
		            <set name="max_level">fo0</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(0, self.p._maxLevel)


    def test_broken_conf__ignore_length_missing(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                </settings>
            </configuration>
        """)
        self.assertEqual(3, self.p._ignoreLength)

    def test_broken_conf__ignore_length_empty(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="ignore_length"></set>
                </settings>
            </configuration>
        """)
        self.assertEqual(3, self.p._ignoreLength)

    def test_broken_conf__ignore_length_NaN(self):
        self.init_plugin(r"""
            <configuration plugin="censor">
                <settings name="settings">
                    <set name="ignore_length">fo0</set>
                </settings>
            </configuration>
        """)
        self.assertEqual(3, self.p._ignoreLength)


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

import configparser
import logging
import os
import shutil
import tempfile
from unittest import TestCase
import unittest
import sys
from b3.config import XmlConfigParser, CfgConfigParser, ConfigFileNotValid
from tests import B3TestCase

@unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
class Test_XmlConfigParser_windows(B3TestCase):

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.setXml("""
            <configuration plugin="test">
                <settings name="settings">
                    <set name="output_file">@conf/status.xml</set>
                </settings>
            </configuration>
        """)

    def test_getpath(self):
        self.console.config.fileName = r"c:\some\where\conf\b3.xml"
        self.assertEqual(r"c:\some\where\conf\status.xml", self.conf.getpath('settings', 'output_file'))

    def test_issue_xlr8or_18(self):
        self.console.config.fileName = r"b3.xml"
        self.assertEqual(r"status.xml", self.conf.getpath('settings', 'output_file'))


class CommonTestMethodsMixin:

    def _assert_func(self, func, expected, conf_value):
        self.conf.loadFromString(self.__class__.assert_func_template % conf_value)
        try:
            self.assertEqual(expected, func('section_foo', 'foo'))
        except (configparser.Error, ValueError) as err:
            self.fail("expecting %s, but got %r" % (expected, err))

    def _assert_func_raises(self, func, expected_error, section, name, conf):
        try:
            self.conf.loadFromString(conf)
            func(section, name)
        except expected_error:
            pass
        except Exception as err:
            self.fail("expecting %s, but got %r" % (expected_error, err))
        else:
            self.fail("expecting %s" % expected_error)

    def assert_get(self, expected, conf_value):
        self._assert_func(self.conf.get, expected, conf_value)

    def assert_get_raises(self, expected_error, section, name, conf):
        self._assert_func_raises(self.conf.get, expected_error, section, name, conf)

    def assert_getint(self, expected, conf_value):
        self._assert_func(self.conf.getint, expected, conf_value)

    def assert_getint_raises(self, expected_error, section, name, conf):
        self._assert_func_raises(self.conf.getint, expected_error, section, name, conf)

    def assert_getfloat(self, expected, conf_value):
        self._assert_func(self.conf.getfloat, expected, conf_value)

    def assert_getfloat_raises(self, expected_error, section, name, conf):
        self._assert_func_raises(self.conf.getfloat, expected_error, section, name, conf)

    def assert_getboolean(self, expected, conf_value):
        self._assert_func(self.conf.getboolean, expected, conf_value)

    def assert_getboolean_raises(self, expected_error, section, name, conf):
        self._assert_func_raises(self.conf.getboolean, expected_error, section, name, conf)

    def assert_getDuration(self, expected, conf_value):
        self._assert_func(self.conf.getDuration, expected, conf_value)

    def test_get(self):
        self.assert_get('bar', 'bar')
        self.assert_get('', '')
        self.assert_get_raises(configparser.NoOptionError, 'section_foo', 'bar', self.assert_func_template % "")
        self.assert_get_raises(configparser.NoOptionError, 'section_bar', 'foo', self.assert_func_template % "")

    def test_getint(self):
        self.assert_getint(-54, '-54')
        self.assert_getint(0, '0')
        self.assert_getint(64, '64')
        self.assert_getint_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "bar")
        self.assert_getint_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "64.5")
        self.assert_getint_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "")
        self.assert_getint_raises(configparser.NoOptionError, 'section_foo', 'bar', self.assert_func_template % "")
        self.assert_getint_raises(configparser.NoOptionError, 'section_bar', 'foo', self.assert_func_template % "")

    def test_getfloat(self):
        self.assert_getfloat(-54.0, '-54')
        self.assert_getfloat(-54.6, '-54.6')
        self.assert_getfloat(0.0, '0')
        self.assert_getfloat(0.0, '0.0')
        self.assert_getfloat(64.0, '64')
        self.assert_getfloat(64.45, '64.45')
        self.assert_getfloat_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "bar")
        self.assert_getfloat_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "64,5")
        self.assert_getfloat_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "")
        self.assert_getfloat_raises(configparser.NoOptionError, 'section_foo', 'bar', self.assert_func_template % "")
        self.assert_getfloat_raises(configparser.NoOptionError, 'section_bar', 'foo', self.assert_func_template % "")

    def test_getboolean(self):
        self.assert_getboolean(False, 'false')
        self.assert_getboolean(False, '0')
        self.assert_getboolean(False, 'off')
        self.assert_getboolean(False, 'OFF')
        self.assert_getboolean(False, 'no')
        self.assert_getboolean(False, 'NO')
        self.assert_getboolean(True, 'true')
        self.assert_getboolean(True, '1')
        self.assert_getboolean(True, 'on')
        self.assert_getboolean(True, 'ON')
        self.assert_getboolean(True, 'yes')
        self.assert_getboolean(True, 'YES')
        self.assert_getboolean_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "bar")
        self.assert_getboolean_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "64,5")
        self.assert_getboolean_raises(ValueError, 'section_foo', 'foo', self.assert_func_template % "")
        self.assert_getboolean_raises(configparser.NoOptionError, 'section_foo', 'bar', self.assert_func_template % "")
        self.assert_getboolean_raises(configparser.NoOptionError, 'section_bar', 'foo', self.assert_func_template % "")

    def test_getDuration(self):
        self.assert_getDuration(0, '0')
        self.assert_getDuration(50, '50')
        self.assert_getDuration(24*60, '24h')
        self.assert_getDuration(0.5, '30s')


class Test_XmlConfigParser(CommonTestMethodsMixin, B3TestCase):

    assert_func_template = """
        <configuration>
            <settings name="section_foo">
                <set name="foo">%s</set>
            </settings>
        </configuration>"""

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = XmlConfigParser()
        self.conf.loadFromString("""<configuration/>""")
        log = logging.getLogger('output')
        log.setLevel(logging.DEBUG)

    def test_get_missing(self):
        self.assert_get_raises(configparser.NoOptionError, 'section_foo', 'bar', """<configuration><settings name="section_foo"><set name="foo"/></settings></configuration>""")
        self.assert_get_raises(configparser.NoOptionError, 'section_bar', 'foo', """<configuration><settings name="section_foo"><set name="foo"/></settings></configuration>""")


class Test_ConfigFileNotValid(TestCase):

    def test_exception_message(self):
        try:
            raise ConfigFileNotValid("f00")
        except ConfigFileNotValid as e:
            self.assertEqual(repr("f00"), str(e))

    def test_loading_invalid_conf(self):
        config = XmlConfigParser()
        try:
            config.loadFromString(r"""<configuration """)
        except ConfigFileNotValid as e:
            self.assertEqual("'unclosed token: line 1, column 0'", str(e))
        except Exception as e:
            self.fail("unexpected exception %r" % e)
        else:
            self.fail("expecting exception")


class Test_CfgConfigParser(CommonTestMethodsMixin, B3TestCase):

    assert_func_template = """
[section_foo]
foo = %s
"""

    def setUp(self):
        B3TestCase.setUp(self)
        self.conf = CfgConfigParser()
        self.conf.loadFromString("[foo]")
        log = logging.getLogger('output')
        log.setLevel(logging.DEBUG)


if __name__ == '__main__':
    unittest.main()


class Test_config_file_encoding(unittest.TestCase):
    """config files are UTF-8, not the machine locale encoding"""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, 'b3.ini')

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, text):
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(text)

    def test_cfg_load_reads_utf8(self):
        self._write('[b3]\nbot_name: Ünknown\n')
        conf = CfgConfigParser()
        conf.load(self.path)
        self.assertEqual('Ünknown', conf.get('b3', 'bot_name'))

    def test_cfg_save_round_trips_utf8(self):
        self._write('[b3]\nbot_name: Ünknown\n')
        conf = CfgConfigParser()
        conf.load(self.path)
        conf.save()
        again = CfgConfigParser()
        again.load(self.path)
        self.assertEqual('Ünknown', again.get('b3', 'bot_name'))

    def test_xml_load_reads_utf8(self):
        self._write('<?xml version="1.0" encoding="utf-8"?>'
                    '<configuration><settings name="b3"><set name="bot_name">Ünknown</set>'
                    '</settings></configuration>')
        conf = XmlConfigParser()
        conf.load(self.path)
        self.assertEqual('Ünknown', conf.get('b3', 'bot_name'))

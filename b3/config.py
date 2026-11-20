
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

__author__  = 'ThorN, Courgette, Fenix'
__version__ = '1.7.9'

import os
import re
import time
import b3
import b3.functions
import b3.exceptions
import b3.storage
import configparser


ConfigFileNotFound = b3.exceptions.ConfigFileNotFound
ConfigFileNotValid = b3.exceptions.ConfigFileNotValid
NoOptionError = b3.exceptions.NoOptionError
NoSectionError = b3.exceptions.NoSectionError

# list of plugins that cannot be loaded as disabled from configuration file
MUST_HAVE_PLUGINS = ('admin', 'publist', 'ftpytail', 'sftpytail', 'httpytail')

class B3ConfigParserMixin(object):
    """
    Mixin implementing ConfigParser methods more useful for B3 business.
    """
    def get(self, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        raise NotImplementedError

    def getboolean(self, section, setting):
        """
        Return a configuration value as a boolean.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value_raw = self.get(section, setting)
        value = value_raw.lower() if value_raw else ''
        if value in ('yes', '1', 'on', 'true'):
            return True
        elif value in ('no', '0', 'off', 'false'):
            return False
        else:
            raise ValueError("%s.%s : '%s' is not a boolean value" % (section, setting, value))

    def getDuration(self, section, setting=None):
        """
        Return a configuration value parsing the duration time
        notation and converting the value into minutes.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        value = self.get(section, setting).strip()
        return b3.functions.time2minutes(value)

    def getpath(self, section, setting):
        """
        Return an absolute path name and expand the user prefix (~).
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        """
        return b3.getAbsolutePath(self.get(section, setting), decode=True)

    def getTextTemplate(self, section, setting=None, **kwargs):
        """
        Return a text template from the configuration file: will
        substitute all the tokens with the given kwargs.
        :param section: The configuration file section.
        :param setting: The configuration file setting.
        :param kwargs: A dict with variables used for string substitution.
        """
        value = b3.functions.vars2printf(self.get(section, setting, raw=True)).strip()
        if len(kwargs):
            return value % kwargs
        return value


class CfgConfigParser(B3ConfigParserMixin, configparser.ConfigParser):
    """
    A config parser class that mimics the ConfigParser, reads the cfg format.
    """
    fileName = ''
    fileMtime = 0

    def __init__(self, allow_no_value=False):
        """
        Object constructor.
        :param allow_no_value: Whether or not to allow empty values in configuration sections
        """
        # strict=False keeps the python2 behavior of tolerating duplicated
        # options/sections in .ini files (last one wins) instead of raising
        # interpolation=None keeps the python2 behavior of passing raw '%'
        # characters through (b3 configs are full of printf-style templates)
        # inline_comment_prefixes keeps the python2 behavior of stripping a
        # ';' comment placed after a value (python3 disables it by default)
        configparser.ConfigParser.__init__(self, allow_no_value=allow_no_value, strict=False,
                                            interpolation=None, inline_comment_prefixes=(';',))

    def add_comment(self, section, comment):
        """
        Add a comment
        :param section: The section where to place the comment
        :param comment: The comment to add
        """
        if not section or section == "DEFAULT":
            sectdict = self._defaults
        else:
            try:
                sectdict = self._sections[section]
            except KeyError:
                raise configparser.NoSectionError(section)
        sectdict['; %s' % (comment,)] = None

    def get(self, section, option, *args, **kwargs):
        """
        Return a configuration value as a string.
        """
        try:
            value = configparser.ConfigParser.get(self, section, option, *args, **kwargs)
            if value is None:
                return ""
            return value
        except configparser.NoSectionError:
            # plugins are used to only catch NoOptionError
            raise configparser.NoOptionError(option, section)

    def load(self, filename):
        """
        Load a configuration file.
        """
        f = open(filename, 'r', encoding='utf-8', errors='surrogateescape')
        self.readfp(f)
        f.close()
        self.fileName = filename
        self.fileMtime = os.path.getmtime(self.fileName)
        return True

    def loadFromString(self, cfg_string):
        """
        Read the cfg config from a string.
        """
        import io
        fp = io.StringIO(cfg_string)
        self.readfp(fp)
        fp.close()
        self.fileName = None
        self.fileMtime = time.time()
        return True

    def readfp(self, fp, filename=None):
        """
        Inherits from ConfigParser.ConfigParser to throw our custom exception if needed
        """
        try:
            # readfp was removed from configparser in python 3.12: read_file is the py3 API
            configparser.ConfigParser.read_file(self, fp, filename)
        except Exception as e:
            raise ConfigFileNotValid("%s" % e)

    def save(self):
        """
        Save the configuration file.
        """
        f = open(self.fileName, 'w', encoding='utf-8', errors='surrogateescape')
        self.write(f)
        f.close()
        return True

    def write(self, fp):
        """
        Write an .ini-format representation of the configuration state.
        """
        if self._defaults:
            fp.write("[%s]\n" % configparser.DEFAULTSECT)
            for (key, value) in list(self._defaults.items()):
                self._write_item(fp, key, value)
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in list(self._sections[section].items()):
                self._write_item(fp, key, value)
            fp.write("\n")

    @staticmethod
    def _write_item(fp, key, value):
        if (key.startswith(';') or key.startswith('#')) and value is None:
            # consider multiline comments
            for line in key.split('\n'):
                line = b3.functions.left_cut(line, ';')
                line = b3.functions.left_cut(line, '#')
                fp.write("; %s\n" % (line.strip(),))
        else:
            if value is not None and str(value).strip() != '':
                fp.write("%s: %s\n" % (key, str(value).replace('\n', '\n\t')))
            else:
                fp.write("%s: \n" % key)

def load(filename):
    """
    Load an INI configuration file.
    """
    # allow the use of empty keys to support the b3.ini configuration file
    config = CfgConfigParser(allow_no_value=True)
    filename = b3.getAbsolutePath(filename, True)
    return config if config.load(filename) else None


class MainConfig(B3ConfigParserMixin):
    """
    Class to use to parse the B3 main config file.
    """
    def __init__(self, config_parser):
        if not isinstance(config_parser, CfgConfigParser):
            raise NotImplementedError("unexpected config type: %r" % config_parser.__class__)
        self._config_parser = config_parser
        self._plugins = []
        self._init_plugins_from_cfg()

    def _init_plugins_from_cfg(self):
        ## Load the list of disabled plugins
        try:
            disabled_plugins_raw = self._config_parser.get('b3', 'disabled_plugins')
        except configparser.NoOptionError:
            disabled_plugins = []
        else:
            disabled_plugins = re.split(r'\W+', disabled_plugins_raw.lower())

        def get_custom_plugin_path(plugin_name):
            try:
                return self._config_parser.get('plugins_custom_path', plugin_name)
            except configparser.NoOptionError:
                return None

        self._plugins = []
        if self._config_parser.has_section('plugins'):
            for name in self._config_parser.options('plugins'):
                self._plugins.append({
                    'name': name,
                    'conf': self._config_parser.get('plugins', name),
                    'path': get_custom_plugin_path(name),
                    'disabled': name.lower() in disabled_plugins and name.lower() not in MUST_HAVE_PLUGINS
                })

    def get_plugins(self):
        """
        :return: list[dict] A list of plugin settings as a dict.
            I.E.:
            [
                {'name': 'admin', 'conf': @conf/plugin_admin.ini, 'path': None, 'disabled': False},
                {'name': 'adv', 'conf': @conf/plugin_adv.ini, 'path': None, 'disabled': False},
            ]
        """
        return self._plugins

    def get_external_plugins_dir(self):
        """
        the directory path (as a string) where additional plugin modules can be found
        :return: str or ConfigParser.NoOptionError
        """
        return self._config_parser.getpath("b3", "external_plugins_dir")

    def get(self, *args, **kwargs):
        """
        Override the get method defined in the B3ConfigParserMixin
        """
        return self._config_parser.get(*args, **kwargs)

    def analyze(self):
        """
        Analyze the main configuration file checking for common mistakes.
        This will mostly check configuration file values and will not perform any futher check related,
        i.e: connection with the database can be established using the provided dsn, rcon password is valid etc.
        Such validations needs to be handled somewhere else.
        :return: A list of strings highlighting problems found (so they can be logged/displayed easily)
        """
        analysis = []

        def _mandatory_option(section, option):
            if not self.has_option(section, option):
                analysis.append('missing configuration value %s::%s' % (section, option))

        _mandatory_option('b3', 'parser')
        _mandatory_option('b3', 'database')
        _mandatory_option('b3', 'bot_name')

        ## PARSER CHECK
        if self.has_option('b3', 'parser'):
            try:
                b3.functions.getModule('b3.parsers.%s' % self.get('b3', 'parser'))
            except ImportError as err:
                analysis.append('invalid parser specified in b3::parser (%s): %s'
                                % (self.get('b3', 'parser'), err))

        ## DSN DICT
        if self.has_option('b3', 'database'):
            dsndict = b3.functions.splitDSN(self.get('b3', 'database'))
            if not dsndict:
                analysis.append('invalid database source name specified in b3::database (%s)' % self.get('b3', 'database'))
            elif dsndict['protocol'] not in b3.storage.PROTOCOLS:
                analysis.append('invalid storage protocol specified in b3::database (%s) : '
                                'valid protocols are : %s' % (dsndict['protocol'], ', '.join(b3.storage.PROTOCOLS)))

        ## ADMIN PLUGIN CHECK
        has_admin = False
        has_admin_config = False
        for plugin in self.get_plugins():
            if plugin['name'] == 'admin':
                has_admin = True
                if plugin['conf']:
                    has_admin_config = True
                break

        if not has_admin:
            analysis.append('missing admin plugin in plugins section')
        elif not has_admin_config:
            analysis.append('missing configuration file for admin plugin')

        return analysis

    def __getattr__(self, name):
        """
        Act as a proxy in front of self._config_parser.
        Any attribute or method call which does not exists in this
        object (MainConfig) is then tried on the self._config_parser
        :param name: str Attribute or method name
        """
        if hasattr(self._config_parser, name):
            attr = getattr(self._config_parser, name)
            if hasattr(attr, '__call__'):
                def newfunc(*args, **kwargs):
                    return attr(*args, **kwargs)
                return newfunc
            else:
                return attr
        else:
            raise AttributeError(name)


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
import xml.etree.ElementTree as ET

from b3.config import CfgConfigParser
from b3.exceptions import ConfigFileNotValid


def _add_penalty(lines, node):
    if node is None:
        return
    if node.get('type'):
        lines.append('penalty: %s' % node.get('type'))
    if node.get('reason'):
        lines.append('reason: %s' % node.get('reason'))
    if node.get('reasonkeyword'):
        lines.append('reason_keyword: %s' % node.get('reasonkeyword'))
    if node.get('duration'):
        lines.append('duration: %s' % node.get('duration'))


def xml_to_ini(xml):
    """Convert the legacy test XML config to the INI format the code reads now."""
    try:
        root = ET.fromstring(xml)
    except Exception as e:
        raise ConfigFileNotValid(str(e))

    lines = []
    for settings in root.findall('./settings'):
        section = settings.get('name')
        items = settings.findall('./set')
        if section == 'plugins' and items and items[0].get('name') == 'external_dir':
            # XML kept this under [plugins], INI keeps it under [b3]
            lines.append('[b3]')
            lines.append('external_plugins_dir: %s' % (items[0].text or '').strip())
            lines.append('')
            continue
        lines.append('[%s]' % section)
        for item in items:
            lines.append('%s: %s' % (item.get('name'), (item.text or '').strip()))
        lines.append('')

    plugins = root.findall('./plugins/plugin')
    if plugins:
        lines.append('[plugins]')
        custom = []
        disabled = []
        for plugin in plugins:
            name = plugin.get('name')
            conf = plugin.get('config')
            if not conf:
                continue
            lines.append('%s: %s' % (name, conf))
            if plugin.get('path'):
                custom.append('%s: %s' % (name, plugin.get('path')))
            if plugin.get('disabled', '').lower() in ('yes', '1', 'on', 'true'):
                disabled.append(name)
        lines.append('')
        if custom:
            lines.append('[plugins_custom_path]')
            lines.extend(custom)
            lines.append('')
        if disabled:
            lines.append('[b3]')
            lines.append('disabled_plugins: %s' % ', '.join(disabled))
            lines.append('')

    ads = root.findall('./ads/ad')
    if ads:
        lines.append('[ads]')
        for i, ad in enumerate(ads, 1):
            lines.append('%s: %s' % (i, (ad.text or '').strip()))
        lines.append('')

    for parent_tag, prefix in (('badwords', 'badword'), ('badnames', 'badname')):
        parent = root.find('./%s' % parent_tag)
        if parent is None:
            continue
        lines.append('[%s]' % parent_tag)
        _add_penalty(lines, parent.find('penalty'))
        lines.append('')
        for rule in parent.findall(prefix):
            lines.append('[%s:%s]' % (prefix, rule.get('name')))
            if rule.get('lang'):
                lines.append('lang: %s' % rule.get('lang'))
            _add_penalty(lines, rule.find('penalty'))
            word = rule.find('word')
            regexp = rule.find('regexp')
            if word is not None:
                lines.append('word: %s' % (word.text or '').strip())
            if regexp is not None:
                lines.append('regexp: %s' % (regexp.text or '').strip())
            lines.append('')

    for tag in ('ip_banlist', 'guid_banlist', 'pbid_banlist', 'rules_of_combat',
                'ip_whitelist', 'guid_whitelist', 'pbid_whitelist'):
        for item in root.findall('./%s' % tag):
            name = item.findtext('name') or tag
            lines.append('[%s:%s]' % (tag, name))
            for field in ('name', 'file', 'force_ip_range', 'message', 'url'):
                value = item.findtext(field)
                if value and value.strip():
                    lines.append('%s: %s' % (field, value.strip()))
            lines.append('')

    used = set()
    for task_type in ('restart', 'cron', 'hourly', 'daily'):
        for task in root.findall('./%s' % task_type):
            name = task.get('name') or task_type
            section = name
            i = 2
            while section in used:
                section = '%s-%s' % (name, i)
                i += 1
            used.add(section)
            lines.append('[task:%s]' % section)
            lines.append('type: %s' % task_type)
            if section != name:
                lines.append('name: %s' % name)
            for attr in ('seconds', 'minutes', 'hour', 'day', 'month', 'dow', 'delay'):
                if task.get(attr):
                    lines.append('%s: %s' % (attr, task.get(attr)))
            for action in ('rcon', 'frostbite', 'bfbc2', 'enable_plugin', 'disable_plugin'):
                for i, node in enumerate(task.findall(action), 1):
                    if action == 'rcon':
                        value = (node.text or '').strip()
                    elif action in ('frostbite', 'bfbc2'):
                        value = node.get('command') or ''
                        for arg in node.findall('arg'):
                            value += ' %s' % (arg.text or '').strip()
                    else:
                        value = node.get('plugin') or ''
                    lines.append('%s%s: %s' % (action, i, value.strip()))
            lines.append('')

    return "\n".join(lines)


# shortcut: the test fixtures still hold XML literals; this shim converts
# them to INI at test time. Convert each fixture to an INI literal and delete
# this module, then the test suite has no XML dependency either.
class XmlConfigParser(CfgConfigParser):
    """Test-only compatibility shim: XML input is converted to INI before loading."""

    def setXml(self, xml):
        self.loadFromString(xml)

    def loadFromString(self, xml):
        super(XmlConfigParser, self).loadFromString(xml_to_ini(xml))

    def load(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            self.loadFromString(f.read())
        self.fileName = filename
        self.fileMtime = os.path.getmtime(filename)
        return True

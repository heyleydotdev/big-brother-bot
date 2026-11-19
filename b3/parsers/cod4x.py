
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

# CHANGELOG:
#           0.1 - Initial release
#           0.2 - Added support for B3Hide plugin, force ID64
#           0.3 - Add player status methods
#           0.4 - Correct status parsing regexes
#           0.5 - Rebuilt _regPlayer against the actual SV_Status_f() engine
#                 source (non-legacy mode only, legacy mode retired). Fixes:
#                   - map line never matched (padded "map     :" vs "map:")
#                   - getMap() only checked the first status line
#                   - lastmsg value leaking into the parsed name
#                   - steamid column not separated from guid/name
#                   - trailing "^7" color-reset now stripped from name
#                   - dropped _regPlayerShort; getPlayerPings()/getPlayerScores()
#                     now match with _regPlayer directly (the short variant
#                     added no real value and risked falling back to the
#                     broken base-class regex if ever left undefined)
#           0.6 - B3 2.x port:
#                   - startup() keeps the cod parser initialisation (world
#                     client, punkbuster probe, map name, g_logsync, event
#                     map) before forcing sv_usesteam64id
#                   - use compiled pattern .match()
#                   - drop the copies of getPlayerList/getPlayerPings/
#                     getPlayerScores, the base ones use _regPlayer
#                   - fix the KeyError in the tempban-by-cid branch
#                     (getCommand('tempban') needs a duration)

__author__ = 'Leiizko, heyleydotdev'
__version__ = '0.6'


import b3.clients
import b3.functions
import b3.parsers.cod4
import re


class Cod4XParser(b3.parsers.cod4.Cod4Parser):
    gameName = 'cod4'
    IpsOnly = False

    # CoD4x reports the 64 bit steam id as guid, do not reject shorter values
    _guidLength = 0

    _reMapNameFromStatus = re.compile(r'^map\s*:\s*(?P<map>.+)$', re.IGNORECASE)

    # non-legacy status row:
    # num score ping playerid steamid name lastmsg address qport rate
    _regPlayer = re.compile(
        r'^\s*(?P<slot>[0-9]+)\s+'
        r'(?P<score>[0-9-]+)\s+'
        r'(?P<ping>[0-9]+)\s+'
        r'(?P<guid>[0-9]+)\s+'
        r'(?P<steam>[0-9]+)\s+'
        r'(?P<name>.*?)(?:\^7)?\s+'
        r'(?P<last>[0-9]+)\s+'
        r'(?P<ip>(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])):?'
        r'(?P<port>-?[0-9]{1,5})\s*'
        r'(?P<qport>-?[0-9]{1,5})\s+'
        r'(?P<rate>[0-9]+)$',
        re.IGNORECASE
    )

    # the base class status methods try this loose regex before _regPlayer:
    # make the only attempt the correct one
    _regPlayerShort = _regPlayer

    _commands = {
        'message': 'tell %(cid)s %(message)s',
        'say': 'say %(message)s',
        'set': 'set %(name)s "%(value)s"',
        'kick': 'kick %(cid)s %(reason)s ',
        'ban': 'permban %(cid)s %(reason)s ',
        'unban': 'unban %(guid)s',
        'tempban': 'tempban %(cid)s %(duration)sm %(reason)s',
        'kickbyfullname': 'kick %(cid)s'
    }

    def startup(self):
        """
        Called after the parser is created before run().
        """
        super().startup()
        # the status rows below are parsed as 64 bit ids, keep the server on it
        self.write('sv_usesteam64id  1', maxRetries=3)

    def unban(self, client, reason='', admin=None, silent=False, *kwargs):
        """
        Unban a client.
        :param client: The client to unban
        :param reason: The reason for the unban
        :param admin: The admin who unbanned this client
        :param silent: Whether or not to announce this unban
        """
        result = self.write(self.getCommand('unban', guid=client.guid))

        if admin:
            admin.message(result)

    def tempban(self, client, reason='', duration=2, admin=None, silent=False, *kwargs):
        """
        Tempban a client.
        :param client: The client to tempban
        :param reason: The reason for this tempban
        :param duration: The duration of the tempban
        :param admin: The admin who performed the tempban
        :param silent: Whether or not to announce the tempban
        """
        duration = b3.functions.time2minutes(duration)

        if isinstance(client, b3.clients.Client) and not client.guid:
            # client has no guid, kick instead
            return self.kick(client, reason, admin, silent)

        elif isinstance(client, str) and re.match('^[0-9]+$', client):
            self.write(
                self.getCommand('tempban', cid=client, reason=reason, duration=duration)
            )
            return

        elif admin:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(
                client=client,
                reason=reason,
                admin=admin,
                banduration=banduration
            )
            fullreason = self.getMessage('temp_banned_by', variables)

        else:
            banduration = b3.functions.minutesStr(duration)
            variables = self.getMessageVariables(
                client=client,
                reason=reason,
                banduration=banduration
            )
            fullreason = self.getMessage('temp_banned', variables)

        duration = 43200 if int(duration) > 43200 else int(duration)

        self.write(
            self.getCommand(
                'tempban',
                cid=client.cid,
                reason=reason,
                duration=duration
            )
        )

        if not silent and fullreason != '':
            self.say(fullreason)

        self.queueEvent(
            self.getEvent(
                'EVT_CLIENT_BAN_TEMP',
                {
                    'reason': reason,
                    'duration': duration,
                    'admin': admin
                },
                client
            )
        )

        client.disconnect()

    def getMap(self):
        """
        Return the current map/level name.

        CoD4x pads the label ("map     : mp_crash") and the map line is not
        guaranteed to be the first one, so check every line.
        """
        data = self.write('status')
        if not data:
            return None

        for line in data.split('\n'):
            m = self._reMapNameFromStatus.match(line.strip())
            if m:
                return str(m.group('map'))

        return None

# -*- coding: utf-8 -*-

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

__author__ = 'Fenix, heyleydotdev'
__version__ = '1.6'

import b3
import b3.clients
import b3.plugin
import b3.events
import threading
import time

from .exceptions import GeolocalizationError
from .geolocators import FreeIpApiGeolocator
from .geolocators import IpApiGeolocator
from .geolocators import IpWhoIsGeolocator
from .geolocators import MaxMindGeolocator


class GeolocationPlugin(b3.plugin.Plugin):

    requiresConfigFile = False

    _cache_ttl = 86400  # number of seconds a Location object is kept in the cache

    def __init__(self, console, config=None):
        """
        Build the plugin object.
        """
        b3.plugin.Plugin.__init__(self, console, config)
        # create geolocators instances
        self.info('creating geolocators object instances...')
        self._geolocators = [IpApiGeolocator(), IpWhoIsGeolocator(), FreeIpApiGeolocator()]
        try:
            # append this one separately since db may be missing
            self._geolocators.append(MaxMindGeolocator())
        except IOError, e:
            self.debug('MaxMind geolocation not available: %s' % e)
        # cache of already retrieved geolocation data: {ip address string: (timestamp, Location)}
        self._cache_lock = threading.Lock()
        self._cache = {}
        # client ids for which a geolocation task is currently running
        self._in_progress = set()

    def onStartup(self):
        """
        Initialize plugin.
        """
        # register events needed
        if self.console.isFrostbiteGame():
            self.registerEvent('EVT_PUNKBUSTER_NEW_CONNECTION', self.geolocate)
        else:
            self.registerEvent('EVT_CLIENT_AUTH', self.geolocate)

        self.registerEvent('EVT_CLIENT_UPDATE', self.geolocate)

        # create our custom events so other plugins can react when clients are geolocated
        self.console.createEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', 'Event client geolocation success')
        self.console.createEvent('EVT_CLIENT_GEOLOCATION_FAILURE', 'Event client geolocation failure')

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def geolocate(self, event):
        """
        Handle EVT_CLIENT_AUTH and EVT_CLIENT_UPDATE.
        """
        client = event.client
        ip = getattr(client, 'ip', None)

        # make sure to launch geolocation only if we have a valid ip address
        if not ip:
            return

        # do not use hasattr or try except here: we'd better try to get geodata also when a previous attempt failed
        # and we ended up with NoneType object in client.location (so we have an attribute but it's not useful)
        if getattr(client, 'location', None):
            return

        client_id = getattr(client, 'id', None)

        with self._cache_lock:
            cached = self._cache.get(ip, None)
            if cached is not None:
                timestamp, location = cached
                if time.time() - timestamp <= self._cache_ttl:
                    self.debug('using cached geolocation data for %s <@%s>', client.name, client.id)
                    client.location = location
                    self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=client))
                    return
                del self._cache[ip]

            if client_id in self._in_progress:
                self.debug('geolocation of %s <@%s> is already in progress: skipping', client.name, client_id)
                return

            self._in_progress.add(client_id)

        t = threading.Thread(target=self._geolocate_worker, args=(client, ip, client_id))
        t.daemon = True  # won't prevent B3 from exiting
        t.start()

    ####################################################################################################################
    #                                                                                                                  #
    #   OTHER METHODS                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def _geolocate_worker(self, client, ip, client_id):
        """
        Retrieve geolocation data from the geolocators and fire the proper event.
        :param client: The client object to geolocate
        :param ip: The ip address string to geolocate
        :param client_id: The id of the client object to geolocate
        """
        try:
            location = None

            for geotool in self._geolocators:

                try:
                    self.debug('retrieving geolocation data for %s <@%s>...', client.name, client.id)
                    location = geotool.getLocation(client)
                    self.debug('retrieved geolocation data for %s <@%s>: %r', client.name, client.id, location)
                    break # stop iterating if we collect valid data
                except GeolocalizationError, e:
                    self.warning('could not retrieve geolocation data %s <@%s>: %s', client.name, client.id, e)
                except Exception, e:
                    self.error('client %s <@%s> geolocation terminated unexpectedtly when using %s service: %s',
                               client.name, client.id, geotool.__class__.__name__, e)

            if location is not None:
                with self._cache_lock:
                    self._cache_prune()
                    self._cache[ip] = (time.time(), location)
                client.location = location
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_SUCCESS', client=client))
            else:
                client.location = None
                self.console.queueEvent(self.console.getEvent('EVT_CLIENT_GEOLOCATION_FAILURE', client=client))

        finally:
            with self._cache_lock:
                self._in_progress.discard(client_id)

    def _cache_prune(self):
        """
        Remove expired entries from the cache. Must be called while holding the cache lock.
        """
        now = time.time()
        expired = [ip for ip, (timestamp, _) in self._cache.items() if now - timestamp > self._cache_ttl]
        for ip in expired:
            del self._cache[ip]
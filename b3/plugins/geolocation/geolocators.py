
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
import b3.clients
import ipaddress
import maxminddb
import os
import os.path
import requests

from .exceptions import GeolocalizationError, InvalidDatabaseError
from .location import Location


class Geolocator(object):

    _timeout = 5

    def __init__(self, *args, **kwargs):
        """
        Object constructor.
        """
        pass

    @staticmethod
    def _getIp(data):
        """
        Extract ip information from the given data
        :param data: The data from where to extract the ip address
        :raise TypeError: if we receive an invalid input data
        :return: string
        """
        if isinstance(data, str):
            ip = data
        elif isinstance(data, b3.clients.Client):
            ip = data.ip
            if not ip:
                raise GeolocalizationError('b3.clients.Client object instance has not ip attribute set')
        else:
            raise GeolocalizationError('invalid argument supplied: %s' % type(data).__name__)

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise GeolocalizationError('invalid ip address supplied: %s' % ip)

        if '%' in ip:  # zone id: no database nor http service can use it
            raise GeolocalizationError('scoped ip address not supported: %s' % ip)

        return ip

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise RequestException: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        raise NotImplementedError


class IpApiGeolocator(Geolocator):

    _url = 'http://ip-api.com/json/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rt = requests.get(self._url % ip, timeout=self._timeout).json()

        if rt['status'] == 'fail':
            raise GeolocalizationError('invalid data returned by the api: %r' % rt)

        return Location(country=rt.get('country', None), region=rt.get('regionName', None), city=rt.get('city', None),
                        cc=rt.get('countryCode', None), rc=rt.get('regionCode', None), isp=rt.get('isp', None),
                        lat=rt.get('lat', None), lon=rt.get('lon', None), timezone=rt.get('timezone', None),
                        zipcode=rt.get('zip', None))


class IpWhoIsGeolocator(Geolocator):

    _url = 'https://ipwho.is/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rt = requests.get(self._url % ip, timeout=self._timeout).json()

        if not rt.get('success', False):
            raise GeolocalizationError('could not geolocate ip %s: %s' % (ip, rt.get('message', 'unknown error')))

        connection = rt.get('connection') or {}
        timezone = rt.get('timezone') or {}

        return Location(country=rt.get('country', None), region=rt.get('region', None), city=rt.get('city', None),
                        cc=rt.get('country_code', None), rc=rt.get('region_code', None),
                        isp=connection.get('isp', None), lat=rt.get('latitude', None),
                        lon=rt.get('longitude', None), timezone=timezone.get('id', None),
                        zipcode=rt.get('postal', None))


class FreeIpApiGeolocator(Geolocator):

    _url = 'https://freeipapi.com/api/json/%s'

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        rt = requests.get(self._url % ip, timeout=self._timeout).json()

        if 'countryName' not in rt:
            raise GeolocalizationError('could not establish in which country is ip %s' % ip)

        return Location(country=rt.get('countryName', None), region=rt.get('regionName', None),
                        city=rt.get('cityName', None), cc=rt.get('countryCode', None),
                        lat=rt.get('latitude', None), lon=rt.get('longitude', None),
                        timezone=rt.get('timeZone', None), zipcode=rt.get('zipCode', None))


class MaxMindGeolocator(Geolocator):
    """
    Geolocate through a MaxMind DB (MMDB) file: DB-IP Lite or GeoLite2 Country
    share the same schema, so either file works.
    """

    # City editions first: they also hold city, region and coordinates
    _db_names = ('dbip-city-lite.mmdb', 'dbip-country-lite.mmdb',
                 'GeoLite2-City.mmdb', 'GeoLite2-Country.mmdb')
    # the retired MaxMind GeoIP Legacy format, only used to warn about it
    _legacy_paths = ('/usr/local/share/GeoIP/GeoIP.dat', '/usr/share/GeoIP/GeoIP.dat')
    _db_dirs = (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'),
        '/usr/local/share/GeoIP',
        '/usr/share/GeoIP',
    )

    def __init__(self, *args, **kwargs):
        """
        Object constructor.
        :raise IOError: if the database is not available
        """
        super(MaxMindGeolocator, self).__init__(*args, **kwargs)
        for directory in self._db_dirs:
            for name in self._db_names:
                path = os.path.join(directory, name)
                if not os.path.isfile(path):
                    continue
                try:
                    self._db = maxminddb.open_database(path)
                except (OSError, maxminddb.InvalidDatabaseError) as e:
                    raise InvalidDatabaseError('invalid MaxMind DB file %s: %s' % (path, e))
                return
        raise IOError('no MaxMind DB file found: put %s in %s'
                      % (self._db_names[0], self._db_dirs[0]))

    def getLocation(self, data):
        """
        Retrieve location data
        :param data: A B3 client object or an IP string
        :raise GeolocalizationError: When we are not able to retrieve location information
        :return: A Location object initialized with location data
        """
        ip = self._getIp(data)
        record = self._db.get(ip) or {}
        country = record.get('country') or {}
        cc = country.get('iso_code')
        name = (country.get('names') or {}).get('en')
        if not cc and not name:
            raise GeolocalizationError('no country data for ip %s' % ip)
        # Country editions stop here, City editions also fill the fields of the location plugin
        subdivisions = record.get('subdivisions') or []
        region = subdivisions[0] if subdivisions else {}
        location = record.get('location') or {}
        return Location(
            country=name,
            cc=cc,
            city=((record.get('city') or {}).get('names') or {}).get('en'),
            region=(region.get('names') or {}).get('en'),
            rc=region.get('iso_code'),
            lat=location.get('latitude'),
            lon=location.get('longitude'),
            timezone=location.get('time_zone'),
            zipcode=(record.get('postal') or {}).get('code'),
        )

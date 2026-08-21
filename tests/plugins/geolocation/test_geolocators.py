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

import unittest

from mock import Mock, patch
from b3.clients import Client
from b3.plugins.geolocation.exceptions import GeolocalizationError
from b3.plugins.geolocation.geolocators import FreeIpApiGeolocator
from b3.plugins.geolocation.geolocators import Geolocator
from b3.plugins.geolocation.geolocators import IpApiGeolocator
from b3.plugins.geolocation.geolocators import IpWhoIsGeolocator


def mock_response(json_data):
    """
    Build a mocked requests response object.
    :param json_data: The value returned by the response json() method
    :return: Mock
    """
    response = Mock()
    response.json.return_value = json_data
    return response


class Test_getIp(unittest.TestCase):

    def test_valid_ip_string(self):
        self.assertEqual('94.32.34.35', Geolocator._getIp('94.32.34.35'))

    def test_invalid_ip_string(self):
        self.assertRaises(GeolocalizationError, Geolocator._getIp, 'not an ip address')
        self.assertRaises(GeolocalizationError, Geolocator._getIp, '94.32.34.35junk')
        self.assertRaises(GeolocalizationError, Geolocator._getIp, '94.32.34')

    def test_client_without_ip(self):
        client = Client(console=Mock())
        self.assertRaises(GeolocalizationError, Geolocator._getIp, client)

    def test_client_with_invalid_ip(self):
        client = Client(console=Mock(), ip='invalid')
        self.assertRaises(GeolocalizationError, Geolocator._getIp, client)

    def test_client_with_valid_ip(self):
        client = Client(console=Mock(), ip='94.32.34.35')
        self.assertEqual('94.32.34.35', Geolocator._getIp(client))

    def test_invalid_type(self):
        self.assertRaises(GeolocalizationError, Geolocator._getIp, 123456)


class Test_IpApiGeolocator(unittest.TestCase):

    def setUp(self):
        self.geolocator = IpApiGeolocator()

    def test_getLocation(self):
        # GIVEN
        json_data = {
            'status': 'success',
            'country': 'Italy',
            'regionName': 'Tuscany',
            'city': 'Florence',
            'countryCode': 'IT',
            'regionCode': '52',
            'isp': 'Fastweb',
            'lat': 43.77,
            'lon': 11.25,
            'timezone': 'Europe/Rome',
            'zip': '50100',
        }
        # WHEN
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response(json_data)
            location = self.geolocator.getLocation('94.32.34.35')
        # THEN
        self.assertEqual('Italy', location.country)
        self.assertEqual('Tuscany', location.region)
        self.assertEqual('Florence', location.city)
        self.assertEqual('IT', location.cc)
        self.assertEqual('52', location.rc)
        self.assertEqual('Fastweb', location.isp)
        self.assertEqual('43.77', location.lat)
        self.assertEqual('11.25', location.lon)
        self.assertEqual('Europe/Rome', location.timezone)
        self.assertEqual('50100', location.zipcode)
        get.assert_called_once_with('http://ip-api.com/json/94.32.34.35', timeout=5)

    def test_getLocation_failure(self):
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response({'status': 'fail', 'message': 'reserved range'})
            self.assertRaises(GeolocalizationError, self.geolocator.getLocation, '127.0.0.1')


class Test_IpWhoIsGeolocator(unittest.TestCase):

    def setUp(self):
        self.geolocator = IpWhoIsGeolocator()

    def test_getLocation(self):
        # GIVEN
        json_data = {
            'ip': '94.32.34.35',
            'success': True,
            'country': 'Italy',
            'country_code': 'IT',
            'region': 'Tuscany',
            'region_code': '52',
            'city': 'Florence',
            'latitude': 43.77,
            'longitude': 11.25,
            'postal': '50100',
            'connection': {'asn': 12874, 'org': 'Fastweb', 'isp': 'Fastweb', 'domain': 'fastweb.it'},
            'timezone': {'id': 'Europe/Rome', 'abbr': 'CEST', 'utc': '+02:00'},
        }
        # WHEN
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response(json_data)
            location = self.geolocator.getLocation('94.32.34.35')
        # THEN
        self.assertEqual('Italy', location.country)
        self.assertEqual('Tuscany', location.region)
        self.assertEqual('Florence', location.city)
        self.assertEqual('IT', location.cc)
        self.assertEqual('52', location.rc)
        self.assertEqual('Fastweb', location.isp)
        self.assertEqual('43.77', location.lat)
        self.assertEqual('11.25', location.lon)
        self.assertEqual('Europe/Rome', location.timezone)
        self.assertEqual('50100', location.zipcode)
        get.assert_called_once_with('https://ipwho.is/94.32.34.35', timeout=5)

    def test_getLocation_missing_optional_fields(self):
        # GIVEN: connection and timezone objects are missing from the response
        json_data = {
            'ip': '94.32.34.35',
            'success': True,
            'country': 'Italy',
            'country_code': 'IT',
        }
        # WHEN
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response(json_data)
            location = self.geolocator.getLocation('94.32.34.35')
        # THEN
        self.assertEqual('Italy', location.country)
        self.assertIsNone(location.isp)
        self.assertIsNone(location.timezone)

    def test_getLocation_failure(self):
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response({'ip': '127.0.0.1', 'success': False, 'message': 'Invalid IP address'})
            self.assertRaises(GeolocalizationError, self.geolocator.getLocation, '127.0.0.1')


class Test_FreeIpApiGeolocator(unittest.TestCase):

    def setUp(self):
        self.geolocator = FreeIpApiGeolocator()

    def test_getLocation(self):
        # GIVEN
        json_data = {
            'ipVersion': 4,
            'ipAddress': '94.32.34.35',
            'latitude': 43.77,
            'longitude': 11.25,
            'countryName': 'Italy',
            'countryCode': 'IT',
            'timeZone': 'Europe/Rome',
            'zipCode': '50100',
            'cityName': 'Florence',
            'regionName': 'Tuscany',
        }
        # WHEN
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response(json_data)
            location = self.geolocator.getLocation('94.32.34.35')
        # THEN
        self.assertEqual('Italy', location.country)
        self.assertEqual('Tuscany', location.region)
        self.assertEqual('Florence', location.city)
        self.assertEqual('IT', location.cc)
        self.assertIsNone(location.rc)
        self.assertIsNone(location.isp)
        self.assertEqual('43.77', location.lat)
        self.assertEqual('11.25', location.lon)
        self.assertEqual('Europe/Rome', location.timezone)
        self.assertEqual('50100', location.zipcode)
        get.assert_called_once_with('https://freeipapi.com/api/json/94.32.34.35', timeout=5)

    def test_getLocation_failure(self):
        with patch('b3.plugins.geolocation.geolocators.requests.get') as get:
            get.return_value = mock_response({'message': 'not found'})
            self.assertRaises(GeolocalizationError, self.geolocator.getLocation, '127.0.0.1')

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

import time

from mock import Mock, patch
from b3.events import Event
from b3.plugins.geolocation.location import Location
from tests.plugins.geolocation import GeolocationTestCase

IP_API_RESPONSE = {
    'status': 'success',
    'country': 'United States',
    'regionName': 'Virginia',
    'city': 'Mountain View',
    'countryCode': 'US',
    'regionCode': 'VA',
    'isp': 'Google LLC',
    'lat': 38.123,
    'lon': -122.1,
    'timezone': 'America/New_York',
    'zip': '20100',
}


def wait_for(condition, timeout=5):
    """
    Wait for the given condition to return True.
    :param condition: A callable returning a boolean value
    :param timeout: The maximum number of seconds to wait
    :return: True if the condition was met within the given timeout, False otherwise
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return condition()


class Test_events(GeolocationTestCase):

    def setUp(self):
        GeolocationTestCase.setUp(self)
        # mock requests.get so no real http request is performed: the first geolocator in the
        # chain (IpApiGeolocator) will succeed using the response defined below
        self.get_patcher = patch('b3.plugins.geolocation.geolocators.requests.get')
        self.mocked_get = self.get_patcher.start()
        self.response = Mock()
        self.response.json.return_value = dict(IP_API_RESPONSE)
        self.mocked_get.return_value = self.response
        self.addCleanup(self.get_patcher.stop)

    def test_event_client_geolocation_success(self):
        # GIVEN
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        # THEN
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertIsInstance(self.mike.location, Location)
        self.assertEqual('United States', self.mike.location.country)
        self.assertEqual(1, self.mocked_get.call_count)

    def test_event_client_geolocation_http_failure_falls_back_to_maxmind(self):
        # GIVEN: every http geolocator returns a malformed response
        self.response.json.side_effect = ValueError('no json object could be decoded')
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        # THEN: the MaxMind local database is used as last resort
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertEqual('United States', self.mike.location.country)
        self.assertEqual(3, self.mocked_get.call_count)  # all the http geolocators have been tried

    def test_event_client_geolocation_failure_invalid_ip(self):
        # GIVEN
        self.mike.ip = '--'
        # WHEN
        self.mike.connects("1")
        # THEN
        self.assertTrue(wait_for(lambda: not self.p._in_progress))
        self.assertIsNone(self.mike.location)
        self.assertEqual(0, self.mocked_get.call_count)  # no http request performed

    def test_event_client_geolocation_success_maxmind(self):
        # GIVEN: only the MaxMind geolocator is available (local database, no http request needed)
        self.p._geolocators = [self.p._geolocators[-1]]
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        # THEN
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertIsNotNone(self.mike.location)
        self.assertIsNone(self.mike.location.isp)
        self.assertEqual('United States', self.mike.location.country)
        self.assertEqual(0, self.mocked_get.call_count)

    def test_event_client_geolocation_success_maxmind_using_event_client_update(self):
        # GIVEN
        self.p._geolocators = [self.p._geolocators[-1]]
        self.mike.ip = ''
        self.mike.connects("1")
        # WHEN
        self.mike.ip = '8.8.8.8'
        self.mike.save(self.console)
        # THEN
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertIsInstance(self.mike.location, Location)
        self.assertEqual('United States', self.mike.location.country)

    def test_event_client_geolocation_cached_on_reconnect(self):
        # GIVEN
        self.mike.ip = '8.8.8.8'
        self.mike.connects("1")
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertEqual(1, self.mocked_get.call_count)
        # WHEN
        self.mike.disconnects()
        self.mike.location = None
        self.mike.connects("2")
        # THEN: no new http request is performed and the location is set from the cache
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertEqual(1, self.mocked_get.call_count)
        self.assertEqual('United States', self.mike.location.country)

    def test_event_client_geolocation_concurrent_events_deduplicated(self):
        # GIVEN
        self.mike.ip = '8.8.8.8'
        # WHEN: two events are handled synchronously before the worker thread had a chance to run
        event = Event(self.console.getEventID('EVT_CLIENT_AUTH'), data=self.mike, client=self.mike)
        self.p.geolocate(event)
        self.p.geolocate(event)
        # THEN: only one geolocation task is started
        self.assertTrue(wait_for(lambda: not self.p._in_progress))
        self.assertEqual(1, self.mocked_get.call_count)

    def test_cache_expiry_triggers_new_lookup(self):
        # GIVEN: an expired entry is stored in the cache
        self.p._cache['8.8.8.8'] = (time.time() - self.p._cache_ttl - 10, Location(country='Somewhere'))
        self.mike.ip = '8.8.8.8'
        # WHEN
        self.mike.connects("1")
        # THEN: a new lookup is performed
        self.assertTrue(wait_for(lambda: getattr(self.mike, 'location', None) is not None))
        self.assertEqual(1, self.mocked_get.call_count)
        self.assertEqual('United States', self.mike.location.country)

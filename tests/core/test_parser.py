
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

import logging
import queue
import threading
import time
import unittest
from unittest.mock import patch
from b3.clients import Client
from b3.events import EventsStats, eventManager
from b3.parser import Parser
from tests import assert_dict_contains_subset



class DummyParser(Parser):

    gameName = "dummy"

    def __init__(self):
        pass # skip parent class constructor
        self.log = logging.getLogger("output")


class _EventHandler:
    """Stand-in for a plugin: records the events it is given."""

    def __init__(self):
        self.events = []

    def isEnabled(self):
        return True

    def parseEvent(self, event):
        self.events.append(event)


class Test_handleEvents(unittest.TestCase):
    """
    The production event dispatcher, now shared with the fake console (see
    Test_dispatcher_is_shared). It needs its own test because the queue and the
    thread are not exercised by the synchronous fake path.
    """

    def setUp(self):
        self.parser = DummyParser()
        self.parser.Events = eventManager
        self.parser.working = True
        self.parser.queue = queue.Queue(10)
        self.parser.exiting = threading.Lock()
        self.parser._eventsStats = EventsStats(self.parser)
        self.handler = _EventHandler()
        self.parser._handlers = {self.parser.getEventID('EVT_CLIENT_SAY'): [self.handler]}

    def _queue(self, key, data):
        now = self.parser.time()
        self.parser.queue.put((now, now + 10, self.parser.getEvent(key, data)))

    def test_events_reach_the_handler(self):
        thread = threading.Thread(target=self.parser.handleEvents, daemon=True)
        thread.start()

        self._queue('EVT_CLIENT_SAY', 'hello')

        deadline = time.time() + 3
        while not self.handler.events and time.time() < deadline:
            time.sleep(0.01)

        received = list(self.handler.events)

        self.parser.working = False  # let the loop end after the next event
        self._queue('EVT_CLIENT_SAY', 'goodbye')
        thread.join(3)

        self.assertEqual(1, len(received), "the event never reached the handler")
        self.assertEqual('hello', received[0].data)
        self.assertFalse(thread.is_alive())

    def test_queue_event_does_not_sleep(self):
        # queueEvent used to sleep 1ms per event: a busy server lost commands
        self.parser.queue = queue.Queue(1000)
        event = self.parser.getEvent('EVT_CLIENT_SAY', 'hello')

        with patch('b3.parser.time.sleep') as sleep_mock:
            for _ in range(100):
                self.parser.queueEvent(event)

        self.assertListEqual([], sleep_mock.mock_calls)


class Test_getMessage(unittest.TestCase):

    def setUp(self):
        self.parser = DummyParser()
        self.parser._messages = {}

    def test_unknown_msg__falls_back_on_default(self):
        self.parser._messages = {}
        self.parser._messages_default = {"f00": "lorem ipsum"}
        self.assertEqual("lorem ipsum", self.parser.getMessage("f00"))

    def test_no_parameter(self):
        self.parser._messages['f00'] = "bar"
        self.assertEqual("bar", self.parser.getMessage('f00'))

    def test_with_parameter(self):
        self.parser._messages['f00'] = "bar %s"
        self.assertEqual("bar joe", self.parser.getMessage('f00', 'joe'))

    def test_with_unexpected_parameter(self):
        self.parser._messages['f00'] = "bar"
        self.assertRaises(TypeError, self.parser.getMessage, 'f00', 'joe')

    def test_with_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertEqual("bar joe", self.parser.getMessage('f00', {'p1': 'joe'}))

    def test_with_missing_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertRaises(KeyError, self.parser.getMessage, 'f00', {'p2': 'joe'})

    def test_with_unicode_dict_parameter(self):
        self.parser._messages['f00'] = "bar %(p1)s"
        self.assertEqual("bar joéÄ", self.parser.getMessage('f00', {'p1': 'joéÄ'}))



class Test_getMessageVariables(unittest.TestCase):

    def setUp(self):
        self.parser = DummyParser()

    def test_with_parameters(self):
        client = Client(name="Jack")
        rv = self.parser.getMessageVariables(client)
        assert_dict_contains_subset(self, {'name': client.name}, rv, rv)

    def test_with_named_parameters(self):
        client = Client(name="Jack")
        assert_dict_contains_subset(self, {'clientname': client.name, 'reason': 'this is a good reason'}, self.parser.getMessageVariables(client=client, reason="this is a good reason"))

    def test_with_named_parameters__unicode(self):
        client = Client(name="ÄÖé")
        assert_dict_contains_subset(self, {'clientname':client.name, 'reason': 'this is a good reason'}, self.parser.getMessageVariables(client=client, reason="this is a good reason"))


class Test_getWrap(unittest.TestCase):

    def setUp(self):
        self.parser = DummyParser()

    def test_wrapped_initialized(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap("TEST")
        self.assertIsNotNone(self.parser.wrapper)

    def test_with_invalid_input(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap(None)
        self.assertListEqual(wrapped_text, [])

    def test_with_empty_string(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap(None)
        self.assertListEqual(wrapped_text, [])

    def test_no_color_codes(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap("Lorem ipsum dolor sit amet, consectetur adipisci elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.")
        self.assertIsInstance(wrapped_text, list)
        self.assertListEqual(wrapped_text, ["Lorem ipsum dolor sit amet, consectetur",
                                            ">adipisci elit, sed eiusmod tempor",
                                            ">incidunt ut labore et dolore magna",
                                            ">aliqua."])

    def test_no_color_codes_with_color_prefix_set(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = '^5'
        wrapped_text = self.parser.getWrap("Lorem ipsum dolor sit amet, consectetur adipisci elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.")
        self.assertIsInstance(wrapped_text, list)
        self.assertListEqual(wrapped_text, ["Lorem ipsum dolor sit amet, consectetur",
                                            ">adipisci elit, sed eiusmod tempor",
                                            ">incidunt ut labore et dolore magna",
                                            ">aliqua."])

    def test_with_color_codes_and_color_prefix(self):
        self.parser._use_color_codes = True
        self.parser._line_length = 40
        self.parser._line_color_prefix = '^7'
        wrapped_text = self.parser.getWrap("Lorem ipsum dolor sit ^2amet, consectetur adipisci elit, ^1sed eiusmod ^7tempor incidunt ut ^8labore et dolore magna ^2aliqua.")
        self.assertIsInstance(wrapped_text, list)
        self.assertListEqual(wrapped_text, ["^7Lorem ipsum dolor sit ^2amet,",
                                            "^3>^2consectetur adipisci elit, ^1sed eiusmod",
                                            "^3>^1^7tempor incidunt ut ^8labore et dolore",
                                            "^3>^8magna ^2aliqua."])

    def test_with_color_codes_and_no_color_prefix(self):
        self.parser._use_color_codes = True
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap("Lorem ipsum dolor sit ^2amet, consectetur adipisci elit, ^1sed eiusmod ^7tempor incidunt ut ^8labore et dolore magna ^2aliqua.")
        self.assertIsInstance(wrapped_text, list)
        self.assertListEqual(wrapped_text, ["Lorem ipsum dolor sit ^2amet,",
                                            "^3>^2consectetur adipisci elit, ^1sed eiusmod",
                                            "^3>^1^7tempor incidunt ut ^8labore et dolore",
                                            "^3>^8magna ^2aliqua."])

    def test_with_short_message_length(self):
        self.parser._use_color_codes = False
        self.parser._line_length = 40
        self.parser._line_color_prefix = ''
        wrapped_text = self.parser.getWrap("Lorem ipsum dolor sit amet")
        self.assertIsInstance(wrapped_text, list)
        self.assertListEqual(wrapped_text, ["Lorem ipsum dolor sit amet"])


if __name__ == '__main__':
    unittest.main()


class Test_dispatcher_is_shared(unittest.TestCase):

    def test_fake_console_uses_the_production_dispatcher(self):
        # a private copy of the dispatch loop is how time.clock() shipped dead
        from b3.fake import FakeConsole
        self.assertIs(Parser._dispatch, FakeConsole._dispatch)

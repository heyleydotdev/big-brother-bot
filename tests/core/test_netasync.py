
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

import socket
import time
import unittest

from b3.lib import netasync


class Test_writable(unittest.TestCase):

    def test_receiver_is_not_write_interested(self):
        self.assertFalse(netasync.dispatcher().writable())

    def test_writer_is_write_interested_only_with_buffered_data(self):
        channel = netasync.dispatcher_with_send()
        self.assertFalse(channel.writable())
        channel.out_buffer = b'x'
        self.assertTrue(channel.writable())


class Test_idle_loop(unittest.TestCase):

    def setUp(self):
        netasync._socket_map.clear()
        self.sock, self.peer = socket.socketpair()
        self.channel = netasync.dispatcher(self.sock)
        self.channel.connected = True

    def tearDown(self):
        self.channel.close()
        self.peer.close()
        netasync._socket_map.clear()

    def test_idle_channel_does_not_spin(self):
        # an always-writable socket made select() return at once: 190k loops/s
        # with a 1s timeout, one core per frostbite2/chiv/frontline server
        started = time.perf_counter()
        netasync.loop(timeout=0.5, count=1)
        self.assertGreaterEqual(time.perf_counter() - started, 0.4)


class Test_writer(unittest.TestCase):

    def test_send_flushes_immediately_and_leaves_no_write_interest(self):
        netasync._socket_map.clear()
        mine, peer = socket.socketpair()
        channel = netasync.dispatcher_with_send(mine)
        channel.connected = True
        try:
            channel.send(b'hello')
            self.assertEqual(b'', channel.out_buffer)
            self.assertFalse(channel.writable())
            self.assertEqual(b'hello', peer.recv(5))
        finally:
            channel.close()
            peer.close()
            netasync._socket_map.clear()

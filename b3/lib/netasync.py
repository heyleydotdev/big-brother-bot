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

"""
Minimal asyncore-compatible layer on the modern `selectors` stdlib.

asyncore was removed from the stdlib in python 3.12, but B3 uses only a
tiny slice of its API: `dispatcher`/`dispatcher_with_send` classes with
handle_read/handle_connect/handle_close hooks and a polling
`loop(timeout, count)` call. This module implements exactly that surface
so the log listeners and game protocol clients keep their structure.

NOT implemented (unused by B3): accept/listening servers, asynchat-style
producers/consumers, channel maps other than the global one.
"""

import errno
import selectors
import socket
import sys
import traceback
import os

_socket_map = {}


class dispatcher(object):

    connected = False
    accepting = False
    closing = False
    debug = False
    log_info = None
    addr = None

    def __init__(self, sock=None, map=None):
        if map is None:
            map = _socket_map
        self._map = map
        self.socket = None
        self._fileno = None
        if sock:
            self.set_socket(sock)

    def set_socket(self, sock, map=None):
        self.socket = sock
        self._fileno = sock.fileno()
        self._map[self._fileno] = self

    def create_socket(self, family, type):
        sock = socket.socket(family, type)
        sock.setblocking(False)
        self.set_socket(sock)

    def connect(self, address):
        self.connected = False
        try:
            self.socket.connect(address)
        except BlockingIOError:
            # non blocking connect in progress: completion is handled
            # by handle_connect_event on the first read/write ready event
            return
        self.connected = True
        self.addr = address

    def bind(self, address):
        self.socket.bind(address)

    def recv(self, buffer_size):
        try:
            return self.socket.recv(buffer_size)
        except BlockingIOError:
            return b''

    def readable(self):
        return True

    def writable(self):
        return True

    # -----------------------------------------------------------------
    # events

    def handle_read_event(self):
        if self.accepting and not self.connected:
            self.handle_accept()
        elif not self.connected:
            self.handle_connect_event()
        else:
            self.handle_read()

    def handle_write_event(self):
        if not self.connected:
            self.handle_connect_event()
        else:
            self.handle_write()

    def handle_connect_event(self):
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            raise OSError(err, os.strerror(err))
        self.handle_connect()
        self.connected = True

    # -----------------------------------------------------------------
    # user overridables (same names and semantics as asyncore)

    def handle_read(self):
        pass

    def handle_write(self):
        pass

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_accept(self):
        pass

    def handle_error(self):
        _, t, v, tb = sys.exc_info()
        if tb is not None:
            tb = tb.tb_next
        print('Uncaptured python exception, closing channel %r (%s:%s %s)' % (self, t, v, v.args),
              file=sys.stderr)
        traceback.print_exception(t, v, tb, file=sys.stderr)
        self.close()

    # -----------------------------------------------------------------

    def close(self):
        self.connected = False
        self.closing = True
        if self._fileno is not None:
            if self._fileno in self._map:
                del self._map[self._fileno]
            self._fileno = None
        if self.socket is not None:
            self.socket.close()
            self.socket = None


class dispatcher_with_send(dispatcher):

    out_buffer = b''
    ac_out_buffer_size = 4096

    def send(self, data):
        self.out_buffer += data
        self.initiate_send()

    def initiate_send(self):
        while self.out_buffer and not self.closing:
            try:
                sent = self.socket.send(self.out_buffer[:self.ac_out_buffer_size])
            except BlockingIOError:
                return
            except OSError:
                self.handle_error()
                return
            self.out_buffer = self.out_buffer[sent:]

    def handle_write(self):
        self.initiate_send()


def poll(timeout=0.0):
    """
    Poll the registered dispatchers once, dispatching read/write events.
    """
    if not _socket_map:
        return
    selector = selectors.DefaultSelector()
    try:
        for obj in list(_socket_map.values()):
            if obj.socket is None:
                continue
            events = 0
            if obj.readable():
                events |= selectors.EVENT_READ
            if obj.writable():
                events |= selectors.EVENT_WRITE
            if events:
                selector.register(obj.socket, events, obj)
        for key, mask in selector.select(timeout):
            obj = key.data
            try:
                if mask & selectors.EVENT_WRITE:
                    obj.handle_write_event()
                if obj.socket is not None and mask & selectors.EVENT_READ:
                    obj.handle_read_event()
            except OSError:
                obj.handle_error()
            except Exception:
                obj.handle_error()
    finally:
        selector.close()


def loop(timeout=30.0, count=None, use_poll=False):
    """
    Poll until there is nothing left to poll or `count` iterations have
    run. Mirrors asyncore.loop: count=None means run until the map is empty.
    """
    if count is None:
        while _socket_map:
            poll(timeout)
    else:
        while count > 0:
            poll(timeout)
            count = count - 1

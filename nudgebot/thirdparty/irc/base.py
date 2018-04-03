import re

from nudgebot.log import Loggable
from cached_property import cached_property

import socket
from types import MethodType, FunctionType
from threading import RLock
import logging
from nudgebot.utils import RunEvery
from nudgebot.thirdparty.base import Party


class required_connection(object):
    """Required connection decorator"""
    def __init__(self, method):
        assert isinstance(method, (MethodType, FunctionType))
        self._method = method

    def __get__(self, obj, cls):
        self._cls = cls
        self._obj = obj
        return self

    def __call__(self, *args, **kwargs):
        if not self._obj.is_connected():
            raise Exception()  # TODO: Exception
        return self._method(self._obj, *args, **kwargs)


class IRCclient(Loggable):
    """
    An IRC Client.

    Example:
        client = IRCclient('chat.freenode.net', 'Nudgebot')
        client.connect()
        client.join('##bot-testing')
        client.msg('##bot-testing', 'Hello all')

    @todo: Support servers with password.
    """

    READ_TIMEOUT = 1  # seconds
    PONG_SERVER_TIMER = 60  # seconds
    _line_splitter = r'\r\n'

    def __init__(self, server: str, nick: str, port=6667):
        assert isinstance(server, str), f'server must be an `str`, got {server}'
        assert isinstance(nick, str), f'nick must be an `str`, got {nick}'
        self._ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ircsock.settimeout(self.READ_TIMEOUT)
        self._server = server
        self._nick = nick
        self._connected = False
        self._io_mutex = RLock()
        self._pong_server_timer = RunEvery(self.PONG_SERVER_TIMER, self.pong_server)
        self._channels = []
        Loggable.__init__(self)
        self.logger.setLevel(logging.DEBUG)

    @property
    def server(self):
        return self._server

    @property
    def nick(self):
        return self._nick

    def connect(self):
        self._ircsock.connect((self._server, 6667))
        self._connected = True
        self.send('USER', ' '.join([self._nick, self._nick, self._nick, self._nick]))
        self.send('NICK', self._nick)
        self._pong_server_timer.start()
        self.logger.info(f'Connected to IRC: server="{self._server}", nick="{self._nick}"')

    def disconnect(self):
        self._pong_server_timer.cancel()
        self._ircsock.close()
        self._connected = False

    def is_connected(self):
        return self._connected

    @required_connection
    def raw_send(self, data: str):
        assert isinstance(data, str)
        self._io_mutex.acquire()
        self.logger.debug(f'Sending data: {data}')
        self._ircsock.send(bytes(data.encode()))
        self._io_mutex.release()

    @required_connection
    def raw_read(self, buffersize=1024, timeout=None):
        self._io_mutex.acquire()
        if timeout:
            assert isinstance(timeout, (int, float)), f'timeout must be a number, got: {timeout}'
            self._ircsock.settimeout(timeout)
        try:
            data = str(self._ircsock.recv(buffersize))
        except socket.timeout:
            data = ''
        finally:
            if timeout:
                self._ircsock.settimeout(self.READ_TIMEOUT)
        if self.logger.level == logging.DEBUG:
            for line in data.split(self._line_splitter):
                self.logger.debug(f'Read data - line: {line}')
        self._io_mutex.release()
        return data

    def send(self, command, data):
        self.logger.debug(f'Sending: {command} {data}')
        self.raw_send(f'{command} {data}\n')

    def read(self, timeout=None):
        recv = self.raw_read(timeout=timeout)
        out = ''
        while recv:
            out += recv
            recv = self.raw_read(timeout=timeout)
        return out

    def read_lines(self, timeout=None):
        return self.read(timeout).split(self._line_splitter)

    @property
    def channels(self):
        return self._channels

    def quit(self, msg='Bye'):
        self.send('QUIT', msg)

    def ping(self, to):
        self.send('PING', f':{to}')

    def pong(self, to):
        self.send('PONG', f':{to}')

    def msg(self, channel: str, msg: str):
        self.send('PRIVMSG', f'{channel} :{msg}')

    def join(self, channel: str):
        self.logger.info(f'Joining channel: {channel}')
        self._channels.append(channel)
        self.send('JOIN', channel)

    def pong_server(self):
        self.send('PONG', f':{self._server}')

    def parse_messages(self, line: str, with_me_only=False):
        records = re.findall(r'([\w\d_\-]+)\!.+ PRIVMSG ([\w\d_\-\#]+) \:(.+)', line)
        if with_me_only:
            records = list(filter(lambda r: self._nick in r[-1], records))
        return records  # [(<sender>, <channel>, <message>), ]


class IRCparty(Party):
    key = 'irc'

    @cached_property
    def client(self):
        client = IRCclient(self.credentials['server'], self.credentials['nick'], port=self.credentials['port'])
        client.connect()
        for channel in self.config['channels']:
            client.join(channel)
        return client

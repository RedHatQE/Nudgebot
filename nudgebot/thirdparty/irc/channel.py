from cached_property import cached_property

from nudgebot.thirdparty.base import PartyScope
from nudgebot.thirdparty.irc.base import IRCparty
from nudgebot.thirdparty.irc.server import Server


class Channel(PartyScope):
    Party = IRCparty()
    primary_keys = ['server', 'name']
    Parent = Server

    def __init__(self, server: Server, name: str):
        self._server = server
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def server(self):
        return self._server

    @classmethod
    def init_by_keys(cls, **kwargs):
        return cls(kwargs.get('server'), kwargs.get('name'))

    @cached_property
    def query(self) -> dict:
        return {'server': self._server.url, 'name': self._name}

    @cached_property
    def parent(self):
        return self.Parent(self._server)

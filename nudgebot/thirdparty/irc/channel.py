from cached_property import cached_property

from nudgebot.thirdparty.base import EndpointScope
from nudgebot.thirdparty.irc.base import IRCendpoint
from nudgebot.thirdparty.irc.server import Server


class Channel(EndpointScope):
    Endpoint = IRCendpoint()
    Parents = [Server]
    primary_keys = ['server', 'channel']

    def __init__(self, server: Server, name: str):
        self._server = server
        self._name = name

    @property
    def server(self):
        return self._server

    @property
    def name(self):
        return self._name

    @classmethod
    def init_by_keys(cls, **query):
        return cls(Server.init_by_keys(**query), query.get('channel'))

    @cached_property
    def query(self) -> dict:
        return {'server': self._server.url, 'channel': self._name}

    @cached_property
    def parent(self):
        return self.Parents[0](self._server)

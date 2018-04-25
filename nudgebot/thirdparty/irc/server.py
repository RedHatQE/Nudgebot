from cached_property import cached_property

from nudgebot.thirdparty.base import EndpointScope
from nudgebot.thirdparty.irc.base import IRCendpoint


class Server(EndpointScope):
    Endpoint = IRCendpoint()
    primary_keys = ['server']
    key = 'irc_server'

    def __init__(self, url):
        self._url = url

    @property
    def url(self):
        return self._url

    @classmethod
    def init_by_keys(cls, **kwargs):
        return cls(kwargs.get('server'))

    @cached_property
    def query(self) -> dict:
        return {'server': self._url}

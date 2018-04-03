from cached_property import cached_property

from nudgebot.thirdparty.base import PartyScope
from nudgebot.thirdparty.irc.base import IRCparty


class Server(PartyScope):
    Party = IRCparty()
    primary_keys = ['url']
    key = 'irc_server'

    def __init__(self, url):
        self._url = url

    @property
    def url(self):
        return self._url

    @classmethod
    def init_by_keys(cls, **kwargs):
        return cls(kwargs.get('url'))

    @cached_property
    def query(self)->dict:
        return {'url': self._url}

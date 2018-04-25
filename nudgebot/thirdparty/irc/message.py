from datetime import datetime

from nudgebot.thirdparty.base import EndpointScope
from nudgebot.thirdparty.irc.base import IRCendpoint
from nudgebot.thirdparty.irc.channel import Channel
from cached_property import cached_property


class Message(EndpointScope):
    Party = IRCendpoint()
    primary_keys = ['server', 'channel', 'sender', 'content', 'datetime']
    Parents = [Channel]

    def __init__(self, channel: Channel, sender: str, content: str, datetime_obj: datetime):
        assert isinstance(channel, Channel)
        assert isinstance(sender, str)
        assert isinstance(content, str)
        assert isinstance(datetime_obj, datetime)
        self._channel = channel
        self._sender = sender
        self._content = content
        self._datetime = datetime_obj

    @property
    def channel(self):
        return self._channel

    @property
    def sender(self):
        return self._sender

    @property
    def content(self):
        return self._content

    @property
    def datetime(self):
        return self._datetime

    @cached_property
    def server(self):
        return self._channel.server

    @classmethod
    def init_by_keys(cls, **query):
        return cls(Channel.init_by_keys(**query), query.get('sender'), query.get('content'), query.get('datetime'))

    @cached_property
    def query(self) -> dict:
        return {
            'server': self.server.url, 'channel': self._channel.name, 'sender': self._sender,
            'content': self._content, 'datetime': self._datetime
        }

    @cached_property
    def parent(self):
        return self.Parents[0].init_by_keys(**self.query)

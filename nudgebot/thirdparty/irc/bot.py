from datetime import datetime
import hashlib

from nudgebot.thirdparty.base import Event, EventsFactory, BotSlave
from nudgebot.thirdparty.irc.base import IRCendpoint
from nudgebot.thirdparty.irc.message import Message


class IRCevent(Event):
    Endpoint = IRCendpoint()


class MessageEvent(IRCevent):
    EndpointScope = Message

    def __init__(self, server, sender, channel, content, datetime_obj):
        self._server = server
        self._sender = sender
        self._channel = channel
        self._content = content
        self._datetime = datetime_obj

    @property
    def id(self):
        return hashlib.md5(f'{self._sender},{self._channel},{self._content}'.encode()).hexdigest()

    @property
    def data(self) -> dict:
        return {
            'server': self._server, 'sender': self._sender, 'channel': self._channel,
            'content': self._content, 'datetime': self._datetime
        }


class MessageMentionedMeEvent(MessageEvent):
    pass


class IRCeventsFactory(EventsFactory):
    Endpoint = IRCendpoint()
    _check_for_new_events_interval = 1

    def build_events(self) -> list:
        events = []
        lines = self.Endpoint.client.read_lines()
        if lines:
            now = datetime.now()
            for line in lines:
                records = self.Endpoint.client.parse_messages(line)
                if records:
                    for sender, channel, content in records:
                        if self.Endpoint.client.nick in content:
                            events.append(MessageMentionedMeEvent(self.Endpoint.client.server, sender, channel, content, now))
                        else:
                            events.append(MessageEvent(self.Endpoint.client.server, sender, channel, content, now))
        return events


class IRCbot(BotSlave):
    Endpoint = IRCendpoint()
    EventsFactory = IRCeventsFactory()
    handle_events_every = 1

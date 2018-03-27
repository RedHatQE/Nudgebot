"""
Thirdparty module includes the interfaces for the third party.

Each implemented third party module should implement these classes.
"""
from abc import ABCMeta, abstractclassmethod, abstractproperty, abstractmethod

from cached_property import cached_property

from nudgebot.base import SubclassesGetterMixin, ABCMetaSingleton
from nudgebot.settings import CurrnetProject
from nudgebot.db.db import CachedStack


class Party(SubclassesGetterMixin, metaclass=ABCMetaSingleton):
    """
    The Party class represents the actual third party interface.

    It holds the credentials, metadata and the api client.
        Should be defined in subclass:
            * key: `str` the key of the third party as appear in the yaml.
    """

    key = None

    def __init_subclass__(cls):  # @NoSelf
        """Verify static attributes."""
        assert cls.key is not None, 'static attribute `key` must be defined'
        assert isinstance(cls.key, str), 'static attribute `key` must be a `str`'
        assert cls.key in CurrnetProject().config.config, 'key "{}" not found in the config yaml'.format(cls.key)
        assert cls.key in CurrnetProject().config.credentials, 'key "{}" not found in the credentials yaml'.format(cls.key)

    @abstractproperty
    def client(self):
        """Return the api client.

        @attention: Use cached_property in the implementation!
        """
        raise NotImplementedError()

    @cached_property
    def config(self):
        """Return the config data."""
        return CurrnetProject().config.config[self.key]

    @cached_property
    def credentials(self):
        """Return the credentials data."""
        return CurrnetProject().config.credentials[self.key]


class APIclass(object):
    """
    A marker for API class. each API class should inherit this.

    e.g. The PullRequest class is an API class of the Github party
    """

    pass


class PartyScope(APIclass, metaclass=ABCMeta):
    """
    Party scope is used to separate the Party into scopes.

    It used for:
        1. have a bridge between the received event and the produced APIclass instances.
        2. Distinguish among the collected statistics (i.e. which statistics to collect after the event received).
    Every time the bot receives an Event from the party's EventHandler, it maps the event data into instances
    of these PartyScope's (which are APIclass's). Implementation example:
        pull request event has the party scopes `Repository` and `PullRequest`, hence, every time the Bot receives
        a PullRequestEvent from the GithubEventHandler, it creates instances of Repository and PullRequest using the init_by_keys
        method. then it collect the statistics that has these party scopes.
    Should be defined in subclass:
        * Party: `Party` The party instance of the scope.
        * primary_keys: (`list` of `str`) The primary keys of this scope, it used to be able to distinguish among the instances
                        and be able to instantiate them independently from these keys without using a parent(s). In case that the
                        PartyScope primary_key is None, it will treat it as singleton scope, e.g. Settings panel is probably a
                        single view in some application.
                        for example:
                            The primary keys of a pull request are 'organization', 'repository' and 'number', these the key
                            elements actually distinguish among all the pull requests in Github and provide the ability to
                            instantiate a pull request independently without instantiating repository and then pass it to
                            the instantiate method.
    """

    Party = None
    primary_keys = None

    def __init_subclass__(cls):  # @NoSelf
        """Verify static attributes."""
        assert cls.Party is not None, 'static attribute `Party` should be defined in {}'.format(cls)
        assert isinstance(cls.Party, Party), 'static attribute `Party` should be a `Party` instance, not `{}`'.format(
            getattr(cls.Party, '__class__', type(cls.Party)))
        cls.primary_keys = cls.primary_keys or []
        assert all(isinstance(key, str) for key in cls.primary_keys)

    @abstractclassmethod
    def init_by_keys(cls, **kwargs):  # @NoSelf
        """Instantiate the scope by keys.

        e.g.
            PullRequest.init_by_keys(organization='octocat', repository='Hello-World', number=1) -->
                PullRequest(organization='octocat', repository='Hello-World', number=1)
        """
        raise NotImplementedError()

    @classmethod
    def init_by_event(cls, event):
        """Instantiate the scope by event.

        e.g.
            PullRequest.init_by_event(PullRequestEvent()) --> PullRequest()
        """
        assert isinstance(event, Event), 'event should be an instance of `Event`, not `{}`'.format(type(event))
        if not all(k in event.data for k in cls.primary_keys):
            raise  # TODO: Exception
        return cls.init_by_keys(**{k: event.data[k] for k in cls.primary_keys})

    @classmethod
    def is_singleton_scope(cls):
        """Return whether this party scope is a singleton or not."""
        return not cls.primary_keys


class Event(SubclassesGetterMixin, metaclass=ABCMeta):
    """
    An Event class represents an event that happens in the party.

    each event has party scopes which are being instantiated using its data. For example:
        RepositoryEvent creates an instance of Repository which is later used to collect statistics.
    Should be defined in subclass:
        * PartyScopes: The scopes of the event. for more info - read the PartyScope docstring.
    """

    PartyScopes = []

    @abstractproperty
    def id(self):
        """Return the unique id of the event."""
        raise NotImplementedError()

    @abstractproperty
    def data(self) -> dict:
        """Return the data of the event. this data will use to instantiate the PartyScope's.

        @attention: this data dict must include all the primary key values of the associated PartyScopes
        """
        raise NotImplementedError()

    @property
    def party(self):
        """Return the Party of the event."""
        return self.PartyScope.Party

    @property
    def hash(self):
        """Return the unique hash for of the event."""
        return '{}::{}::{}'.format(self.part.key, self.PartyScope.__name__, self.id)


class EventsFactory(metaclass=ABCMetaSingleton):
    """
    An events factory is used to listen to the party, detect, and classify new events in the third party.

    When the parent object calls to get_new_events(), new data (AKA grab_new_data) is grabbed from the third party
    and then it builds the events (AKA build events) from this raw data.
    _dilivered_events_stack is used to store the hash's of the events that has already been delivered, once new events
    have been detected, it push them to the stack (AKA _push_to_delivered_events_stack) and returns them to
    the parent object.
    Should be defined in subclass:
        * Party: `Party` The events factory's party.
    """

    Party: Party = None
    _dilivered_events_stack = CachedStack('delivered_events',
                                          length=CurrnetProject().config.config.events.delivered_stack_length)

    @abstractmethod
    def grab_new_data(self):
        """Grab new raw data from the third party client.

        This function should return a new data as raw (primitive types like `dict`, `list`, etc), then build_events
        will use this to build the events.
        """
        raise NotImplementedError()

    @abstractmethod
    def build_events(self, data) -> list:
        """Build the events from the received raw data.

        @param data: The data as raw.
        """
        raise NotImplementedError()

    def _push_to_delivered_events_stack(self, event: Event):
        """Push the event to the delivered events stack.

        @param event: `Event` The event to push
        """
        assert isinstance(event, Event), 'Cannot push non-event object to the delivered events buffer.'
        if len(self._delivered_events_buffer) == self.BufferLength:
            self._dilivered_events_stack.pop(0)
            self._dilivered_events_stack.append(event.hash)

    @property
    def delivered_events(self):
        """Return the delivered events."""
        return self._dilivered_events_stack

    def get_new_events(self) -> list:
        """Return new events."""
        events = self.build_events(self.grab_new_data())
        for event in events:
            self._push_to_delivered_events_stack(event)
        return events

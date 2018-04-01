"""
Thirdparty module includes the interfaces for the third party.

Each implemented third party module should implement these classes.
"""
import time

from cached_property import cached_property

from nudgebot.base import SubclassesGetterMixin, ABCMetaSingleton
from nudgebot.settings import CurrentProject
from nudgebot.db.db import CachedStack
from nudgebot.log import Loggable
from threading import Thread


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
        assert cls.key in CurrentProject().config.config, 'key "{}" not found in the config yaml'.format(cls.key)
        assert cls.key in CurrentProject().config.credentials, 'key "{}" not found in the credentials yaml'.format(cls.key)

    @property
    def client(self):
        """Return the api client.

        @attention: Use cached_property in the implementation!
        """
        raise NotImplementedError()

    @cached_property
    def config(self):
        """Return the config data."""
        return CurrentProject().config.config[self.key]

    @cached_property
    def credentials(self):
        """Return the credentials data."""
        return CurrentProject().config.credentials[self.key]


class APIclass(object):
    """
    A marker for API class. each API class should inherit this.

    e.g. The PullRequest class is an API class of the Github party
    """

    pass


class PartyScope(SubclassesGetterMixin, APIclass):
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
        * Parent: The parent party scope, for example: repository is the parent of pull request.
    """

    Party = None
    primary_keys = []
    Parent = None

    @classmethod
    def all(cls):  # @NoSelf
        """Return a generator of all the instances of the party scope"""
        raise NotImplementedError()

    @classmethod
    def init_by_keys(cls, **kwargs):  # @NoSelf
        """Instantiate the scope by keys.

        e.g.
            PullRequest.init_by_keys(organization='octocat', repository='Hello-World', number=1) -->
                PullRequest(organization='octocat', repository='Hello-World', number=1)
        """
        raise NotImplementedError()

    @cached_property
    def query(self) -> dict:
        """Return the query according to the primary keys"""
        raise NotImplementedError()

    @cached_property
    def parent(self):
        raise NotImplementedError()

    @classmethod
    def get_all_parent_classes(cls):
        """Return all the parents of the scope"""
        parents = []
        parent = cls.Parent
        while True:
            parents.append(parent)
            if not hasattr(parent, 'Parent') or not parent.Parent:
                break
            parent = parent.Parent
        return parents

    @cached_property
    def hierarchy(self):
        hierarchy = [self]
        while issubclass(hierarchy[-1].__class__, self.__class__) and hierarchy[-1].parent:
            hierarchy.append(hierarchy[-1].parent)
        return hierarchy

    @classmethod
    def get_hierarchy_classes(cls):
        return [cls] + cls.get_all_parent_classes()

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


class Event(SubclassesGetterMixin):
    """
    An Event class represents an event that happens in the party.

    each event has party scopes which are being instantiated using its data. For example:
        RepositoryEvent creates a instance Repository instance which later used to collect statistics.
    Should be defined in subclass:
        * Party: `Party`
        * PartyScopes: The scopes of the event. for more info - read the PartyScope docstring.
    """

    Perty = None
    PartyScopes = []

    def __init_subclass__(self):
        assert all(issubclass(ps, PartyScope) for ps in self.PartyScopes), \
            'All party scopes should be subclasses of {}'.format(PartyScope.__name__)
        assert all(ps.Party == self.PartyScopes[0].Party for ps in self.PartyScopes), \
            'All party scopes should have the same party'

    def __repr__(self):
        return '<{} id={}, hash={}>'.format(self.__class__.__name__, self.id, self.hash)

    @property
    def id(self):
        """Return the unique id of the event."""
        raise NotImplementedError()

    @property
    def data(self) -> dict:
        """Return the data of the event. this data will use to instantiate the PartyScope's.

        @attention: this data dict must include all the primary key values of the associated PartyScopes
        """
        raise NotImplementedError()

    @property
    def party(self):
        """Return the Party of the event."""
        return self.Party

    @classmethod
    def hash_by_id(cls, event_id):
        """Return the hash for the event using ID only"""
        return '{}::{}'.format(cls.Party.key, event_id)

    @property
    def hash(self):
        """Return the unique hash for of the event."""
        return self.hash_by_id(self.id)


class EventsFactory(Loggable, Thread, metaclass=ABCMetaSingleton):
    """
    An events factory is used to listen to the party, detect, and classify new events in the third party.

    The events factory is running in a separated thread and collect new events and store them in the events buffer.
    Every X seconds interval (`_check_for_new_events_interval`) it calls to `build_events` which responsible to get
    new data, classify the events and store them in the events buffer.
    Each time the parent is calling to `pull_event`, it's popping the first event in the buffer and return it.

    Should be defined in subclass:
        * Party: `Party` The events factory's party.
    """

    Party: Party = None
    _dilivered_events_stack = CachedStack('delivered_events',
                                          length=CurrentProject().config.config.events.delivered_stack_length)
    _check_for_new_events_interval = CurrentProject().config.config.events.check_interval
    _events_buffer = []

    def __init__(self):
        Loggable.__init__(self)
        Thread.__init__(self, name=self.__class__.__name__, daemon=True)
        self._buffer_buisy_mutex = False

    def build_events(self) -> list:
        """Build new_events"""
        raise NotImplementedError()

    def collect_new_events(self) -> list:
        """Collecting new events and push them into the events buffer"""
        self.logger.info('Collecting new events...')
        events = self.build_events()
        if not events:
            self.logger.info('No new events.')
        for event in events:
            self.logger.info('New event detected: {}'.format(event))
            while self._buffer_buisy_mutex:
                pass  # TODO: Better
            self._buffer_buisy_mutex = True
            self._events_buffer.append(event)
            self._buffer_buisy_mutex = False

    def pull_event(self):
        """Return the first event in the events buffer. if the events buffer is empty, return None."""
        while self._buffer_buisy_mutex:
            pass  # TODO: Better
        self._buffer_buisy_mutex = True
        event = None
        if self._events_buffer:
            event = self._events_buffer.pop(0)
            self._dilivered_events_stack.push(event.hash)
        self._buffer_buisy_mutex = False
        if event:
            self.logger.info('Pulling new event: {}'.format(event))
        return event

    def run(self):
        """Overwrite of Thread.run. Collect and store events in infinite loop with interval `_check_for_new_events_interval`"""
        while True:
            last_check = time.time()
            self.collect_new_events()
            while time.time() - last_check < self._check_for_new_events_interval:
                self.logger.debug('Waiting for new events collection: new collection in {}s'.format(
                    self._check_for_new_events_interval - (time.time() - last_check)))
                time.sleep(3)

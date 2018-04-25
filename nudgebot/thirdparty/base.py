"""
Thirdparty module includes the interfaces for the third party.

Each implemented third party module should implement these classes.
"""
import time
from threading import Lock

from wait_for import wait_for
from cached_property import cached_property

from nudgebot.base import SubclassesGetterMixin, Singleton, Thread
from nudgebot.settings import CurrentProject
from nudgebot.db.db import CachedStack
from nudgebot.log import Loggable
from nudgebot.exceptions import SubThreadException


class Endpoint(SubclassesGetterMixin, metaclass=Singleton):
    """
    The Endpoint class represents the actual third party interface.

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

    e.g. The PullRequest class is an API class of the Github Endpoint.
    """

    pass


class EndpointScope(SubclassesGetterMixin, APIclass):
    """
    Endpoint scope is used to separate the Endpoint into scopes.

    It used for:
        1. have a bridge between the received event and the produced APIclass instances.
        2. Distinguish among the collected statistics (i.e. which statistics to collect after the event received).
    Every time the bot receives an Event from the Endpoint's EventFactory, it maps the event data into instances
    of these EndpointScope's (which are APIclass's). Implementation example:
        pull request event has the endpoint scopes `Repository` and `PullRequest`, hence, every time the Bot receives
        a PullRequestEvent from the GithubEventHandler, it creates instances of Repository and PullRequest using the init_by_keys
        method. then it collect the statistics that has these endpoint scopes.
    Should be defined in subclass:
        * Endpoint: `Endpoint` The endpoint instance of the scope.
        * primary_keys: (`list` of `str`) The primary keys of this scope, it used to be able to distinguish among the instances
                        and be able to instantiate them independently from these keys without using a parent(s). In case that the
                        EndpointScope primary_key is None, it will treat it as singleton scope, e.g. Settings panel is probably a
                        single view in some application.
                        for example:
                            The primary keys of a pull request are 'organization', 'repository' and 'number', these the key
                            elements actually distinguish among all the pull requests in Github and provide the ability to
                            instantiate a pull request independently without instantiating repository and then pass it to
                            the instantiate method.
        * Parents: The parent endpoint scopes, for example: The parent of Repository are [Organization, User].
    """

    Endpoint = None
    primary_keys = []
    Parents = []

    @classmethod
    def init_by_keys(cls, **query):
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
        """
        Return the parent endpoint scope.

        @rtype: `EndpointScope`.
        """
        return  # Optional to overwrite

    @classmethod
    def get_static_hierarchy(cls, include_me=True):
        """
        Return all the classes in the hierarchy to the top

        @keyword include_me: `bool` Whether to include this class as well in the set.
        @rtype: `set`.
        """
        hierarchy = set()
        if include_me:
            hierarchy.add(cls)
        parents = cls.Parents
        for parent in parents:
            hierarchy.update(parent.get_static_hierarchy())
        return hierarchy

    @cached_property
    def hierarchy(self):
        hierarchy = [self]
        while issubclass(hierarchy[-1].__class__, EndpointScope) and hierarchy[-1].parent:
            hierarchy.append(hierarchy[-1].parent)
        return hierarchy

    @classmethod
    def init_by_event(cls, event):
        """Instantiate the scope by event.

        e.g.
            PullRequest.init_by_event(PullRequestEvent()) --> PullRequest()
        """
        assert isinstance(event, Event), 'event should be an instance of `Event`, not `{}`'.format(type(event))
        assert all(k in event.data for k in cls.primary_keys), \
            f'Missing keys in event data, event data keys: {event.data.keys()}; required keys: {cls.primary_keys}'
        return cls.init_by_keys(**{k: event.data[k] for k in cls.primary_keys})

    @classmethod
    def is_singleton_scope(cls):
        """Return whether this endpoint scope is a singleton or not."""
        return not cls.primary_keys


class Event(SubclassesGetterMixin):
    """
    An Event class represents an event that happens in the party.

    each event has endpoint scope which is being instantiated using its data. For example:
        RepositoryEvent creates a instance Repository instance which later used to collect statistics.
    Should be defined in subclass:
        * Endpoint: `Endpoint`
        * EndpointScope: The endpoint scope of the event. for more info - read the EndpointScope docstring.
    """

    Endpoint = None
    EndpointScope = None

    def __repr__(self):
        return '<{} id={}, hash={}>'.format(self.__class__.__name__, self.id, self.hash)

    @property
    def id(self):
        """Return the unique id of the event."""
        raise NotImplementedError()

    @property
    def data(self) -> dict:
        """
        Return the data of the event. this data will use to instantiate the EndpointScope.

        @attention: this data dict must include all the primary key values of the associated EndpointScope
        """
        raise NotImplementedError()

    @property
    def endpoint(self):
        """Return the endpoint of the event."""
        return self.Endpoint

    @classmethod
    def hash_by_id(cls, event_id):
        """Return the hash for the event using ID only"""
        return '{}::{}'.format(cls.Endpoint.key, event_id)

    @property
    def hash(self):
        """Return the unique hash for of the event."""
        return self.hash_by_id(self.id)


class EventsFactory(Loggable, Thread, metaclass=Singleton):
    """
    An events factory is used to listen to the endpoint, detect, and classify new events in the third party.

    The events factory is running asynchronously and collect new events and store them in the events buffer.
    Every X seconds interval (`_check_for_new_events_interval`) it calls to `build_events` which responsible to get
    new data, classify the events and store them in the events buffer.
    Each time the parent is calling to `pull_event`, it's popping the first event in the buffer and return it.

    Should be defined in subclass:
        * Endpoint: `Endpoint` The events factory's endpoint.
    """

    Endpoint: Endpoint = None
    _dilivered_events_stack = CachedStack('delivered_events',
                                          length=CurrentProject().config.config.events.delivered_stack_length)
    _check_for_new_events_interval = CurrentProject().config.config.events.check_interval

    def __init__(self):
        Thread.__init__(self)
        Loggable.__init__(self)
        self._events_buffer = []
        self._buffer_buisy_mutex = Lock()

    def __repr__(self):
        return f'<Events factory {self.__class__.__name__}>'

    def build_events(self) -> list:
        """
        Build new_events

        This factory method is actually the events factory.

        @rtype: (`list` of `Event`)
        """
        raise NotImplementedError()

    def collect_new_events(self) -> list:
        """Collecting new events and push them into the events buffer"""
        self.logger.debug('Collecting new events...')
        events = self.build_events()
        if not events:
            self.logger.debug('No new events.')
        for event in events:
            self.logger.info('A new event has been detected: {}'.format(event))
            self._buffer_buisy_mutex.acquire()
            self._events_buffer.append(event)
            self._buffer_buisy_mutex.release()

    def pull_event(self):
        """
        Return the first event in the events buffer. if the events buffer is empty, return None.

        @rtype: `Event`
        """
        self._buffer_buisy_mutex.acquire()
        event = None
        if self._events_buffer:
            event = self._events_buffer.pop(0)
            self._dilivered_events_stack.push(event.hash)
        self._buffer_buisy_mutex.release()
        if event:
            self.logger.info('Pulling new event: {}'.format(event))
        return event

    def run(self):
        """Collect and store events in infinite loop with interval `_check_for_new_events_interval`"""
        self.logger.info(f'Running {self.__class__.__name__}')
        while True:
            last_check = time.time()
            self.collect_new_events()
            while time.time() - last_check < self._check_for_new_events_interval:
                self.logger.debug('Waiting for new events collection: new collection in {}s'.format(
                    self._check_for_new_events_interval - (time.time() - last_check)))
                time.sleep(1)


class ScopesCollector(object, metaclass=Singleton):
    """
    ScopeCollector is used to collect all the scopes in the endpoint in order to perform a poll.

    For example, in the github endpoint, the scope collector is used to collect all the repositories, pull requests, issues, etc.
    and then with this object we will be able to collect the statistics and perform tasks.
    Some parties are not pollable (e.g. The IRC endpoint) so there is no need to implement this.

    """

    Endpoint = None

    def collect_all(self) -> list:
        """A factory method that build and return all the scope instances of the endpoint"""
        raise NotImplementedError()


class BotSlave(Thread):
    """Bot slave is the endpoint's bot.

    It is running in its own thread and responsible for handling the events, collecting the statistics, handling the tasks
    and the polls for the specific Endpoint.
    Each cycle it's pull event from its events factory, collecting statistics and handling the tasks.

    Should be defined in subclass:
        * Endpoint: `Endpoint` The bot's endpoint.
        * EventsFactory: `EventsFactory` The bot's events factory.
        * ScopeCollector (Optional): `ScopeCollector` In case that the bot is pollable you should provide this.

    """

    Endpoint: Endpoint = None
    EventsFactory = None
    ScopeCollector = None
    handle_events_every = 10  # The timeout between the events handling, optional to overwrite.

    def __init__(self, statistics: list, tasks: list):
        """
        Instantiate.

        @param statstics: (`list` of `Statistics`) The Statistics that the bot collects.
        @param tasks: (`list` of `Task`) The Tasks that the bot perform or evaluates.

        """
        Thread.__init__(self)
        Loggable.__init__(self)
        self._statistics = statistics
        self._tasks = tasks
        self._busy_mutext = Lock()

    def __repr__(self):
        return f'<Bot slave {self.__class__.__name__}>'

    @property
    def pollable(self):
        """Return whether the bot is pollable or not"""
        return bool(self.ScopeCollector)

    def get_conditional_tasks(self, scope: EndpointScope=None):
        """
        Return the conditional tasks of this bot.

        @keyword scope: `EndpointScope` The endpoint scope to filter by.
        @rtype: `ConditionalTask`
        """
        from nudgebot.tasks import ConditionalTask
        conditional_tasks = [task for task in self._tasks if issubclass(task, ConditionalTask)]
        if scope:
            static_hierarchy = [ps.__class__ for ps in scope.hierarchy]
            conditional_tasks = [task for task in conditional_tasks if task.EndpointScope in static_hierarchy]
        return conditional_tasks

    def poll(self):
        """
        If the bot is pollable, performing a poll, collecting all the scopes from the scopes collectors,
        updating statistics and handling tasks.
        """
        if not self.pollable:
            self.logger.warning('Poll has been triggered but the bot is not pollable! Return;')
            return
        self._busy_mutext.acquire()
        try:
            self.logger.info('Stating poll')
            for scope in self.ScopeCollector.collect_all():
                stats_collection = []
                for stat_class in self._statistics:
                    for parent in scope.hierarchy:
                        if stat_class.EndpointScope == parent.__class__:
                            statistics = stat_class(**parent.query)  # TODO: Init from scope
                            statistics.set_endpoint_scope(parent)
                            self.logger.debug(f'Collecting statistics: {statistics}')
                            statistics.collect()
                            stats_collection.append(statistics)
                for task_cls in self.get_conditional_tasks(scope):
                    task = task_cls(scope, stats_collection)
                    task.handle()

            self.logger.info('Finished poll')

        finally:
            self._busy_mutext.release()

    def handle_events(self):
        """Pulling new events from the event factory, collecting statistics and handling tasks"""
        self._busy_mutext.acquire()
        try:
            event = self.EventsFactory.pull_event()
            while event:
                self.logger.debug('Handling new event: {}'.format(event.id))
                event_endpoint_scope_classes = event.EndpointScope.get_static_hierarchy()
                stat_collection = []
                for statistics_cls in self._statistics:
                    if statistics_cls.EndpointScope in event_endpoint_scope_classes:
                        statistics = statistics_cls.init_by_event(event)
                        self.logger.debug(f'Collecting statistics: {statistics}')
                        stat_collection.append(statistics)
                        statistics.collect()
                self.logger.debug('Checking for tasks to run')
                for task_cls in self.get_conditional_tasks():
                    if task_cls.EndpointScope in event_endpoint_scope_classes:
                        task_endpoint_scope_classes = task_cls.EndpointScope.get_static_hierarchy()
                        statistics = []
                        for stats in stat_collection:
                            if stats.Endpoint == task_cls.Endpoint and stats.EndpointScope in task_endpoint_scope_classes:
                                statistics.append(stats)
                        task = task_cls(event.EndpointScope.init_by_event(event), statistics, event)
                        task.handle()
                event = self.EventsFactory.pull_event()
        finally:
            self._busy_mutext.release()

    def run(self):
        """
        Run the bot's main loop.

        Checking each cycle for new events, collecting statistics and handling tasks.

        @param poll_first: `bool` Whether to poll first or not.
        """
        if self.pollable:
            self.poll()
        if not self.EventsFactory.is_alive():
            self.EventsFactory.start()
        while True:
            if not self.EventsFactory.is_alive():
                self.logger.error(f'{self} events factory has died..')
                raise SubThreadException(self.EventsFactory)
            update_start_time = time.time()
            self.handle_events()
            wait_for(lambda: time.time() - update_start_time > self.handle_events_every and not self._busy_mutext.locked(),
                     logger=self.logger, message='Waiting for work timeout to finish.')

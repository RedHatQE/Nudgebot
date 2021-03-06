from collections import OrderedDict
from cached_property import cached_property
from types import MethodType

from nudgebot.base import SubclassesGetterMixin
from nudgebot.base.toggle_cached_properties import toggled_cached_property
from nudgebot.base.toggle_cached_properties import ToggledCachedProperties
from nudgebot.thirdparty.base import EndpointScope, Event
from nudgebot.db.db import DataCollection
from nudgebot.log import Loggable


class statistic(Loggable, toggled_cached_property):
    """Represents a statistic"""

    def __init__(self, getter):
        toggled_cached_property.__init__(self, getter)
        self.prettify = None
        Loggable.__init__(self)

    def __get__(self, obj, cls):
        self.obj = obj
        if self.obj and not hasattr(self.obj, '_toggled_cached_properties'):
            self.obj._toggled_cached_properties = {}
        return self

    def pretty(self, func):

        parent = self

        def pretty(value=None):
            return func(value or parent())

        self.prettify = pretty
        return self

    def __call__(self):
        self.logger.debug(f'Getting statistic: {self}')
        return toggled_cached_property.__call__(self)

    def uncache(self):
        self.logger.debug(f'Uncaching statistic: {self}')
        toggled_cached_property.uncache(self)

    def __repr__(self):
        return '<{}: {}.{}>'.format(self.__class__.__name__, self.obj, getattr(self.getter, '__name__', self.getter))


class constant_statistic(statistic):
    """
    This decorator provide the ability to add constant statistic.
    We use it for the primary keys statistics which are constants.
        @note: The decoration should be done via regular call. i.e. constant_statistic(self, k, v)
    """
    def __init__(self, obj, key, value):
        """
            @param obj: `object` The object which have this method will have.
            @param key: `str` The key (name) of the property.
            @param value: The value of the property.
        """
        def getter(*args):  # noqa
            return value
        self.obj = obj
        getter.__name__ = key
        getter = MethodType(getter, obj)
        statistic.__init__(self, getter)


class Statistics(Loggable, DataCollection, ToggledCachedProperties, SubclassesGetterMixin):
    """
    The Statistics class represents a bunch of statistics that related to a scope of some Endpoint.
    Once you define a Statistics class you can start to create the statistic getters which will
    be used to calculate and cache the statistics. once you call to a `statistic` object it
    calculates (i.e. run the getter), cache the returned value and return it, then, the next time you'll
    call this statistic it'll be cached, in order to un-cache you should just call <StatisticsInstance>.<stat>.uncache(),
    in order to un-cache all the statistics you can call self.uncache_all().
    In order to collect the statistics and store them in the database you can use self.collect() method.
    Should be defined in subclass:
        * EndpointScope: `EndpointScope` The Endpoint scope of this Statistics.
        * COLLECTION_NAME: `str` The name of the collection in the statistics database.
        * key: a Unique key identifier for the statistics.
    """
    EndpointScope = None
    COLLECTION_NAME = None
    key = None
    DATABASE_NAME = 'statistics'

    def __init__(self, **query):
        assert self.EndpointScope and EndpointScope in self.EndpointScope.__mro__
        assert self.COLLECTION_NAME and isinstance(self.COLLECTION_NAME, str)
        assert self.key and isinstance(self.key, str)
        assert all(k in self.EndpointScope.primary_keys for k in query.keys())
        Loggable.__init__(self)
        self._query = query
        self._scope = None
        self._add_query_to_stats()

    def __repr__(self):
        return '<{} query={}>'.format(self.__class__.__name__, self._query)

    def _add_query_to_stats(self):
        """Adding the query attributes as statistic's"""
        for k, v in self._query.items():
            setattr(self, k, constant_statistic(self, k, v))

    @classmethod
    def reload(cls):
        instances = []
        for data in cls.get_db_collection().find({}, {'_id': False}):
            instances.append(cls(**{k: v for k, v in data.items() if k in cls.EndpointScope.primary_keys}))
            instances[-1].set_cache(**data)
        return instances

    @cached_property
    def query(self):
        """Return the query"""
        return self._query

    @cached_property
    def scope(self):
        """Return the endpoint scope instance of the statistics"""
        if not self._scope:
            self._scope = self.EndpointScope.init_by_keys(**self._query)
        return self._scope

    @property
    def db_data(self):
        """Return the DB document of the statistics"""
        return self.db_collection.find_one(self._query, {'_id': False})

    def collect(self, cached_only=False):
        """Collecting statistics and store them in the statistics database.
            @keyword cached_only: `bool` Update only the cached ones if True and only if such statistics
                                  data exists in the statistics database, otherwise, update only the cached ones.
        """
        self.logger.info(f'Collecting statistics: {self}')
        data = self.db_data or {}
        data_exists = bool(data)
        for key, prop in self.dict(cached_only=cached_only and data_exists).items():
            data[key] = prop
        if data_exists:
            self.db_collection.update_one(self._query, {'$set': data})
            return
        self.db_collection.insert_one(data)

    def set_endpoint_scope(self, scope: EndpointScope):
        """Settings the endpoint scope instance directly, this is in case that we already have it and want to prevent
        it from get it via the Endpoint API.
        """
        assert isinstance(scope, EndpointScope), 'scope must be an instance of `{}`, not `{}`'.format(
            getattr(EndpointScope, '__name__'), type(scope))
        self._scope = scope

    @classmethod
    def init_by_event(cls, event):
        """Instantiating the EndpointScope by the event"""
        assert isinstance(event, Event), f'Instantiate {cls} by event required Event instance as argument, not {type(event)}'
        assert all((key in event.data) for key in cls.EndpointScope.primary_keys), \
            'Primary keys not found in event data. should be: {}'.format(cls.EndpointScope.primary_keys)
        return cls(**{k: event.data[k] for k in cls.EndpointScope.primary_keys})

    def pretty_dict(self, cached_only=True):
        pretty_dict = OrderedDict()
        for key in self.EndpointScope.primary_keys:
            pretty_dict[key] = None
        for k, v in self.dict(cached_only=cached_only).items():
            pretty_dict[k] = (getattr(self, k).prettify(v) if getattr(self, k).prettify else v)
        return pretty_dict


class StatisticsCollection(object):
    """This class provide a wrapper for a collection of statistics objects.

    It used to provide an easy access to the statistics inside the tasks by only getattr, as following:
        self.<statistics_key>.<statistic> --> value
    """

    def __init__(self, statistics_list: list):
        """
        @param statistics_list: (`list` of `Statistics`) The list of statistics object of the collection.
        """
        assert statistics_list
        assert all(issubclass(s.__class__, Statistics) for s in statistics_list)
        self._statistics_list = statistics_list

    def __getattr__(self, stats_key):
        """Fetch the statistics by key and create a wrapper the call the statistic"""
        try:
            stats = next(s for s in self._statistics_list if s.key == stats_key)
        except StopIteration:
            raise Exception(f'Could not find statistics: {stats_key}')

        class wrapper(object):
            def __getattribute__(self, stat):
                return getattr(stats, stat)()
        return wrapper()

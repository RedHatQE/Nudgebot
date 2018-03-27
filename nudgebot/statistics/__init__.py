from cached_property import cached_property
from types import MethodType

from nudgebot.base import SubclassesGetterMixin
from nudgebot.base.toggle_cached_properties import toggled_cached_property
from nudgebot.base.toggle_cached_properties import ToggledCachedProperties
from nudgebot.thirdparty.base import Party, PartyScope, Event
from nudgebot.thirdparty.github.base import Github
from nudgebot.thirdparty.github.pull_request import PullRequest
from nudgebot.thirdparty.github.repository import Repository
from nudgebot.thirdparty.github.issue import Issue
from nudgebot.db.db import DataCollection


class statistic(toggled_cached_property):
    """statistic markup"""
    def __repr__(self):
        return '<{}: {}.{}>'.format(self.__class__.__name__, self.obj, getattr(self.getter, '__name__', self.getter))
    pass


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
        def getter(*args):
            return value
        self.obj = obj
        getter.__name__ = key
        getter = MethodType(getter, obj)
        statistic.__init__(self, getter)


class Statistics(DataCollection, ToggledCachedProperties, SubclassesGetterMixin):
    """
    The Statistics class represents a bunch of statistics that related to a scope of some party.
    Once you define a Statistics class you can start to create the statistic getters which will
    be used to calculate and cache the statistics. once you call to a `statistic` object it
    calculates (i.e. run the getter), cache the returned value and return it, then, the next time you'll
    call this statistic it'll be cached, in order to un-cache you should just call <StatisticsInstance>.<stat>.uncache(),
    in order to un-cache all the statistics you can call self.uncache_all().
    In order to collect the statistics and store them in the database you can use self.collect() method.
    Should be defined in subclass:
        * Party: `Party` The Party of this Statistics.
        * PartyScope: `PartyScope` The Party of this Statistics.
        * COLLECTION_NAME: `str` The name of the collection in the statistics database.
    """
    Party = None
    PartyScope = None
    DATABASE_NAME = 'statistics'
    COLLECTION_NAME = None

    def __init__(self, **query):
        assert self.Party and isinstance(self.Party, Party)
        assert self.PartyScope and PartyScope in self.PartyScope.__mro__
        assert self.COLLECTION_NAME and isinstance(self.COLLECTION_NAME, str)
        self._query = query
        self._add_query_to_stats()

    def __repr__(self):
        return '<{} query={}>'.format(self.__class__.__name__, self._query)

    def _add_query_to_stats(self):
        """Adding the query attributes as statistic's"""
        for k, v in self._query.items():
            setattr(self, k, constant_statistic(self, k, v))

    @cached_property
    def query(self):
        return self._query

    @cached_property
    def party_scope(self):
        return self.PartyScope.init_by_keys(**self._query)

    @property
    def db_data(self):
        return self.db_collection.find_one(self._query, {'_id': False})

    def collect(self, cached_only=False):
        """Collecting statistics and store them in the statistics database.
            @keyword cached_only: `bool` Update only the cached ones if True and only if such statistics
                                  instance exists in the statistics database, otherwise, update only the cached ones.
        """
        data = self.db_data or {}
        data_exists = bool(data)
        for key, prop in self.dict(cached_only=cached_only or data_exists).items():
            data[key] = prop
        if data_exists:
            self.db_collection.update_one(self._query, {'$set', data})
            return
        self.db_collection.insert_one(data)

    @classmethod
    def from_event(cls, event):
        """Instantiating the PartyScope from the event"""
        assert isinstance(event, Event)  # TODO: Exception
        assert all((key in event.data) for key in cls.PartyScope.primary_keys)  # TODO: Exception
        return cls(**{k: event.data[k] for k in cls.PartyScope.primary_keys})


class GithubStatistics(Statistics):
    Party = Github()


class RepositoryStatistics(GithubStatistics):
    PartyScope = Repository
    COLLECTION_NAME = 'github_repository'


class IssueStatistics(GithubStatistics):
    PartyScope = Issue
    COLLECTION_NAME = 'github_issue'


class PullRequestStatistics(GithubStatistics):
    PartyScope = PullRequest
    COLLECTION_NAME = 'github_pull_request'


class ReviewersStatistics(GithubStatistics):
    PartyScope = PullRequest
    COLLECTION_NAME = 'github_reviewers'

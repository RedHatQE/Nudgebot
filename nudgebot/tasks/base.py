from datetime import datetime
import hashlib

from cached_property import cached_property

from nudgebot.base import SubclassesGetterMixin, AttributeDict
from nudgebot.log import Loggable
from nudgebot.db.db import DataCollection
from nudgebot.utils import underscored
from nudgebot.statistics.base import StatisticsCollection
from nudgebot.settings import CurrentProject


class TaskBase(Loggable, DataCollection, SubclassesGetterMixin):
    """A base class for a task"""
    Party = None
    NAME = None
    DATABASE_NAME = 'tasks'

    def __init__(self):
        Loggable.__init__(self)

    @cached_property
    def all_statistics(self):
        """Return all the statistics database as AttributeDict"""
        statistics_database = CurrentProject().db_client.statistics
        collections = [getattr(statistics_database, name) for name in statistics_database.collection_names()]
        return AttributeDict.attributize_dict({collection.name: list(collection.find()) for collection in collections})

    @cached_property
    def COLLECTION_NAME(self):
        return underscored(self.NAME)

    def run(self):
        raise NotImplementedError()


class ConditionalTask(TaskBase):
    """
    A conditional task.

    By default, the task is running once the condition is changed from False to True and the specific task[0] has not
    done in the past.
    If `RUN_ONE` is False, it'll run the task whenever the condition is True and the specific task[0] has not done in the past.
    If `ONLY_ON_CONDITION_CHANGED` is False, it'll run the task even that the specific task[0] has already done in the past.

    Vocabulary:
        [0] 'Specific task' means the task with the specific artifacts as defined in the get_artifacts function. it used to
            unify the specific case.

    Should be defined in subclass:
        * Name: `str` The name of the task.
        * Party: `Party` The Party of the task.
        * PartyScopes: (`list` of `PartyScope`) List of the party scopes that associated with this task. these party scope
                       instances will be built once the task is handled.
        * RUN_ONCE: (optional) `bool` Whether to run the task once when the condition is True.
        * ONLY_ON_CONDITION_CHANGED: (optional) `bool` run only if the condition has changed (become from False to True),
                                     default is True.
    """
    PartyScopes = None
    RUN_ONCE = True
    ONLY_ON_CONDITION_CHANGED = True

    def __init__(self, party_scopes, statistics, event=None):
        self._party_scopes = party_scopes
        self._statistics = statistics
        self._event = event
        super(ConditionalTask, self).__init__()

    def __repr__(self):
        return '<{} info={}'.format(self.NAME, self.query)

    @property
    def condition(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    @cached_property
    def _statistics_queries(self):
        """Return the statistics queries"""
        queries = {}
        for stats in self._statistics:
            queries[stats.COLLECTION_NAME] = stats.query
        return queries

    def _build_db_data(self):
        """Build the db data of the task instance"""
        self.logger.debug('Bulding task db document.')
        db_data = {}
        db_data.update(self.query)
        db_data['condition'] = False
        db_data['records'] = []
        self.db_collection.insert_one(db_data)
        return db_data

    def _add_record(self, datetime_, hash_):
        """Adding the record of the task to the task database"""
        assert isinstance(datetime_, datetime)
        assert isinstance(hash_, str)
        record = {'datetime': datetime_, 'hash': hash_, 'artifacts': self.artifacts}
        self.logger.debug(f'Adding record: {record}')
        self.db_collection.update_one(self.query, {'$addToSet': {'records': record}})

    @cached_property
    def party(self):
        return self.Party

    @cached_property
    def party_scopes(self):
        return self._party_scopes

    @cached_property
    def statistics(self):
        """Return the statistics collection of the statistics list"""
        return StatisticsCollection(self._statistics)

    @cached_property
    def event(self):
        return self._event

    @property
    def props(self):
        return {
            'party': self.party,
            'party_scopes': self.party_scopes,
            'statistics': self.statistics,
            'event': self.event
        }

    def get_artifacts(self):  # noqa
        """
        Return list of the artifacts which will be used to unify this task.

        This used to distinguish the particular task instance from the others,
        since the statistics could be changed.

        @note: Optional to overwrite, default is no artifacts (empty list).
        @note: _all_ the artifacts should be of type `str`.
        """
        return []

    @cached_property
    def artifacts(self):
        artifacts = self.get_artifacts()
        assert all(isinstance(prop, str) for prop in artifacts), \
            ('All task artifacts should be of type `str`. '
             'please check that you have overwrite correctly the `get_artifacts` method')
        return artifacts

    @cached_property
    def query(self):
        """Return the query of the task in the database"""
        return {
            'name': self.NAME,
            'statistics_queries': self._statistics_queries
        }

    @property
    def db_data(self):
        db_data = self.db_collection.find_one(self.query, {'_id': False})
        if not db_data:
            db_data = self._build_db_data()
        return db_data

    @property
    def hash(self):
        """Return the unique hash of the task"""
        hash_properties = self.artifacts
        return hashlib.md5(','.join(hash_properties).encode()).hexdigest()

    @property
    def is_done_in_the_past(self):
        """Return whether this task has been done in the past by hash"""
        return any(self.hash == rec['hash'] for rec in self.records)

    @property
    def records(self):
        """Return the task records in the databse"""
        return self.db_data['records']

    def handle(self):
        """
        Handle the task.

        Evaluating the condition, if the condition is True it's running the task as long as `RUN_ONCE` is False,
        if `ONLY_ON_CONDITION_CHANGED` is True it'll run only if the condition changed from False to True.
        After task has run, we store its record in the databse and we uncache the statistics and collect them again,
        that because the task could affect them.
        """
        db_data = self.db_data
        self.logger.info(f'Checking task condition: {self}')
        condition = self.condition
        self.logger.info(f'Condition is {condition}')
        condition_changed = (False if not self.ONLY_ON_CONDITION_CHANGED else db_data['condition'] != condition)
        if condition and (not self.RUN_ONCE or (condition_changed and not self.is_done_in_the_past)):  # False --> True
            self.logger.info(f'Running task: {self}')
            self.run()
            self._add_record(datetime.utcnow(), self.hash)
            self.logger.debug('Run done.')
            # recollecting all the statistics
            self.logger.info('Recollecting statistics after task run.')
            for stats in self._statistics:
                stats.uncache_all()
                stats.collect()
        db_data['condition'] = condition
        self.db_collection.update_one(self.query, {'$set': db_data})


class PeriodicTask(TaskBase):
    """
    A periodic task.

    A periodic task is running as a crontab task.
    Each time the crontab is triggering the task, ALL the statistics are being collected from the statistics database
    and passed as AttributeDict into the `run` function. each statistics is plural and that means that for
    each statistics key we get all the instances, i.e.
        statistics.<statistics_key>[<index>].<statistic>

    Should be defined in subclass:
        * Name: `str` The name of the task.
        * CRONTAB: `celery.schedule.crontab` The crontab of the periodic task.
    """
    CRONTAB = None

    def run(self):
        raise NotImplementedError()

    def handle(self):
        self.logger.info(f'Running periodic task: {self.NAME}')
        self.run()

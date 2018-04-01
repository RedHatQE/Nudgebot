"""
The bot package.

Include the Bot class and its functionality.

"""

import time
from threading import Lock

from wait_for import wait_for

from nudgebot.thirdparty.github.events import GithubEventsFactory
from nudgebot.log import Loggable
from nudgebot.tasks.base import ConditionalTask
from nudgebot.thirdparty.github.base import GithubScope


class Bot(Loggable):
    """The Bot is the main bridge, is used to receive new events, collect the statistics, trigger the tasks and the reports."""

    EventFactories = (
        GithubEventsFactory(),
    )
    UpdateEvery = 10  # Run update() every X seconds

    def __init__(self, statistics: list, tasks: list):
        """Instantiate.

        @param statstics: (`list` of `Statistics`) The Statistics that the bot collects.
        @param tasks: (`list` of `Task`) The Tasks that the bot perform or evaluates.
        @param reports: (`reports` of `Report`) The Reports that the bot sends.

        """
        Loggable.__init__(self)
        self._statistics = statistics
        self._tasks = tasks
        self._busy_mutext = Lock()

    def get_conditional_tasks(self, party_scope=None):
        conditional_tasks = [task for task in self._tasks if issubclass(task, ConditionalTask)]
        if party_scope:
            conditional_tasks = [task for task in conditional_tasks
                                 if set(party_scope.get_hierarchy_classes()) == set(task.PartyScopes)]
        return conditional_tasks

    def full_sync(self):
        """Performing a full sync, collect statistics from all the scopes and handling the tasks."""
        self._busy_mutext.acquire()
        try:
            self.logger.info('Stating full sync')
            for github_scope in GithubScope.get_subclasses():
                for obj in github_scope.all():
                    stats_collection = []
                    for stat_class in self._statistics:
                        for parent in obj.hierarchy:
                            if stat_class.PartyScope == parent.__class__:
                                statistics = stat_class(**parent.query)  # TODO: Init from scope
                                statistics.set_party_scope(parent)
                                self.logger.info(f'Collecting statistics: {statistics}')
                                statistics.collect()
                                stats_collection.append(statistics)
                    for task_cls in self.get_conditional_tasks(github_scope):
                        party_scopes = {ps.__class__: ps for ps in list(set([s.party_scope for s in stats_collection]))}
                        task = task_cls(party_scopes, stats_collection)
                        task.handle()

            self.logger.info('Finished full sync')

        finally:
            self._busy_mutext.release()

    def update(self):
        """Update."""
        # TODO: Full docstring
        self._busy_mutext.acquire()
        try:
            for event_factory in self.EventFactories:
                event = event_factory.pull_event()
                while event:
                    self.logger.info('Handling new event: {}'.format(event.id))
                    stat_collection = []
                    for statistics_cls in self._statistics:
                        if statistics_cls.Party == event.party and statistics_cls.PartyScope in event.PartyScopes:
                            statistics = statistics_cls.init_by_event(event)
                            self.logger.info(f'Collecting statistics: {statistics}')
                            stat_collection.append(statistics)
                            statistics.collect()
                    self.logger.info('Checking for tasks to run')
                    for task_cls in self._tasks:
                        if issubclass(task_cls, ConditionalTask) and event.PartyScopes == task_cls.PartyScopes:
                            statistics = []
                            for stats in stat_collection:
                                if stats.Party == task_cls.Party and stats.PartyScope in task_cls.PartyScopes:
                                    statistics.append(stats)
                            party_scopes = {ps.__class__: ps for ps in list(set([s.party_scope for s in statistics]))}
                            task = task_cls(party_scopes, statistics, event)
                            task.handle()
                    event = event_factory.pull_event()
        finally:
            self._busy_mutext.release()

    def run(self):
        """Run the bot."""
        for event_factory in self.EventFactories:
            event_factory.start()
        while True:
            update_start_time = time.time()
            self.update()
            wait_for(lambda: time.time() - update_start_time > self.UpdateEvery and not self._busy_mutext.locked(),
                     logger=self.logger, message='Waiting for update timeout to finish.')

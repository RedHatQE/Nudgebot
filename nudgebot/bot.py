"""
The bot package.

Include the Bot class and its functionality.

"""

import time

from nudgebot.thirdparty.github.events import GithubEventsFactory
from nudgebot.settings import CurrnetProject


class Bot(object):
    """The Bot is the main bridge, is used to receive new events, collect the statistics, trigger the tasks and the reports."""

    EventFactories = (
        GithubEventsFactory,
    )
    UpdateEvery = CurrnetProject().config.config.events.check_every

    def __init__(self, statistics: list, tasks: list, reports: list):
        """Instantiate.

        @param statstics: (`list` of `Statistics`) The Statistics that the bot collects.
        @param tasks: (`list` of `Task`) The Tasks that the bot perform or evaluates.
        @param reports: (`reports` of `Report`) The Reports that the bot sends.

        """
        self._statistics = statistics
        self._tasks = tasks
        self._reports = reports

    def full_sync(self):
        """Doing a full sync, collect statistics from all the scopes."""
        pass  # TODO: Implement and improve docstring

    def update(self):
        """Update."""
        # TODO: Full docstring
        for event_factory in self.EventFactories:
            for event in event_factory().get_new_events():
                stat_collection = []
                for statistics_cls in self._statistics:
                    if statistics_cls.Party == event.Party and statistics_cls.PartyScopes in event.PartyScopes:
                        statistics = statistics_cls.from_event(event)
                        stat_collection.append(statistics)
                        statistics.collect()
                for task in self._tasks:
                    task  # do task with stat if it conditional and the condition passes
                for report in self._reports:
                    report  # send report with stat if it conditional and the condition passes

    def run(self):
        """Run the bot."""
        while True:
            update_start_time = time.time()
            self.update()
            while time.time() - update_start_time < self.UpdateEvery:
                time.sleep(1)

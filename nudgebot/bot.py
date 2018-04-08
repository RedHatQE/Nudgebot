"""
The bot package.

Include the Bot class and its functionality.

"""
import time

from nudgebot.log import Loggable
from nudgebot.thirdparty.github.bot import GithubBot
from nudgebot.thirdparty.irc.bot import IRCbot
from nudgebot.exceptions import SubThreadException


class Bot(Loggable):

    def __init__(self, statistics: list, tasks: list):
        """Instantiate.

        @param statstics: (`list` of `Statistics`) The Statistics that the bot collects.
        @param tasks: (`list` of `Task`) The Tasks that the bot perform or evaluates.

        """
        Loggable.__init__(self)
        self._statistics = statistics
        self._tasks = tasks
        self._slaves = []
        for slave_cls in (GithubBot, IRCbot):
            slave_stats = [stats for stats in statistics if stats.Party == slave_cls.Party]
            slave_tasks = [task for task in tasks if task.Party == slave_cls.Party]
            slave = slave_cls(slave_stats, slave_tasks)
            self._slaves.append(slave)

    def mainloop(self):
        """
        Run the bot's mainloop.
        """
        # Starting slaves
        for slave in self._slaves:
            slave.start()
        #
        while True:
            if not slave.isAlive():
                self.logger.error('Bot slave died.')
                raise SubThreadException(slave)
            time.sleep(5)

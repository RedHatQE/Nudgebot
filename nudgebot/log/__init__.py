import logging

from nudgebot.settings import CurrentProject


class Loggable(object):
    """Provides a logger attribute for logging to the subclass"""
    def __init__(self):
        logging.basicConfig(format='%(name)s %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(
            getattr(logging, CurrentProject().config.config.logging_level.upper())
        )

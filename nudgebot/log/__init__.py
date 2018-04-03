import logging

from nudgebot.settings import CurrentProject


class Loggable(object):
    """Provides a logger attribute for logging to the subclass"""
    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(
            getattr(logging, CurrentProject().config.config.logging_level.upper()) if CurrentProject()
            else logging.INFO
        )

import logging

from nudgebot.settings import CurrnetProject


class Loggable(object):
    """Provides a logger attribute for logging to the subclass"""
    # TODO: Use this
    def __init_subclass__(cls):  # @NoSelf
        """Setting the logger to the inherit class"""
        logging.basicConfig()
        logger = getattr(cls, 'logger', None) or logging.getLogger('MainLogger')
        logger.setLevel(getattr(logging, CurrnetProject().config.logging_level.upper()))
        cls.logger = logger

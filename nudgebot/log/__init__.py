import logging

from nudgebot.settings import CURRENT_PROJECT


logging.basicConfig()
main_logger = logging.getLogger('MainLogger')
main_logger.setLevel(getattr(logging, CURRENT_PROJECT.config.logging_level.upper()))

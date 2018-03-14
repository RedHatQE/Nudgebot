import os
import sys

from nudgebot import settings


DIR = os.path.dirname(__file__)
settings.CURRENT_PROJECT = sys.modules[__name__]

from .config import config  # noqa

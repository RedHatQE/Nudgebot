import os
import sys

from nudgebot import settings


DIR = os.path.dirname(__file__)
settings.CurrentProject().setup(sys.modules[__name__])

# The following imports must be AFTER project setting
from config import config
from nudgebot.db import DatabaseClient

db_client = DatabaseClient()

from nudgebot.bot import Bot

from nudgebot.statistics import collect_statistics_classes
from nudgebot.tasks import collect_task_classes

from nudgebot.celery_runner import CeleryRunner

import statistics
import tasks


STATISTICS = collect_statistics_classes(statistics)
TASKS = collect_task_classes(tasks)

celery_runner = CeleryRunner()
bot = Bot(STATISTICS, TASKS)


__all__ = [
    'db_client',
    'STATISTICS',
    'TASKS',
    'celery_runner',
    'bot',
]

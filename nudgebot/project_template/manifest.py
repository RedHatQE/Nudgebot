from nudgebot.statistics import Statistics
from nudgebot.reports import Report
from nudgebot.tasks import Task

from . import statistics
from . import reports
from . import tasks


STATISTICS = Statistics.collect(statistics)
TASKS = Report.collect(reports)
REPORTS = Task.collect(tasks)

STATISTICS.extend([
    # List your statistics classes here
])

TASKS.extend([
    # List your task classes here
])

REPORTS.extend([
    # List your report classes here
])

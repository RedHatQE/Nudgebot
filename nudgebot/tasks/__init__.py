from functools import partial

from nudgebot.utils import collect_subclasses
from nudgebot.tasks.base import TaskBase
from . import base
from .base import ConditionalTask, PeriodicTask  # noqa

collect_task_classes = partial(collect_subclasses, cls=TaskBase, exclude=collect_subclasses(base, TaskBase))

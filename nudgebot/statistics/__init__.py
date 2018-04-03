from functools import partial

from nudgebot.utils import collect_subclasses
from .base import Statistics
from . import github


collect_statistics_classes = partial(collect_subclasses, cls=Statistics, exclude=collect_subclasses(github, Statistics))

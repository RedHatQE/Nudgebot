import time
from datetime import datetime

import pytest

from nudgebot.base.toggle_cached_properties import ToggledCachedProperties, toggled_cached_property


def test_toggle_cached_properties():
    """Testing the ToggledCachedProperties and toggled_cached_property"""
    class Times(ToggledCachedProperties):
        @property
        def local_time(self):
            return datetime.now()

        @toggled_cached_property
        def first_call(self):
            return self.local_time

    T = Times()
    for _ in range(3):
        fc = T.first_call()
        for _ in range(3):
            time.sleep(1)
            fc1 = T.first_call()
            assert fc == fc1
            fc = fc1
        T.first_call.uncache()
        assert fc != T.first_call()
        fc = T.first_call()
        T.first_call.uncache()


def test_wrong_class():
    """Testing that there is an assertion error when we inherit class that is not ToggledCachedProperties
    and decorating a toggled_cached_property"""
    class Times(object):  # Check this out - Times is `object`
        @property
        def local_time(self):
            return datetime.now()

        @toggled_cached_property
        def first_call(self):
            return self.local_time

    with pytest.raises(AssertionError):
        Times().first_call()

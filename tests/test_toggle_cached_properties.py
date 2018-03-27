import time
from datetime import datetime

from nudgebot.base.toggle_cached_properties import ToggledCachedProperties, toggled_cached_property


def test_toggled_cached_property():
    """Testing toggled_cached_property only"""
    class Times(object):
        @property
        def local_time(self):
            return datetime.now()

        @toggled_cached_property
        def first_call(self):
            t = self.local_time
            print(t)
            return t

    T = Times()
    for _ in range(3):
        fc = T.first_call()
        for _ in range(3):
            time.sleep(0.1)
            fc1 = T.first_call()
            assert fc == fc1
            fc = fc1


def test_toggled_cached_properties():
    """Testing the ToggledCachedProperties and toggled_cached_property"""
    class Times(ToggledCachedProperties):
        @property
        def local_time(self):
            return datetime.now()

        @toggled_cached_property
        def first_call(self):
            t = self.local_time
            print(t)
            return t

    T = Times()
    for _ in range(3):
        fc = T.first_call()
        for _ in range(3):
            time.sleep(0.1)
            fc1 = T.first_call()
            assert fc == fc1
            fc = fc1
        T.first_call.uncache()
        assert fc != T.first_call()
        fc = T.first_call()
        time.sleep(0.1)
        assert fc == T.first_call()
        T.uncache_all()
        assert fc != T.first_call()


def test_toggled_cached_properties_dict():
    """Testing the dict() function in ToggledCachedProperties"""
    # TODO: Fixturize Times (DRY)
    class Times(ToggledCachedProperties):
        @property
        def local_time(self):
            return datetime.now()

        @toggled_cached_property
        def first_call(self):
            t = self.local_time
            print(t)
            return t

    T = Times()
    assert 'first_call' not in T.dict(cached_only=True)
    T.first_call()
    assert 'first_call' in T.dict(cached_only=True)
    T.uncache_all()
    assert 'first_call' in T.dict()
    T.uncache_all()
    assert 'first_call' not in T.dict(cached_only=True)

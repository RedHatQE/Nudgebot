from nudgebot.base import AttributeDict


class toggled_cached_property(object):
    """A decorator for toggled cached property."""
    def __init__(self, getter):
        self.__doc__ = getattr(getter, '__doc__')
        self.getter = getter

    def uncache(self):
        """Un-cache the property"""
        if self.getter.__name__ in self.obj:
            del self.obj[self.getter.__name__]

    def __get__(self, obj, cls):
        assert isinstance(obj, ToggledCachedProperties), \
            'toggled_cached_property "{}" must be an attribute of {}'.format(
                self.getter.__name__, ToggledCachedProperties)
        self.obj = obj
        return self

    def __call__(self):
        if self.getter.__name__ in self.obj:
            return self.obj[self.getter.__name__]
        value = self.obj[self.getter.__name__] = self.getter(self.obj)
        return value


class ToggledCachedProperties(AttributeDict):
    """"""

    def uncache_all(self):
        """Un-cache all properties"""
        for k in self.keys():
            # Please do not iterate over self since it causes:
            # RuntimeError: dictionary changed size during iteration
            del self[k]

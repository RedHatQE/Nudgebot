class toggled_cached_property(object):
    """
    A decorator for toggled cached property. Toggled cached property provides the ability to cache and un-cache
    properties.
    Example:
        >>> import time
        >>> class Times(object):
                @property
                def local_time(self):
                    return datetime.now()

                @toggled_cached_property
                def first_call(self):
                    time.sleep(1)
                    t = self.local_time
                    return t
        >>> t = Times()
        >>> t.first_call()
        2018-03-27 22:12:52.464317
        >>> t.first_call()
        2018-03-27 22:12:52.464317      # The value is the same after ~1 second
        >>> t.first_call.uncache()      # un-caching the property
        >>> t.first_call()              # now the value is different (~2 seconds later)
        2018-03-27 22:12:53.668292
    """
    def __init__(self, getter):
        self.__doc__ = getattr(getter, '__doc__')
        self.getter = getter

    def uncache(self):
        """Un-cache the property"""
        if self.getter.__name__ in self.obj._toggled_cached_properties:
            del self.obj._toggled_cached_properties[self.getter.__name__]

    def __get__(self, obj, cls):
        self.obj = obj
        if not hasattr(self.obj, '_toggled_cached_properties'):
            self.obj._toggled_cached_properties = {}
        return self

    def __call__(self):
        if self.getter.__name__ in self.obj._toggled_cached_properties:
            return self.obj._toggled_cached_properties[self.getter.__name__]
        value = self.obj._toggled_cached_properties[self.getter.__name__] = self.getter(self.obj)
        return value


class ToggledCachedProperties(object):
    """Object that contains `toggled_cached_property` objects and provide utility functions"""

    def __iter__(self):
        return self.dict()

    def initialize_cache_dict_if_not_exists(self):
        """Initializing the _toggled_cached_properties if it doesn't already exists.
        """
        if not hasattr(self, '_toggled_cached_properties'):
            self._toggled_cached_properties = {}

    def dict(self, cached_only=False):
        """Returns a dictionary representation of all the ToggledCachedProperties
            @keyword cached_only: `bool` Whether to get only the cached ones or get all.
        """
        out = {}
        self.initialize_cache_dict_if_not_exists()
        keys = (self._toggled_cached_properties.keys() if cached_only else dir(self))
        for k in keys:
            val = (getattr(self, k) if k != 'dict' else None)
            if isinstance(val, ToggledCachedProperties):
                out[k] = ToggledCachedProperties.dict(val)
                continue
            elif isinstance(val, toggled_cached_property):
                out[k] = val()
        return out

    def uncache_all(self):
        """Un-cache all properties"""
        self.initialize_cache_dict_if_not_exists()
        for k in list(self._toggled_cached_properties.keys()):
            del self._toggled_cached_properties[k]

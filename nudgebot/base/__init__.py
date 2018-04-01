from abc import ABCMeta

from enum import Enum


class ExtendedEnum(Enum):
    """An extension for the native enum.Enum"""
    @classmethod
    def values(cls):
        return [field.value for field in cls]

    @classmethod
    def get_by_value(cls, value):
        for field in cls:
            if field.value == value:
                return field
        raise ValueError('Could not find value "{}" in enum[{}]'.format(value, cls.values()))


class Singleton(type):
    """Singleton class"""
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]


class ABCMetaSingleton(ABCMeta, Singleton):
    """A both ABCMeta and Singleton class"""
    pass


class AttributeDict(dict):
    """A dict object that provides the ability to to set/get items as attributes"""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    @classmethod
    def attributize_dict(cls, obj):
        if isinstance(obj, dict):
            attr_dict = cls()
            for key, value in obj.items():
                attr_dict[key] = cls.attributize_dict(value)
            return attr_dict
        elif isinstance(obj, (list, tuple)):
            nested_list = list()
            for value in obj:
                nested_list.append(cls.attributize_dict(value))
            return nested_list
        return obj


class SubclassesGetterMixin(object):
    """Includes a subclasses getter for the inherit class and collector"""
    @classmethod
    def get_subclasses(cls):
        """Getting the subclasses of the class"""
        return cls.__subclasses__()

    @classmethod
    def collect(cls, *modules):
        """Collect all subclasses of the class in the given modules.
        _IMPORTANT_: This could be very slow operation in case that some properties take time to get.
        """
        subclasses = []
        for module in modules:
            attr_names = dir(module)
            for attr_name in attr_names:
                attr = getattr(module, attr_name)
                if cls in getattr(attr, '__mro__', []):
                    subclasses.append(attr)
        return subclasses

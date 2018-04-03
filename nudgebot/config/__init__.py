import os
import yaml

from nudgebot.base import AttributeDict
from nudgebot.exceptions import (MissingConfigurationFileException,
                                 MissingConfigurationAttributeException)


class Config(object):
    """The Config object contains all the config data that found in the configfiles() as `dict`"""
    CONFIG_NAMES = ('config', 'credentials', 'users')

    @classmethod
    def configfiles(cls):
        return [f'{f}.yaml' for f in cls.CONFIG_NAMES]

    @classmethod
    def configtemplates(cls):
        return [f'{f}.template.yaml' for f in cls.CONFIG_NAMES]

    def __init__(self, dirpath):
        """
        @param dirpath: `str` the path of the config directory.
        """
        self.dirpath = dirpath
        self._data = AttributeDict()
        self._first_reload_done = False

    def reload(self):
        self._first_reload_done = True
        for p in self.configfiles():
            conf_name = os.path.splitext(p)[0]
            fp = os.path.join(self.dirpath, p)
            if not os.path.exists(fp):
                raise MissingConfigurationFileException(fp)
            with open(fp, 'r') as confile:
                self._data[conf_name] = AttributeDict.attributize_dict(yaml.load(confile))

    def __getitem__(self, key):
        if not super(Config, self).__getattribute__('_first_reload_done'):
            super(Config, self).__getattribute__('reload')()
        try:
            return self._data[key]
        except KeyError:
            raise MissingConfigurationAttributeException(key)

    def __getattribute__(self, name):
        if not super(Config, self).__getattribute__('_first_reload_done'):
            super(Config, self).__getattribute__('reload')()
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.__getitem__(name)

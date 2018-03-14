import os
import yaml

from nudgebot.base import AttributeDict
from nudgebot.exceptions import MissingConfigurationFileException


class Config(object):
    """The Config object contains all the config data that found in the CONFIG_FILES as `dist`"""
    CONFIG_FILES = ('config.yaml', 'credentials.yaml')

    def __init__(self, dirpath):
        """
        @param dirpath: `str` the path of the config directory.
        """
        self.dirpath = dirpath

    def reload(self):
        self._data = AttributeDict()
        for p in self.CONFIG_FILES:
            conf_name = os.path.splitext(p)[0]
            fp = os.path.join(self.dirpath, p)
            if not os.path.exists(fp):
                raise MissingConfigurationFileException(fp)
            with open(fp, 'r') as confile:
                self._data[conf_name] = AttributeDict.attributize_dict(yaml.load(confile))

    def __getitem__(self, key):
        return self._data[key]

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.__getitem__(name)

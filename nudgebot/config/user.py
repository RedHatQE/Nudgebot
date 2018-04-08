from hashlib import md5

from cached_property import cached_property

from nudgebot.settings import CurrentProject
from nudgebot.exceptions import CouldNotFindUserException
from nudgebot.utils import flatten_dict


class User(object):
    """
    Represents a user in the organization.

    The class contains all the user info and helper functions for users management.
    """

    CONFIG_DATA = CurrentProject().config.users

    def __init__(self, key: str):
        assert isinstance(key, str)
        self._key = key
        self.config_data  # Just to raise exception of no such key found

    def __repr__(self):
        f'<{self.__class__.__name__} key={self._key}>'

    def __hash__(self):
        return md5(','.join([f'{k}:{v}' for k, v in flatten_dict(self.config_data).items()]))

    @classmethod
    def _user_keys(cls):
        return [u.key for u in cls.CONFIG_DATA]

    @classmethod
    def all(cls):
        """
        Get all users

        @rtype: `list` of `User`.
        """
        return [cls(key) for key in cls._user_keys()]

    @classmethod
    def get_user(cls, **query):
        """
        Get a user by specific query

        @param query: The query, keys and values.
        @rtype: `None` if user found, otherwise `User`.
        """
        assert isinstance(query, dict)
        for user in cls.all():
            if all(user.config_data.get(k) == v for k, v in query.items()):
                return user

    @cached_property
    def config_data(self):
        """
        Return the configuration data of the user.

        @rtype: `AttributeDict`
        """
        if self._key not in self._user_keys():
            raise CouldNotFindUserException(self._key, self._user_keys())
        return next(data for data in self.CONFIG_DATA if data.key == self._key)

    @cached_property
    def github(self):
        """
        Return the github user object of the user

        @rtype: `nudgebot.thirdparty.github.user.User`
        """
        from nudgebot.thirdparty.github.user import User
        return User.instantiate(self.config_data.github_login)

    @property
    def irc_nick(self):
        """
        @rtype: `str`
        """
        return self.config_data.irc_nick

    @property
    def email(self):
        """
        @rtype: `str`
        """
        return self.config_data.email

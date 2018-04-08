from cached_property import cached_property
from github.NamedUser import NamedUser

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import PartyScope


class User(PyGithubObjectWrapper, PartyScope):
    PyGithubClass = NamedUser
    primary_keys = ['login']

    @classmethod
    def instantiate(cls, login):
        return cls(cls.Party.client.get_user(login))

    @classmethod
    def init_by_keys(cls, **query):
        return cls.instantiate(query.get('login') or query.get('organization'))

    @cached_property
    def query(self)->dict:
        return {'login': self.login}

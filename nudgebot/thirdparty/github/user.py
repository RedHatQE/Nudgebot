from github.NamedUser import NamedUser

from nudgebot.thirdparty.github.base import PyGithubObjectWrapper
from nudgebot.thirdparty.base import APIclass


class User(PyGithubObjectWrapper, APIclass):
    PyGithubClass = NamedUser

    @classmethod
    def instantiate(cls, login):
        return cls(cls.Party.client.get_user(login))

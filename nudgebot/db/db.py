import pprint

from pymongo import MongoClient

from bson import _ENCODERS as bson_encoders
from nudgebot.settings import CurrentProject


class DatabaseClient(MongoClient):  # noqa
    """A Database client for MongoDB"""
    bson_types = tuple(bson_encoders.keys())
    HOST = CurrentProject().config.config.database.mongo_client.host
    PORT = CurrentProject().config.config.database.mongo_client.port

    def __init__(
            self,
            host=None,
            port=None,
            document_class=dict,
            tz_aware=None,
            connect=None,
            **kwargs):
        MongoClient.__init__(self, host=host, port=port, document_class=document_class,
                             tz_aware=tz_aware, connect=connect, **kwargs)

    @classmethod
    def bson_encode(cls, node):
        """Verifying that all the objects in the dict node are bson encodable.
        Those that are not converted to an `str`.
            @param node: Either a node of the json tree or a value.
        """
        if isinstance(node, dict):
            result = {}
            for key, value in node.items():
                result[key] = cls.bson_encode(value)
        elif isinstance(node, (list, tuple)):
            result = []
            for item in node:
                result.append(cls.bson_encode(item))
        elif isinstance(node, cls.bson_types):
            result = node
        else:
            result = str(node)
        return result

    def dump(self, databasename, collection_name=None, query=None, filepath=None, dismiss_id=True):
        """Dumping the database content.
            @param databasename: `str` The name of the database to dump.
            @keyword collection_name: `str` filter by collection name to dump a specific collection.
            @keyword query: `dict` filter by a query in the collection.
            @keyword filepath: `str` The path of the file to dump.
            @keyword dismiss_id: `bool` Whether to dismiss the '_id' property.
        """
        assert isinstance(databasename, str)
        assert collection_name is None or isinstance(collection_name, str)
        assert query is None or isinstance(query, dict)
        assert filepath is None or isinstance(filepath, str)
        db = getattr(self, databasename)
        if collection_name:
            collections = [getattr(db, collection_name)]
        else:
            collections = [getattr(db, name) for name in db.collection_names()]
        data = {}
        for collection in collections:
            dismiss_id = {'_id': False} if dismiss_id else {}
            data[collection.name] = list(collection.find(query, dismiss_id))
        if filepath:
            with open(filepath, 'w') as f:
                f.write(pprint.pformat(data, width=20) + '\n')
        return data

    def clear_db(self, i_really_want_to_do_this=False):
        """Clearing all the database content. This is unrevertable danger operation.
            @param i_really_want_to_do_this: `bool` Whether I really want to perform this operation.
                if false - it'll raise exception.
        """
        if not i_really_want_to_do_this:
            raise Exception('You are performing a really danger operation. if you really want to do this - '
                            'please call clear_db(i_really_want_to_do_this=True).')
        for dbname in self.database_names():
            if dbname not in ('local', 'admin'):
                self.drop_database(dbname)


class DataCollection(object):
    """
    Define the inherit class as data collection and provides access into it
    Should be defined in subclass:
        * DATABSE_NAME: `str` The name of the database.
        * COLLECTION_NAME: `str` The name of the COLLECTION_NAME in that database.
    """
    DATABASE_NAME = None
    COLLECTION_NAME = None

    def upsert(self, query: dict, update: dict):
        """Update a document with the matched query, if no such document, insert.
            @see: https://docs.mongodb.com/manual/reference/method/db.collection.update/#upsert-option
        """
        return self.db_collection.update(query, update, {'upsert': True})

    @property
    def db_collection(self):
        """Returns the database collection"""
        assert self.DATABASE_NAME is not None
        assert self.COLLECTION_NAME is not None
        db = getattr(CurrentProject().db_client, self.DATABASE_NAME)
        return getattr(db, self.COLLECTION_NAME)


class CachedStack(DataCollection):
    """
    A cached LIFO stack that cache itself in the database.
    """
    DATABASE_NAME = 'metadata'
    COLLECTION_NAME = 'cached_stacks'

    def __init__(self, name: str, length: int = 1000):
        """
        @param name: `str` The name of the cached stack.
        @keyword  length: `int` the length of the cached stack. if length = -1: length is unlimited.
        """
        self._i = 0
        self._name = name
        self._length = length
        self._length_exeeded = False
        self.stack or self.db_collection.insert_one({'name': self._name, 'stack': []})

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.stack)

    def __eq__(self, other):
        return self.stack == getattr(other, 'stack', None)

    def __getitem__(self, index):
        return self.stack[index]

    def __contains__(self, item):
        return item in self.stack

    def __len__(self):
        return len(self.stack)

    @property
    def stack(self):
        """Returns the stack."""
        doc = self.db_collection.find_one({'name': self._name}, {'_id': False})
        if doc:
            return doc['stack']
        return []

    @property
    def length_exeeded(self):
        """
        Checking whether the length exceeded. once it exceeded, it continue to be exceeded.
        That in order to reduce DB calls."""
        if not self._length_exeeded:
            self._length_exeeded = (False if self._length == -1 else self._length <= len(self.stack))
        return self._length_exeeded

    def pop(self):
        """Pop the first item"""
        return self.db_collection.update_one({'name': self._name}, {'$pop': {'stack': -1}})

    def push(self, item):
        """
        Push a new item to the stack, pop the first.
            @param item: The item to push."""
        if self.length_exeeded:
            self.pop()
        self.db_collection.update_one({'name': self._name}, {'$addToSet': {'stack': item}})

    def clear(self):
        """Clearing the stack"""
        while self.stack:
            self.pop()

import collections

import os
import smtplib
import logging
from threading import Timer
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate


def send_email(from_address, receivers, subject, body, attachments=None, text_format='plain', logger=None):
    """Sending an email from <from_address> to the <receivers> with the provided <subject> and <body>
        @param from_address: `str` The address from which the email is being sent.
        @param receivers: (`list` of `str`) A list of the email addresses of the receivers.
        @param subject: `str` The subject of the email.
        @param body: `str` The body of the email.
        @keyword attachments: (`list` of `str`) A list of paths to files to be attached.
        @keyword text_format: `str` The email text format, could be either 'plain' or 'html'
        @keyword logger: `logging.Logger` The logger to use.
    """
    # Validate params:
    assert isinstance(from_address, str)
    assert isinstance(receivers, (list, tuple))
    assert isinstance(subject, str)
    assert isinstance(body, str)
    assert isinstance(attachments, (type(None), list, tuple))
    if attachments:
        for attach in attachments:
            assert isinstance(attach, str), 'All attachments should be strings'
            assert os.path.exists(attach), 'No such file: "{}"'.format(attach)
    assert isinstance(text_format, str)
    text_format = text_format.lower()  # Insensitive
    assert text_format in ('plain', 'html')
    assert isinstance(logger, (logging.Logger, type(None)))
    # -
    logger = logger or logging
    logger.info('Sending Email from {} to {}; subject="{}"'.format(from_address, receivers, subject))

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = COMMASPACE.join(receivers)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, text_format))
    if attachments:
        for attachment in attachments:
            with open(attachment, "rb") as attachment_file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_file.raw_read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= {}"
                                .format(attachment))
                msg.attach(part)

    smtp_server = smtplib.SMTP('localhost')
    smtp_server.sendmail(from_address, receivers, msg.as_string())


def from_camel(string: str) -> str:
    """Converting a CamelCase string to non_camel_case"""
    assert isinstance(string, str), 'string must be a type of `str`'
    out = ''
    for i, c in enumerate(string):
        addition = c.lower()
        if c.isupper():
            if i != 0:
                addition = '_' + addition
        out += addition
    return out


def underscored(string):
    """Convert string from 'string with whitespaces' to 'string_with_whitespaces'"""
    assert isinstance(string, str)
    return string.replace(' ', '_')


def collect_subclasses(mod, cls, exclude=None):
    """Collecting all subclasses of `cls` in the module `mod`

    @param mod: `ModuleType` The module to collect from.
    @param cls: `type` or (`list` of `type`) The parent class(es).
    @keyword exclude: (`list` of `type`) Classes to not include.
    """
    out = []
    for name in dir(mod):
        attr = getattr(mod, name)
        if (
                isinstance(attr, type) and
                (attr not in cls if isinstance(cls, (list, tuple)) else attr != cls) and
                issubclass(attr, cls) and
                (attr not in exclude if exclude else True)):
            out.append(attr)
    return out


class RunEvery(object):
    """
    A thread that runs a callback every interval seconds.
    """
    def __init__(self, interval, callback, args=None, kwargs=None):
        """
        @param inteval: `int` Number of seconds among executions.
        @param callback: A callable callback to call every interval seconds.
        @keyword args: `tuple` The arguments of the callback function.
        @keyword kwargs: `dict` The keyword arguments of the callback function.
        """
        self.interval = interval
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.thread = Timer(self.interval, self.handle_callback, self.args, self.kwargs)

    def handle_callback(self, *args, **kwargs):
        self.callback(*args, **kwargs)
        self.thread = Timer(self.interval, self.handle_callback, args, kwargs)
        self.thread.start()

    def start(self, run_first=False):
        """
        @param run_first: `bool` Whether to first run the callback and then start the timer.
        """
        if run_first:
            self.callback(*(self.args or tuple()), **(self.kwargs or {}))
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten a dictionary to one dict

    @param d: `dict` The dictionary to flat.
    @keyword parent_key: `str` The parent key.
    @keyword sep: `str` The separator that will be used to redefine the key.
    @rtype: `dict`
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def getnode(iterable, keys_vector: tuple):
    """
    Trying to get a specific node in a dict. It's like dict.get but recursive.
    Example:
        >>> mydict = {'a': 1, 'b': {'c': 2}, 'c': 3, 'd': None}
        >>> mylist = [1, [2, 3], 4]
        >>> getnode(mydict, ['a'])
        1
        >>> getnode(mydict, ['b', 'c'])
        2
        >>> getnode(mylist, [1, 1])
        3

    @param iterable: (`dict` or `list` or `tuple` or any iterable object) The object to perform the node get.
    @param keys_vector: (`list` or `tuple`) The keys vector (actually the path of the node).

    """
    assert isinstance(iterable, collections.Iterable), f'iterable argument must be an iterable object!, got {type(iterable)}'
    assert isinstance(keys_vector, (list, tuple)), 'keys_vector argument must be a list or a tuple!'

    current_node = iterable
    for key in keys_vector:
        if isinstance(current_node, collections.MutableMapping):
            current_node = current_node.get(key, None)
            if not current_node:
                return
        elif isinstance(current_node, collections.Sequence) and isinstance(key, int):
            try:
                current_node = current_node[key]
            except IndexError:
                return
        else:
            return

    return current_node

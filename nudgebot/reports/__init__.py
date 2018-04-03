import os

from celery.schedules import crontab
from jinja2 import Template

from nudgebot.utils import send_email
from nudgebot.settings import CurrentProject
from nudgebot.base import SubclassesGetterMixin


class Report(SubclassesGetterMixin):
    """A Base report object
    static attributes:
        * NAME `str`: the name of the report. If not defined - uses the class name as name.
        * CRONTAB `celery.schedule.crontab`: The crontab schedule of the report. If defined, the
                                             report is periodic and will be triggered accordingly.
        * SUBJECT `str`: The subject of the report, could be also formatted in jinja2 format and will
                   be rendered with the data.
        * TEMPLATE `str` or `unicode`: The template of the report body, could be either a path to a template
                    file or the template content itself.
        * TEXT_FORMAT `str`: the text format of the report body. could be either `html` or `plain`
        * RECEIVERS `list` of `str`: a list of email addresses that will receive the report
    """
    NAME = None
    CRONTAB = None
    SUBJECT = None
    TEMPLATE = None
    TEXT_FORMAT = 'plain'
    RECEIVERS = []

    def __init__(self):
        assert isinstance(self.NAME, (str, type(None))), 'Report NAME should be an str, not {}'.format(self.NAME)
        assert self.CRONTAB is None or isinstance(self.CRONTAB, crontab), \
            'CRONTAB should be either None or celery.schedule.crontab, found: {}'.format(self.CRONTAB)
        assert self.SUBJECT, 'SUBJECT should be defined in the report class'
        assert self.TEMPLATE, 'TEMPLATE should be defined in the report class'
        assert self.RECEIVERS, 'No receivers for the report, please define RECEIVERS'

    def __repr__(self):
        return '<{} name="{}", subject="{}", >'.format(self.__class__.__name__, self.get_name(), self.subject)

    @classmethod
    def get_name(cls):
        """Returns the name of the report
            @rtype: `str`
        """
        return cls.NAME or cls.__name__

    @property
    def data(self):
        """In this function we should implement the data calculation for the report.
        This data will be used for the template. The property should return the data dictionary
        used for the report rendering
            @rtype: `dict`
        """
        return NotImplementedError()

    @property
    def subject(self):
        """The rendered representation of the report subject"""
        return Template(self.SUBJECT).render(data=self.data)

    @property
    def body(self):
        """Rendering the body of the report with the data"""
        if os.path.exists(self.TEMPLATE):
            with open(self.TEMPLATE, 'r') as f:
                template_raw = f.raw_read().encode('UTF-8')
        else:
            template_raw = self.TEMPLATE
        return Template(template_raw).render(data=self.data)

    def send(self, receivers=None):
        """Sending the report to the <receivers>.
            @keyword receivers: (`list` of `str`) list of the addresses of the report receivers,
                                Uses the default self.RECEIVERS if not provided
        """
        return send_email(CurrentProject().config.credentials.email.address,
                          receivers or self.RECEIVERS, self.subject, self.body, text_format=self.TEXT_FORMAT)

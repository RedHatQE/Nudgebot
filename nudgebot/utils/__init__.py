import os
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate
import logging


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
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename= {}"
                                .format(attachment))
                msg.attach(part)

    smtp_server = smtplib.SMTP('localhost')  # TODO: parameterize
    smtp_server.sendmail(from_address, receivers, msg.as_string())

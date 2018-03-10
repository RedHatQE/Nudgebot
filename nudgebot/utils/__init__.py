import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate
import logging


def send_email(from_address, receivers, subject, body, attachments=None, text_format='plain', logger=None):
    """Sending an email to to <receivers> with the provided <subject> and <body>
    Args:
        :str from_address: The address from which the email is being sent.
        :list receivers: A list of the email addresses of the receivers.
        :str body: The body of the email.
    Kwargs:
        :list attachments: A list of paths to files to be attached.
        :str text_format: The email text format, could be either 'plain' or 'html'
        :logging.Logger logger: The logger to use.
    """
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

    smtp_server = smtplib.SMTP('localhost')
    smtp_server.sendmail(from_address, receivers, msg.as_string())

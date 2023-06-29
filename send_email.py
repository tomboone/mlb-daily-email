from jinja2 import Environment, FileSystemLoader, select_autoescape
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import Config, db
import logging

logging.basicConfig(
    filename='mlb.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def render_template(template, **kwargs):
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)
    return template.render(**kwargs)


def send_email(to, sender, subject, body):
    mailer = db.session.execute(db.select(Config).filter_by(active=1)).first()[0]
    user = mailer.username
    password = mailer.password

    # convert TO into list if string
    if type(to) is not list:
        to = to.split()

    to_list = to

    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['Subject'] = subject
    msg['To'] = ','.join(to)
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP_SSL(mailer.smtp)  # or your smtp server
    server.login(user, password)
    try:
        log.info('sending email...')
        server.sendmail(sender, to_list, msg.as_string())
    except Exception as e:
        log.error('Error sending email')
        log.exception(str(e))
    finally:
        server.quit()

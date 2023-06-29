from jinja2 import Environment, FileSystemLoader, select_autoescape
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import Config
from logger import log
from sqlalchemy import select
from database import db_session


# render a template with the variables passed in
def render_template(template, **kwargs):
    env = Environment(  # create the environment
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template)  # get the template
    return template.render(**kwargs)  # render the template with the variables passed in


# send an email
def send_email(to, sender, subject, body):
    mailer = db_session.execute(select(Config).filter_by(active=1)).first()[0]  # get mailer config

    if mailer is None:  # if there is no mailer config, don't send an email
        log.error('No mailer config found')
        return

    user = mailer.username  # smtp username
    password = mailer.password  # smtp password

    # convert TO into list if string
    if type(to) is not list:
        to = to.split()

    to_list = to  # list of email addresses to send to

    msg = MIMEMultipart('alternative')  # create message
    msg['From'] = sender  # set sender
    msg['Subject'] = subject  # set subject
    msg['To'] = ','.join(to)  # set recipients
    msg.attach(MIMEText(body, 'html'))  # attach html body

    if mailer.ssl == 1:  # if ssl is enabled, use SMTP_SSL
        server = smtplib.SMTP_SSL(mailer.smtp, mailer.port)  # create server
    else:  # else use SMTP
        server = smtplib.SMTP(mailer.smtp, mailer.port)  # create server

    server.login(user, password)  # login to smtp server

    try:  # try to send email
        log.info('sending email...')  # log info
        server.sendmail(sender, to_list, msg.as_string())  # send email
    except Exception as e:  # catch exception
        log.error('Error sending email')  # log error
        log.exception(str(e))  # log exception
    finally:
        server.quit()  # quit server

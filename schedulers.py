from datetime import datetime
from datetime import timedelta
import send_email
import get_stats
from models import Config, User
from database import db_session
from sqlalchemy import select


def daily_email():
    today = datetime.now().strftime('%Y-%m-%d')  # get today's date
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')  # get yesterday's date

    boxscores = get_stats.get_boxscores(yesterday)  # get yesterday's boxscores
    probables = get_stats.get_probables(today)  # get today's probables
    standings = get_stats.get_standings()  # get standings
    transactions = get_stats.get_transactions(yesterday)  # get transactions
    leaders = get_stats.get_league_leaders()  # get league leaders

    if len(boxscores) == 0 & len(probables) == 0:  # if there are no games today or yesterday, don't send an email
        return

    html = send_email.render_template('daily.j2', **locals())  # render the template with the variables above
    to_list = []  # list of email addresses to send to
    users = db_session.execute(select(User.email).filter_by(active=1)).all()  # get all users

    for user in users:  # add all users to the list
        to_list.append(user[0])
    if len(to_list) == 0:  # if there are no users, don't send an email
        return

    sender = db_session.execute(
        select(
            Config.from_email
        )
    ).first()[0]  # get the sender email

    if sender is None:
        return  # if there is no sender, don't send an email

    subject = 'Daily MLB Report - ' + datetime.strftime(datetime.now(), '%m/%d/%Y')  # subject of the email

    send_email.send_email(to_list, sender, subject, html)  # send the email

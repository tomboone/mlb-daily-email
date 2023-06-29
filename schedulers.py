from datetime import datetime
from datetime import timedelta
import send_email
import get_stats
from models import Config, User, db


def daily_email():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

    boxscores = get_stats.get_boxscores(yesterday)  # get yesterday's boxscores
    probables = get_stats.get_probables(today)  # get today's probables
    standings = get_stats.get_standings()  # get standings
    leaders = get_stats.get_league_leaders()  # get league leaders

    html = send_email.render_template('daily.j2', **locals())
    to_list = []
    users = db.session.execute(db.select(User.email)).all()
    for user in users:
        to_list.append(user[0])
    sender = db.session.execute(db.select(Config.from_email).filter_by(active=1)).first()[0]
    subject = 'Daily MLB Report - ' + datetime.strftime(datetime.now(), '%m/%d/%Y')

    # send email to a list of email addresses
    send_email.send_email(to_list, sender, subject, html)

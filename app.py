from flask import Flask, render_template, flash, redirect, url_for
from settings import secret_key, admin_email, security_password_salt, site_name
from models import User, Role, Config
from forms import ConfigForm
from database import db_session, init_db
from flask_login import login_required
from flask_security import Security, SQLAlchemySessionUserDatastore, hash_password
from flask_security.decorators import roles_required
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from sqlalchemy import select
from flask_wtf.csrf import CSRFProtect
import atexit
import schedulers
import get_stats

app = Flask(__name__)

# App config
app.config['SCHEDULER_API_ENABLED'] = True  # enable APScheduler
app.config['SECRET_KEY'] = secret_key
app.config['SECURITY_PASSWORD_SALT'] = security_password_salt
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = False
app.secret_key = app.config['SECRET_KEY']

csrf = CSRFProtect(app)

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
app.security = Security(app, user_datastore)

with app.app_context():  # need to be in app context to create the database.py
    init_db()  # create the database.py
    db_session.commit()

    if not app.security.datastore.find_user(email=admin_email):
        admin = app.security.datastore.find_role('admin')
        if not app.security.datastore.find_role('admin'):  # If no admin role, create it
            admin = app.security.datastore.create_role(id=1, name='admin',
                                                       description='Administrator')  # create admin role
        db_session.commit()
        user = app.security.datastore.create_user(email=admin_email, password=hash_password("password"))
        app.security.datastore.add_role_to_user(user, admin)
    db_session.commit()

# scheduler
scheduler = APScheduler()  # create the scheduler
scheduler.init_app(app)  # initialize the scheduler
scheduler.start()  # start the scheduler
atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app


# Background task to update the reports
@scheduler.task('cron', id='send_email', hour=6, max_instances=1)  # run at 6am
def update_reports():
    with scheduler.app.app_context():  # need to be in app context to access the database.py
        schedulers.daily_email()  # update the reports


# Home route
@app.route('/')
def index():
    return render_template('index.html', title=site_name)


# Config route
@app.route('/config')
@login_required
@roles_required('admin')
def config():
    try:
        siteconfig = db_session.execute(
            select(
                Config.username,
                Config.password,
                Config.from_email,
                Config.smtp,
                Config.port,
                Config.ssl
            ).order_by(
                Config.id
            )
        ).mappings().first()
    except IndexError:
        siteconfig = None

    if siteconfig is None:
        flash('Site config not found.', 'danger')
        return redirect(url_for('config_add'))

    return render_template('config.html', config=siteconfig, title='Site Config | {}'.format(site_name))


@app.route('/config/add', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def config_add():
    form = ConfigForm()
    if form.validate_on_submit():
        siteconfig = Config(
            username=form.username.data,
            password=form.password.data,
            from_email=form.from_email.data,
            smtp=form.smtp.data,
            port=form.port.data,
            ssl=form.ssl.data
        )
        db_session.add(siteconfig)
        db_session.commit()
        flash('Site config added successfully.', 'success')
        return redirect(url_for('config'))

    try:
        siteconfig = db_session.execute(Config.query).mappings().all()[0]
    except IndexError:
        siteconfig = None

    if siteconfig is not None:
        flash('Site config already exists.', 'danger')
        return redirect(url_for('config'))

    return render_template('config_add.html', form=form, title='Site Config | {}'.format(site_name))


# Config form route
@app.route('/config/edit', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def config_edit():
    siteconfig = db_session.execute(
        select(
            Config.username,
            Config.password,
            Config.from_email,
            Config.smtp,
            Config.port,
            Config.ssl
        ).order_by(Config.id)).mappings().first()

    if siteconfig is None:
        flash('Site config not found.', 'danger')
        return redirect(url_for('config_add'))

    form = ConfigForm(obj=siteconfig)

    if form.validate_on_submit():
        form.populate_obj(siteconfig)
        db_session.commit()
        flash('Site config updated successfully.', 'success')
        return render_template('config.html', config=siteconfig, title='Site Config | {}'.format(site_name))

    return render_template('config_edit.html', form=form, title='Site Config | {}'.format(site_name))


# Today's games route
@app.route('/today')
@login_required
def report():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    boxscores = get_stats.get_boxscores(yesterday)  # get yesterday's boxscores
    probables = get_stats.get_probables(today)  # get today's probables
    standings = get_stats.get_standings()  # get standings
    leaders = get_stats.get_league_leaders()  # get league leaders

    return render_template('today.html', boxscores=boxscores, probables=probables, standings=standings,
                           leaders=leaders, title='Today\'s Email | {}'.format(site_name))


if __name__ == '__main__':
    app.run()

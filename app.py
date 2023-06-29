from flask import Flask, render_template, flash, redirect, url_for
from settings import secret_key, sqlalchemy_database_uri
from flask_bcrypt import Bcrypt
from models import User, db
from forms import LoginForm
from flask_login import LoginManager, login_required, login_user, logout_user
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
import statsapi
import atexit
import schedulers
import get_stats

app = Flask(__name__)

# Flask-Login
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"

bcrypt = Bcrypt()  # Flask-Bcrypt

# App config
app.config['SCHEDULER_API_ENABLED'] = True  # enable APScheduler
app.secret_key = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_database_uri

login_manager.init_app(app)  # Flask-Login
db.init_app(app)  # Flask-SQLAlchemy
bcrypt.init_app(app)  # Flask-Bcrypt

with app.app_context():  # need to be in app context to create the database
    db.create_all()  # create the database

# scheduler
scheduler = APScheduler()  # create the scheduler
scheduler.init_app(app)  # initialize the scheduler
scheduler.start()  # start the scheduler
atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app


# Background task to update the reports
@scheduler.task('cron', id='send_email', hour=6, max_instances=3)  # run at 55 minutes past the hour
def update_reports():
    with scheduler.app.app_context():  # need to be in app context to access the database
        schedulers.daily_email()  # update the reports


# Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


site_name = 'MLB@NTB'  # site name


# Home route
@app.route('/')
def index():
    return render_template('index.html', title=site_name)


# Login route
@app.route('/login/', methods=('GET', 'POST'), strict_slashes=False)
def login():
    form = LoginForm()  # LoginForm from forms.py

    if form.validate_on_submit():  # if form is submitted
        try:
            # check if user exists
            user = User.query.filter_by(email=form.email.data).first()
            # check if password is correct
            if bcrypt.check_password_hash(user.pwd, form.pwd.data):
                login_user(user)  # login user
                return redirect(url_for('index'))  # redirect to home page
            else:  # if login is incorrect
                flash('Invalid email or password!', 'danger')  # flash error
        except Exception as e:  # Catch any errors
            flash('{}'.format(e), 'danger')  # Flash the error

    # Render the login page
    return render_template('auth.html', form=form, title='Login | {}'.format(site_name))


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()  # logout user
    return redirect(url_for('login'))  # redirect to login page


# Today's games route
@app.route('/today')
# @login_required
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

from wtforms.validators import Email, InputRequired, DataRequired
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, PasswordField, SubmitField


class ConfigForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    from_email = StringField('From Email', validators=[DataRequired()])
    smtp = StringField('SMTP', validators=[DataRequired()])
    port = IntegerField('Port', validators=[DataRequired()])
    ssl = BooleanField('SSL')

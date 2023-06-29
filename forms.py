from wtforms.validators import InputRequired, Length, Email
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, PasswordField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(min=8, max=72)])


class ConfigForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    from_email = StringField('From Email', validators=[DataRequired()])
    smtp = StringField('SMTP', validators=[DataRequired()])
    port = IntegerField('Port', validators=[DataRequired()])
    ssl = BooleanField('SSL', validators=[DataRequired()])
    active = BooleanField('Active', validators=[DataRequired()])

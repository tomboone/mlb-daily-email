from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)

    def __repr__(self):
        return '<User %r>' % self.email


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    from_email = db.Column(db.String(255), nullable=False)
    smtp = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    ssl = db.Column(db.Boolean, nullable=False)
    active = db.Column(db.Boolean, nullable=False)

    # Constructor
    def __repr__(self):
        return '<Config %r>' % self.smtp

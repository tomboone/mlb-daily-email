import os

admin_email = ''
secret_key = os.environ.get("SECRET_KEY", '')
security_password_salt = os.environ.get("SECURITY_PASSWORD_SALT", '')
sqlalchemy_database_uri = ''
site_name = ''

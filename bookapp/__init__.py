import secrets
from datetime import timedelta

from flask import Flask, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary
from flask_babel import Babel

app = Flask(__name__)
app.secret_key = "hnsahfiuh43q8"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookdb?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 4
db = SQLAlchemy(app)
login = LoginManager(app=app)
cloudinary.config(cloud_name='dcncfkvwv',
                  api_key='429919544328797',
                  api_secret='8ceqNUyck4BnLwqIaMDG5ap_hBk')
babel = Babel(app)
migrate = Migrate(app, db)

app.config['GOOGLE_CLIENT_ID'] = '160924728426-i4uv37p517l3vpkvqam2h8pl1011vj1i.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
app.config['GOOGLE_DISCOVERY_URL'] = 'https://accounts.google.com/.well-known/openid-configuration'
app.config['GOOGLE_SCOPES'] = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
@app.before_request
def before_request():
    if 'nonce' not in session:
        session['nonce'] = secrets.token_urlsafe(32)